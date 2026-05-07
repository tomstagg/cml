"""Integration tests for POST /api/admin/appointments/{id}/conflict-check."""

import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.models.appointment import Appointment, AppointmentType, ConflictCheckOutcome
from app.models.chat_session import ChatSession

_verify_engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
_verify_factory = async_sessionmaker(_verify_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def proceed_appointment(db_session, enrolled_org):
    """A pending Proceed appointment with a chat session attached."""
    session = ChatSession(
        id=uuid.uuid4(),
        practice_area="residential_conveyancing",
        answers={},
        message_history=[],
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(session)
    await db_session.flush()

    appt = Appointment(
        session_id=session.id,
        org_id=enrolled_org.id,
        type=AppointmentType.appoint,
        client_name="Jane Smith",
        client_email="jane@example.com",
        consent_contacted=True,
        consent_terms=True,
    )
    db_session.add(appt)
    await db_session.commit()
    await db_session.refresh(appt)
    return appt


async def test_conflict_check_requires_admin_key(client, proceed_appointment):
    resp = await client.post(
        f"/api/admin/appointments/{proceed_appointment.id}/conflict-check",
        json={"outcome": "clear"},
    )
    assert resp.status_code == 401


async def test_conflict_check_clear_does_not_email(admin_client, proceed_appointment, db_session):
    with patch(
        "app.api.admin.appointments.send_conflict_check_failed", new_callable=AsyncMock
    ) as mock_email:
        resp = await admin_client.post(
            f"/api/admin/appointments/{proceed_appointment.id}/conflict-check",
            json={"outcome": "clear"},
        )
    assert resp.status_code == 200
    assert resp.json()["conflict_check_outcome"] == "clear"
    mock_email.assert_not_called()

    async with _verify_factory() as fresh:
        refreshed = await fresh.execute(
            select(Appointment).where(Appointment.id == proceed_appointment.id)
        )
        assert refreshed.scalar_one().conflict_check_outcome == ConflictCheckOutcome.clear


async def test_conflict_check_conflict_emails_user(admin_client, proceed_appointment):
    with patch(
        "app.api.admin.appointments.send_conflict_check_failed", new_callable=AsyncMock
    ) as mock_email:
        resp = await admin_client.post(
            f"/api/admin/appointments/{proceed_appointment.id}/conflict-check",
            json={"outcome": "conflict"},
        )
    assert resp.status_code == 200
    assert resp.json()["conflict_check_outcome"] == "conflict"
    mock_email.assert_awaited_once()
    args = mock_email.await_args.args
    assert args[0] == "jane@example.com"
    assert args[1] == "Jane Smith"
    # results URL should include the session id
    assert str(proceed_appointment.session_id) in args[3]


async def test_conflict_check_invalid_outcome_rejected(admin_client, proceed_appointment):
    resp = await admin_client.post(
        f"/api/admin/appointments/{proceed_appointment.id}/conflict-check",
        json={"outcome": "maybe"},
    )
    assert resp.status_code == 422


async def test_conflict_check_missing_appointment_returns_404(admin_client):
    resp = await admin_client.post(
        f"/api/admin/appointments/{uuid.uuid4()}/conflict-check",
        json={"outcome": "clear"},
    )
    assert resp.status_code == 404
