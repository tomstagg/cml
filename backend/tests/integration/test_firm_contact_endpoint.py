"""Integration tests for GET /api/public/appointments/{id}/firm-contact."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest_asyncio
from sqlalchemy import select

from app.models.appointment import Appointment, AppointmentType
from app.models.chat_session import ChatSession
from app.services.followup_tokens import make_followup_token


@pytest_asyncio.fixture
async def callback_appointment(db_session, enrolled_org):
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
        type=AppointmentType.callback,
        client_name="Jane",
        client_email="jane@example.com",
        consent_contacted=True,
        consent_terms=True,
    )
    db_session.add(appt)
    await db_session.commit()
    await db_session.refresh(appt)
    return appt


async def test_firm_contact_yes_sets_flag_true(client, callback_appointment, verify_session):
    token = make_followup_token(callback_appointment.id, True)
    resp = await client.get(
        f"/api/public/appointments/{callback_appointment.id}/firm-contact",
        params={"answer": "yes", "token": token},
    )
    assert resp.status_code == 200
    assert "Thanks" in resp.text

    refreshed = await verify_session.execute(
        select(Appointment).where(Appointment.id == callback_appointment.id)
    )
    assert refreshed.scalar_one().firm_contact_made is True


async def test_firm_contact_no_sets_flag_false(client, callback_appointment, verify_session):
    token = make_followup_token(callback_appointment.id, False)
    resp = await client.get(
        f"/api/public/appointments/{callback_appointment.id}/firm-contact",
        params={"answer": "no", "token": token},
    )
    assert resp.status_code == 200

    refreshed = await verify_session.execute(
        select(Appointment).where(Appointment.id == callback_appointment.id)
    )
    assert refreshed.scalar_one().firm_contact_made is False


async def test_firm_contact_invalid_token_returns_403(client, callback_appointment):
    resp = await client.get(
        f"/api/public/appointments/{callback_appointment.id}/firm-contact",
        params={"answer": "yes", "token": "deadbeef"},
    )
    assert resp.status_code == 403


async def test_firm_contact_token_for_other_answer_rejected(client, callback_appointment):
    """Yes-token used on a no-link must fail."""
    yes_token = make_followup_token(callback_appointment.id, True)
    resp = await client.get(
        f"/api/public/appointments/{callback_appointment.id}/firm-contact",
        params={"answer": "no", "token": yes_token},
    )
    assert resp.status_code == 403


async def test_firm_contact_invalid_answer_returns_400(client, callback_appointment):
    token = make_followup_token(callback_appointment.id, True)
    resp = await client.get(
        f"/api/public/appointments/{callback_appointment.id}/firm-contact",
        params={"answer": "maybe", "token": token},
    )
    assert resp.status_code == 400


async def test_firm_contact_missing_appointment_returns_404(client):
    appt_id = uuid.uuid4()
    token = make_followup_token(appt_id, True)
    resp = await client.get(
        f"/api/public/appointments/{appt_id}/firm-contact",
        params={"answer": "yes", "token": token},
    )
    assert resp.status_code == 404
