"""Public API: create appointments and callback requests."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.appointment import Appointment, AppointmentType
from app.models.organisation import Organisation
from app.schemas.appointment import AppointmentCreate, AppointmentResponse
from app.services.email import (
    send_callback_to_firm,
    send_callback_user_copy,
    send_proceed_to_firm,
    send_proceed_user_copy,
)
from app.services.followup_tokens import verify_followup_token

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    body: AppointmentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a Proceed (`appoint`) or Callback request and dispatch emails.

    Per Annex One §12.2 the firm-side email is sent **in the user's name**
    (display name + ``reply_to``) with CML BCC'd. The user receives a neutral
    CML-branded copy.
    """
    if not body.consent_contacted or not body.consent_terms:
        raise HTTPException(status_code=400, detail="Both consent fields must be accepted")

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
        preferred_time=body.preferred_time,
        quoted_price=body.quoted_price,
        consent_contacted=body.consent_contacted,
        consent_terms=body.consent_terms,
    )
    db.add(appointment)
    await db.flush()

    quoted_price = float(body.quoted_price) if body.quoted_price else None
    client_email = str(body.client_email)

    if body.type == AppointmentType.appoint.value:
        background_tasks.add_task(
            send_proceed_user_copy,
            client_email,
            body.client_name,
            org.name,
            quoted_price,
            settings.excluded_disbursements_url,
        )
        if org.email:
            background_tasks.add_task(
                send_proceed_to_firm,
                org.email,
                org.name,
                body.client_name,
                client_email,
                quoted_price,
            )
    else:
        background_tasks.add_task(
            send_callback_user_copy,
            client_email,
            body.client_name,
            org.name,
            body.preferred_time,
            quoted_price,
        )
        if org.email:
            background_tasks.add_task(
                send_callback_to_firm,
                org.email,
                org.name,
                body.client_name,
                client_email,
                body.client_phone,
                body.preferred_time,
                quoted_price,
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
