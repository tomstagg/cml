"""Admin API: appointment conflict-check outcomes (Phase F)."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.appointment import Appointment, ConflictCheckOutcome
from app.models.organisation import Organisation
from app.schemas.appointment import ConflictCheckRequest
from app.services.email import send_conflict_check_failed

router = APIRouter(prefix="/appointments", tags=["admin-appointments"])


@router.post("/{appointment_id}/conflict-check", status_code=status.HTTP_200_OK)
async def post_conflict_check_outcome(
    appointment_id: uuid.UUID,
    body: ConflictCheckRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Record the firm's conflict-check outcome and notify the user on conflict.

    Annex One §12.4: when the firm reports a conflict, the user is emailed
    immediately with a deep link back to their results so they can pick an
    alternative.
    """
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.conflict_check_outcome = ConflictCheckOutcome(body.outcome)
    db.add(appt)
    await db.flush()

    if body.outcome == "conflict":
        org_result = await db.execute(select(Organisation).where(Organisation.id == appt.org_id))
        org = org_result.scalar_one_or_none()
        firm_name = org.name if org else "the firm"
        results_url = (
            f"{settings.app_url}/results/{appt.session_id}" if appt.session_id else settings.app_url
        )
        background_tasks.add_task(
            send_conflict_check_failed,
            appt.client_email,
            appt.client_name,
            firm_name,
            results_url,
        )

    return {
        "id": str(appt.id),
        "conflict_check_outcome": appt.conflict_check_outcome.value,
    }
