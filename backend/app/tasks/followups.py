"""APScheduler follow-up jobs (Phase F).

Three jobs replace the prior 90-day review-invitation cron:

* End-of-day Callback follow-up — same working day as the request.
* 5-working-day Select follow-up — quote-drift reminder + binary check-in.
* 2-month Select feedback request — issues a ReviewInvitation token.

All three are dedupe'd by a date window: each appointment falls in exactly
one daily cron run, so we don't need a per-job ``sent_at`` column. The
2-month job additionally guards against a duplicate by joining on the
existing ``review_invitations`` row.
"""

import logging
import uuid
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_factory
from app.models.appointment import Appointment, AppointmentType
from app.models.organisation import Organisation
from app.models.review import ReviewInvitation
from app.services.email import (
    send_callback_followup,
    send_select_feedback_request,
    send_select_followup,
)
from app.services.followup_tokens import followup_url

logger = logging.getLogger(__name__)


def working_days_ago(n: int, today: date | None = None) -> date:
    """Return the date N working days before ``today`` (Mon-Fri only)."""
    d = today or date.today()
    remaining = n
    while remaining > 0:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            remaining -= 1
    return d


def _utc_day_window(target: date) -> tuple[datetime, datetime]:
    start = datetime.combine(target, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end


async def _load_firm_name(db: AsyncSession, org_id: uuid.UUID) -> str:
    result = await db.execute(select(Organisation).where(Organisation.id == org_id))
    org = result.scalar_one_or_none()
    return org.name if org else "your solicitor"


# ── End-of-day Callback follow-up ────────────────────────────────────────────


async def _callback_followup_job(today: date | None = None) -> int:
    """Send "did the firm call you?" emails for callbacks made today.

    Returns the count of emails dispatched (used by tests).
    """
    target = today or date.today()
    start, end = _utc_day_window(target)
    sent = 0

    async with async_session_factory() as db:
        try:
            stmt = select(Appointment).where(
                Appointment.type == AppointmentType.callback,
                Appointment.created_at >= start,
                Appointment.created_at < end,
                Appointment.firm_contact_made.is_(None),
            )
            result = await db.execute(stmt)
            appointments = result.scalars().all()

            for appt in appointments:
                firm_name = await _load_firm_name(db, appt.org_id)
                await send_callback_followup(
                    appt.client_email,
                    appt.client_name,
                    firm_name,
                    followup_url(appt.id, True),
                    followup_url(appt.id, False),
                )
                sent += 1
            await db.commit()
            logger.info(f"Callback follow-up: {sent} email(s) sent")
        except Exception as e:
            await db.rollback()
            logger.error(f"Callback follow-up job failed: {e}")
    return sent


# ── 5-working-day Select follow-up ───────────────────────────────────────────


async def _select_followup_job(today: date | None = None) -> int:
    """Send "is your matter progressing?" emails for Selects N working days old."""
    n = settings.proceed_followup_working_days
    target = working_days_ago(n, today)
    start, end = _utc_day_window(target)
    sent = 0

    async with async_session_factory() as db:
        try:
            stmt = select(Appointment).where(
                Appointment.type == AppointmentType.select,
                Appointment.created_at >= start,
                Appointment.created_at < end,
                Appointment.firm_contact_made.is_(None),
            )
            result = await db.execute(stmt)
            appointments = result.scalars().all()

            for appt in appointments:
                firm_name = await _load_firm_name(db, appt.org_id)
                await send_select_followup(
                    appt.client_email,
                    appt.client_name,
                    firm_name,
                    followup_url(appt.id, True),
                    followup_url(appt.id, False),
                )
                sent += 1
            await db.commit()
            logger.info(f"Select follow-up: {sent} email(s) sent")
        except Exception as e:
            await db.rollback()
            logger.error(f"Select follow-up job failed: {e}")
    return sent


# ── 2-month Select feedback request ──────────────────────────────────────────


async def _select_feedback_request_job(today: date | None = None) -> int:
    """Issue a review token + email for Selects whose delay window matures today.

    Replaces the prior ``review_invitation_job`` (90-day, status=completed
    based). Now keyed off Select appointments at
    ``settings.review_invitation_delay_days`` old, dedupe'd by the existence
    of a ``review_invitations`` row.
    """
    delay = settings.review_invitation_delay_days
    expiry = settings.review_invitation_expiry_days
    target = (today or date.today()) - timedelta(days=delay)
    start, end = _utc_day_window(target)
    sent = 0

    async with async_session_factory() as db:
        try:
            stmt = (
                select(Appointment)
                .outerjoin(ReviewInvitation, ReviewInvitation.appointment_id == Appointment.id)
                .where(
                    Appointment.type == AppointmentType.select,
                    Appointment.created_at >= start,
                    Appointment.created_at < end,
                    ReviewInvitation.id.is_(None),
                    Appointment.client_email.is_not(None),
                )
            )
            result = await db.execute(stmt)
            appointments = result.scalars().all()

            for appt in appointments:
                token = uuid.uuid4()
                expires_at = datetime.now(timezone.utc) + timedelta(days=expiry)
                invitation = ReviewInvitation(
                    appointment_id=appt.id,
                    email=appt.client_email,
                    token=token,
                    expires_at=expires_at,
                    sent_at=datetime.now(timezone.utc),
                )
                db.add(invitation)
                await db.flush()

                firm_name = await _load_firm_name(db, appt.org_id)
                review_url = f"{settings.app_url}/review/{token}"
                await send_select_feedback_request(appt.client_email, firm_name, review_url)
                sent += 1

            await db.commit()
            logger.info(f"Select feedback request: {sent} email(s) sent")
        except Exception as e:
            await db.rollback()
            logger.error(f"Select feedback request job failed: {e}")
    return sent


def register_followup_jobs(scheduler) -> None:
    """Register Phase F follow-up jobs against an existing AsyncIOScheduler."""
    scheduler.add_job(
        _callback_followup_job,
        trigger="cron",
        hour=17,
        minute=0,
        id="callback_followup_job",
        replace_existing=True,
    )
    scheduler.add_job(
        _select_followup_job,
        trigger="cron",
        hour=9,
        minute=0,
        id="select_followup_job",
        replace_existing=True,
    )
    scheduler.add_job(
        _select_feedback_request_job,
        trigger="cron",
        hour=9,
        minute=30,
        id="select_feedback_request_job",
        replace_existing=True,
    )
