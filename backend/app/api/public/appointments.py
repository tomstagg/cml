"""Public API: create appointments and callback requests."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.appointment import Appointment
from app.models.organisation import Organisation
from app.schemas.appointment import AppointmentCreate, AppointmentResponse
from app.services.email import (
    send_appointment_confirmation_consumer,
    send_appointment_notification_firm,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    body: AppointmentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create an appointment or callback request."""
    if not body.consent_contacted or not body.consent_terms:
        raise HTTPException(status_code=400, detail="Both consent fields must be accepted")

    # Verify org exists and is enrolled
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

    # Send emails in background
    background_tasks.add_task(
        send_appointment_confirmation_consumer,
        str(body.client_email),
        body.client_name,
        org.name,
        body.type,
        float(body.quoted_price) if body.quoted_price else None,
    )

    if org.email:
        background_tasks.add_task(
            send_appointment_notification_firm,
            org.email,
            org.name,
            body.client_name,
            str(body.client_email),
            body.client_phone,
            body.type,
            body.preferred_time,
            float(body.quoted_price) if body.quoted_price else None,
        )

    return appointment
