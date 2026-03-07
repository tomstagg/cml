"""APScheduler jobs for background tasks."""

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.services.reviews import sync_all_google_reviews
from app.services.email import send_review_invitation
from app.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _weekly_google_review_sync():
    """Fetch latest Google reviews for all enrolled firms."""
    logger.info("Starting weekly Google reviews sync")
    async with async_session_factory() as db:
        try:
            result = await sync_all_google_reviews(db)
            await db.commit()
            logger.info(f"Google reviews sync complete: {result}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Google reviews sync failed: {e}")


async def _review_invitation_job():
    """Send review invitations for appointments completed ~90 days ago."""
    from app.models.appointment import Appointment, AppointmentStatus
    from app.models.review import ReviewInvitation

    logger.info("Starting review invitation job")
    delay_days = settings.review_invitation_delay_days
    expiry_days = settings.review_invitation_expiry_days

    cutoff_from = datetime.now(timezone.utc) - timedelta(days=delay_days + 1)
    cutoff_to = datetime.now(timezone.utc) - timedelta(days=delay_days)

    async with async_session_factory() as db:
        try:
            # Find completed appointments in the window that haven't had invitations sent
            stmt = (
                select(Appointment)
                .outerjoin(ReviewInvitation, ReviewInvitation.appointment_id == Appointment.id)
                .where(
                    Appointment.status == AppointmentStatus.completed,
                    Appointment.created_at >= cutoff_from,
                    Appointment.created_at <= cutoff_to,
                    ReviewInvitation.id == None,
                    Appointment.client_email != None,
                )
            )
            result = await db.execute(stmt)
            appointments = result.scalars().all()

            sent = 0
            for appt in appointments:
                import uuid

                token = uuid.uuid4()
                expires_at = datetime.now(timezone.utc) + timedelta(days=expiry_days)

                invitation = ReviewInvitation(
                    appointment_id=appt.id,
                    email=appt.client_email,
                    token=token,
                    expires_at=expires_at,
                )
                db.add(invitation)
                await db.flush()

                # Load org for firm name
                from app.models.organisation import Organisation

                org_result = await db.execute(
                    select(Organisation).where(Organisation.id == appt.org_id)
                )
                org = org_result.scalar_one_or_none()
                firm_name = org.name if org else "your solicitor"

                review_url = f"{settings.app_url}/review/{token}"
                await send_review_invitation(appt.client_email, firm_name, review_url)

                from datetime import datetime as dt

                invitation.sent_at = dt.now(timezone.utc)
                sent += 1

            await db.commit()
            logger.info(f"Review invitations sent: {sent}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Review invitation job failed: {e}")


def start_scheduler():
    """Register and start APScheduler jobs."""
    scheduler.add_job(
        _weekly_google_review_sync,
        trigger="cron",
        day_of_week="mon",
        hour=3,
        minute=0,
        id="weekly_google_review_sync",
        replace_existing=True,
    )
    scheduler.add_job(
        _review_invitation_job,
        trigger="cron",
        hour=9,
        minute=0,
        id="review_invitation_job",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started")


def stop_scheduler():
    scheduler.shutdown()
    logger.info("APScheduler stopped")
