"""Firm dashboard: 30-day counts for the 2×2 grid (Phase G2)."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.analytics_event import AnalyticsEvent
from app.models.appointment import Appointment, AppointmentType
from app.models.firm_user import FirmUser
from app.models.review import Review
from app.schemas.firm import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["firm-dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: FirmUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.org_id
    since = datetime.now(timezone.utc) - timedelta(days=30)

    new_appointments = await db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.org_id == org_id,
            Appointment.type == AppointmentType.select,
            Appointment.created_at >= since,
        )
    )

    new_reviews = await db.scalar(
        select(func.count(Review.id)).where(
            Review.org_id == org_id,
            Review.created_at >= since,
        )
    )

    # `results_viewed` events whose metadata.org_ids array contains this org.
    # Phase I emits these — until then the count is zero.
    appearances = await db.scalar(
        select(func.count(AnalyticsEvent.id)).where(
            AnalyticsEvent.event_type == "results_viewed",
            AnalyticsEvent.metadata_["org_ids"].contains([str(org_id)]),
            AnalyticsEvent.created_at >= since,
        )
    )

    return DashboardStats(
        new_appointments_30d=new_appointments or 0,
        video_call_requests_30d=0,
        appearances_in_results_30d=appearances or 0,
        new_reviews_30d=new_reviews or 0,
    )
