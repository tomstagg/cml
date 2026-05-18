"""Public API: create Select requests.

Callback requests are handled by ``app/api/public/callbacks.py`` via the
multi-firm bulk endpoint.
"""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.appointment import Appointment, AppointmentType
from app.models.chat_session import ChatSession
from app.models.organisation import Organisation
from app.schemas.appointment import AppointmentCreate, AppointmentResponse
from app.services.chat import build_intake_summary
from app.services.email import send_select_to_firm, send_select_user_copy
from app.services.followup_tokens import verify_followup_token

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    body: AppointmentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a Select request and dispatch emails.

    Per Annex One §12.2 the firm-side email is sent **in the user's name**
    (display name + ``reply_to``) with CML BCC'd. The user receives a neutral
    CML-branded copy.
    """
    if body.type != AppointmentType.select.value:
        raise HTTPException(
            status_code=422,
            detail=(
                "This endpoint accepts Select requests only. "
                "Use /api/public/callbacks/bulk for callbacks."
            ),
        )
    if not body.data_sharing_consent:
        raise HTTPException(
            status_code=400,
            detail="Data sharing consent is required to send your details to the firm.",
        )
    if not body.client_phone:
        raise HTTPException(status_code=400, detail="Phone number is required for Select.")

    org_result = await db.execute(
        select(Organisation).where(Organisation.id == body.org_id, Organisation.enrolled == True)
    )
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Firm not found or not enrolled")

    appointment = Appointment(
        session_id=body.session_id,
        org_id=body.org_id,
        type=body.type,
        client_name=body.client_name,
        client_email=str(body.client_email),
        client_phone=body.client_phone,
        quoted_price=body.quoted_price,
        data_sharing_consent=body.data_sharing_consent,
        purchase_property_postcode=body.purchase_property_postcode,
        sale_property_postcode=body.sale_property_postcode,
    )
    db.add(appointment)
    await db.flush()

    quoted_price = float(body.quoted_price) if body.quoted_price else None
    client_email = str(body.client_email)

    session_result = await db.execute(select(ChatSession).where(ChatSession.id == body.session_id))
    session_obj = session_result.scalar_one_or_none()
    intake_summary = build_intake_summary(session_obj.answers or {} if session_obj else {})

    background_tasks.add_task(
        send_select_user_copy,
        client_email,
        body.client_name,
        org.trading_name,
        intake_summary,
        body.purchase_property_postcode,
        body.sale_property_postcode,
        quoted_price,
        body.price_type,
    )
    if org.referral_email:
        background_tasks.add_task(
            send_select_to_firm,
            org.referral_email,
            org.trading_name,
            body.client_name,
            client_email,
            body.client_phone,
            intake_summary,
            body.purchase_property_postcode,
            body.sale_property_postcode,
            quoted_price,
            body.price_type,
        )

    return appointment


_THANK_YOU_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>Thanks — Choose My Lawyer</title></head>
<body style="font-family:Inter,system-ui,sans-serif;text-align:center;padding:80px 20px;">
<h1 style="color:#080C64;">Thanks for letting us know</h1>
<p style="color:#444;max-width:480px;margin:0 auto;">{message}</p>
</body></html>
"""


@router.get("/{appointment_id}/firm-contact", response_class=HTMLResponse)
async def record_firm_contact(
    appointment_id: uuid.UUID,
    answer: str,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Capture the binary "did the firm contact you?" reply from a follow-up email."""
    if answer not in ("yes", "no"):
        raise HTTPException(status_code=400, detail="answer must be 'yes' or 'no'")
    answer_bool = answer == "yes"
    if not verify_followup_token(appointment_id, answer_bool, token):
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.firm_contact_made = answer_bool
    db.add(appt)

    msg = (
        "Glad to hear the firm got in touch."
        if answer_bool
        else "Sorry to hear that — we'll follow up with the firm."
    )
    return HTMLResponse(_THANK_YOU_HTML.format(message=msg))
