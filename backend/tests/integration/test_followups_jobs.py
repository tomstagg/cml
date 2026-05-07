"""Integration tests for the Phase F APScheduler follow-up jobs.

Each job is invoked directly with a synthetic ``today`` so the date-window
dedupe is deterministic. ``async_session_factory`` is patched onto a NullPool
sessionmaker bound to the test DB so the job's DB access plays nicely with
pytest-asyncio's per-test event loops.
"""

import os
import uuid
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.models.appointment import Appointment, AppointmentType
from app.models.review import ReviewInvitation
from app.tasks import followups

# Build a NullPool factory pointing at the test DB so the job can open fresh
# connections in whichever event loop is running.
_test_engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
_test_factory = async_sessionmaker(_test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
def patch_session_factory():
    with patch.object(followups, "async_session_factory", _test_factory):
        yield


# ── helpers ──────────────────────────────────────────────────────────────────


async def _seed_appointment(
    db_session,
    *,
    org_id,
    appt_type: AppointmentType,
    created_at: datetime,
    firm_contact_made: bool | None = None,
) -> Appointment:
    appt = Appointment(
        session_id=None,
        org_id=org_id,
        type=appt_type,
        client_name="Jane",
        client_email="jane@example.com",
        consent_contacted=True,
        consent_terms=True,
        firm_contact_made=firm_contact_made,
    )
    db_session.add(appt)
    await db_session.flush()
    # created_at is server_default, override it manually for the test
    appt.created_at = created_at
    db_session.add(appt)
    await db_session.commit()
    await db_session.refresh(appt)
    return appt


# ── _callback_followup_job ───────────────────────────────────────────────────


async def test_callback_followup_emails_today_callbacks(db_session, enrolled_org):
    today = date(2026, 5, 7)
    today_dt = datetime(2026, 5, 7, 10, 0, tzinfo=timezone.utc)
    await _seed_appointment(
        db_session,
        org_id=enrolled_org.id,
        appt_type=AppointmentType.callback,
        created_at=today_dt,
    )
    with patch("app.tasks.followups.send_callback_followup", new_callable=AsyncMock) as mock_send:
        sent = await followups._callback_followup_job(today=today)
    assert sent == 1
    mock_send.assert_awaited_once()


async def test_callback_followup_skips_proceed_appointments(db_session, enrolled_org):
    today = date(2026, 5, 7)
    today_dt = datetime(2026, 5, 7, 10, 0, tzinfo=timezone.utc)
    await _seed_appointment(
        db_session,
        org_id=enrolled_org.id,
        appt_type=AppointmentType.appoint,
        created_at=today_dt,
    )
    with patch("app.tasks.followups.send_callback_followup", new_callable=AsyncMock) as mock_send:
        sent = await followups._callback_followup_job(today=today)
    assert sent == 0
    mock_send.assert_not_awaited()


async def test_callback_followup_skips_already_responded(db_session, enrolled_org):
    today = date(2026, 5, 7)
    today_dt = datetime(2026, 5, 7, 10, 0, tzinfo=timezone.utc)
    await _seed_appointment(
        db_session,
        org_id=enrolled_org.id,
        appt_type=AppointmentType.callback,
        created_at=today_dt,
        firm_contact_made=True,
    )
    with patch("app.tasks.followups.send_callback_followup", new_callable=AsyncMock) as mock_send:
        sent = await followups._callback_followup_job(today=today)
    assert sent == 0
    mock_send.assert_not_awaited()


async def test_callback_followup_ignores_other_days(db_session, enrolled_org):
    today = date(2026, 5, 7)
    yesterday_dt = datetime(2026, 5, 6, 10, 0, tzinfo=timezone.utc)
    await _seed_appointment(
        db_session,
        org_id=enrolled_org.id,
        appt_type=AppointmentType.callback,
        created_at=yesterday_dt,
    )
    with patch("app.tasks.followups.send_callback_followup", new_callable=AsyncMock) as mock_send:
        sent = await followups._callback_followup_job(today=today)
    assert sent == 0


# ── _proceed_followup_job ────────────────────────────────────────────────────


async def test_proceed_followup_runs_for_5_working_days_old(db_session, enrolled_org):
    today = date(2026, 5, 8)  # Fri
    target_dt = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)  # 5 working days back
    await _seed_appointment(
        db_session,
        org_id=enrolled_org.id,
        appt_type=AppointmentType.appoint,
        created_at=target_dt,
    )
    with patch("app.tasks.followups.send_proceed_followup", new_callable=AsyncMock) as mock_send:
        sent = await followups._proceed_followup_job(today=today)
    assert sent == 1
    mock_send.assert_awaited_once()


async def test_proceed_followup_skips_callback(db_session, enrolled_org):
    today = date(2026, 5, 8)
    target_dt = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    await _seed_appointment(
        db_session,
        org_id=enrolled_org.id,
        appt_type=AppointmentType.callback,
        created_at=target_dt,
    )
    with patch("app.tasks.followups.send_proceed_followup", new_callable=AsyncMock) as mock_send:
        sent = await followups._proceed_followup_job(today=today)
    assert sent == 0


# ── _proceed_feedback_request_job ────────────────────────────────────────────


async def test_feedback_request_creates_invitation_and_emails(db_session, enrolled_org):
    today = date(2026, 5, 8)
    target_dt = datetime(2026, 5, 8, 12, 0, tzinfo=timezone.utc) - timedelta(days=60)
    appt = await _seed_appointment(
        db_session,
        org_id=enrolled_org.id,
        appt_type=AppointmentType.appoint,
        created_at=target_dt,
    )
    with patch(
        "app.tasks.followups.send_proceed_feedback_request", new_callable=AsyncMock
    ) as mock_send:
        sent = await followups._proceed_feedback_request_job(today=today)
    assert sent == 1
    mock_send.assert_awaited_once()

    inv = await db_session.execute(
        select(ReviewInvitation).where(ReviewInvitation.appointment_id == appt.id)
    )
    invitation = inv.scalar_one()
    assert invitation.email == "jane@example.com"
    assert invitation.token is not None


async def test_feedback_request_skips_if_invitation_exists(db_session, enrolled_org):
    today = date(2026, 5, 8)
    target_dt = datetime(2026, 5, 8, 12, 0, tzinfo=timezone.utc) - timedelta(days=60)
    appt = await _seed_appointment(
        db_session,
        org_id=enrolled_org.id,
        appt_type=AppointmentType.appoint,
        created_at=target_dt,
    )
    db_session.add(
        ReviewInvitation(
            appointment_id=appt.id,
            email="jane@example.com",
            token=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
    )
    await db_session.commit()

    with patch(
        "app.tasks.followups.send_proceed_feedback_request", new_callable=AsyncMock
    ) as mock_send:
        sent = await followups._proceed_feedback_request_job(today=today)
    assert sent == 0
    mock_send.assert_not_awaited()
