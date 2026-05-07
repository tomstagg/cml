"""APScheduler entrypoint.

Owns the shared scheduler instance and the weekly Google reviews sync. Phase
F follow-up jobs are registered alongside via ``register_followup_jobs``.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import async_session_factory
from app.services.reviews import sync_all_google_reviews
from app.tasks.followups import register_followup_jobs

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
    register_followup_jobs(scheduler)
    scheduler.start()
    logger.info("APScheduler started")


def stop_scheduler():
    scheduler.shutdown()
    logger.info("APScheduler stopped")
