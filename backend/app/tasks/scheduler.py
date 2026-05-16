"""APScheduler bootstrap.

The Google Places reviews sync was retired when reputation data moved to the
Master Export workbook. The scheduler now only orchestrates the Phase F
follow-up jobs registered by ``register_followup_jobs``.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.tasks.followups import register_followup_jobs

logger = logging.getLogger(__name__)

scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> None:
    global scheduler
    if scheduler is not None:
        return
    scheduler = AsyncIOScheduler(timezone="Europe/London")
    register_followup_jobs(scheduler)
    scheduler.start()
    logger.info("APScheduler started with follow-up jobs")


def stop_scheduler() -> None:
    global scheduler
    if scheduler is None:
        return
    scheduler.shutdown(wait=False)
    scheduler = None
    logger.info("APScheduler stopped")
