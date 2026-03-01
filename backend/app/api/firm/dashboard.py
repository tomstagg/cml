"""Firm dashboard: stats and appointments."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.appointment import Appointment, AppointmentType
from app.models.firm_user import FirmUser
from app.models.organisation import Organisation
from app.schemas.firm import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["firm-dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: FirmUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.org_id

    # Total appointments
    appt_result = await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.org_id == org_id,
            Appointment.type == AppointmentType.appoint,
        )
    )
    total_appointments = appt_result.scalar() or 0

    # Total callbacks
    callback_result = await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.org_id == org_id,
            Appointment.type == AppointmentType.callback,
        )
    )
    total_callbacks = callback_result.scalar() or 0

    # Org rating
    org_result = await db.execute(select(Organisation).where(Organisation.id == org_id))
    org = org_result.scalar_one_or_none()

    # Recent appointments (last 10)
    recent_result = await db.execute(
        select(Appointment)
        .where(Appointment.org_id == org_id)
        .order_by(Appointment.created_at.desc())
        .limit(10)
    )
    recent = recent_result.scalars().all()

    recent_list = [
        {
            "id": str(a.id),
            "type": a.type,
            "status": a.status,
            "client_name": a.client_name,
            "quoted_price": float(a.quoted_price) if a.quoted_price else None,
            "created_at": a.created_at.isoformat(),
        }
        for a in recent
    ]

    return DashboardStats(
        total_appearances=0,  # Phase 2: track search appearance impressions
        total_appointments=total_appointments,
        total_callbacks=total_callbacks,
        aggregate_rating=org.aggregate_rating if org else None,
        aggregate_review_count=org.aggregate_review_count if org else None,
        recent_appointments=recent_list,
    )
