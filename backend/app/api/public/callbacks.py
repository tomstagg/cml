"""Public API: bulk Request-a-callback submissions.

Users may ask up to three firms to call them about their transaction from a
single results set. Per spec, once a session has any callback Appointment
recorded the endpoint locks (409) — further callbacks require a new search.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.appointment import Appointment, AppointmentType
from app.models.chat_session import ChatSession
from app.models.organisation import Organisation
from app.schemas.appointment import BulkCallbackCreate, BulkCallbackResponse
from app.services.chat import build_intake_summary
from app.services.email import send_bulk_callbacks_user_copy, send_callback_to_firm

router = APIRouter(prefix="/callbacks", tags=["callbacks"])


@router.post(
    "/bulk",
    response_model=BulkCallbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_bulk_callbacks(
    body: BulkCallbackCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create N (1..3) callback appointments for one session in one submission."""
    sess = (
        await db.execute(select(ChatSession).where(ChatSession.id == body.session_id))
    ).scalar_one_or_none()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    already = (
        await db.execute(
            select(Appointment.id)
            .where(
                Appointment.session_id == body.session_id,
                Appointment.type == AppointmentType.callback,
            )
            .limit(1)
        )
    ).first()
    if already:
        raise HTTPException(
            status_code=409,
            detail="Callbacks already requested for this search",
        )

    firm_ids = [f.org_id for f in body.firms]
    orgs = (
        (
            await db.execute(
                select(Organisation).where(
                    Organisation.id.in_(firm_ids),
                    Organisation.enrolled.is_(True),
                )
            )
        )
        .scalars()
        .all()
    )
    org_by_id = {o.id: o for o in orgs}
    if len(org_by_id) != len(firm_ids):
        raise HTTPException(
            status_code=404,
            detail="One or more firms not found or not enrolled",
        )

    appts: list[Appointment] = []
    for f in body.firms:
        appt = Appointment(
            session_id=body.session_id,
            org_id=f.org_id,
            type=AppointmentType.callback.value,
            client_name=body.client_name,
            client_email=str(body.client_email),
            client_phone=body.client_phone,
            preferred_callback_window=body.preferred_callback_window,
            quoted_price=f.quoted_price,
            data_sharing_consent=True,
        )
        db.add(appt)
        appts.append(appt)
    await db.flush()

    intake_summary = build_intake_summary(sess.answers or {})
    firm_blocks: list[dict] = []
    for f, appt in zip(body.firms, appts):
        org = org_by_id[f.org_id]
        quoted = float(f.quoted_price) if f.quoted_price is not None else None
        firm_blocks.append(
            {
                "firm_name": org.trading_name,
                "quoted_price": quoted,
                "price_type": f.price_type,
            }
        )
        if org.referral_email:
            background_tasks.add_task(
                send_callback_to_firm,
                org.referral_email,
                org.trading_name,
                body.client_name,
                str(body.client_email),
                body.client_phone,
                intake_summary,
                None,
                None,
                body.preferred_callback_window,
                quoted,
                f.price_type,
            )

    background_tasks.add_task(
        send_bulk_callbacks_user_copy,
        str(body.client_email),
        body.client_name,
        firm_blocks,
        intake_summary,
        None,
        None,
        body.preferred_callback_window,
    )

    await db.commit()
    return BulkCallbackResponse(
        created=len(appts),
        appointment_ids=[a.id for a in appts],
    )
