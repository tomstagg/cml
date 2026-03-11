"""Integration tests for the firm dashboard stats endpoint."""

import pytest_asyncio

from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.models.review import Review, ReviewSource


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _make_appointment(db_session, org, session, appt_type):
    appt = Appointment(
        session_id=session.id,
        org_id=org.id,
        type=appt_type,
        status=AppointmentStatus.pending,
        client_name="Test Client",
        client_email="client@example.com",
        consent_contacted=True,
        consent_terms=True,
    )
    db_session.add(appt)
    await db_session.commit()
    await db_session.refresh(appt)
    return appt


# ── GET /api/firm/dashboard/stats ─────────────────────────────────────────────


async def test_dashboard_stats_empty_state(auth_client):
    resp = await auth_client.get("/api/firm/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_appointments"] == 0
    assert data["total_callbacks"] == 0
    assert data["aggregate_rating"] is None
    assert data["recent_appointments"] == []


async def test_dashboard_stats_counts_appointments(
    auth_client, enrolled_org, db_session, completed_session
):
    await _make_appointment(db_session, enrolled_org, completed_session, AppointmentType.appoint)
    await _make_appointment(db_session, enrolled_org, completed_session, AppointmentType.appoint)

    resp = await auth_client.get("/api/firm/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_appointments"] == 2
    assert data["total_callbacks"] == 0


async def test_dashboard_stats_counts_callbacks(
    auth_client, enrolled_org, db_session, completed_session
):
    await _make_appointment(db_session, enrolled_org, completed_session, AppointmentType.callback)

    resp = await auth_client.get("/api/firm/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_callbacks"] == 1
    assert data["total_appointments"] == 0


async def test_dashboard_stats_mixed_appointment_types(
    auth_client, enrolled_org, db_session, completed_session
):
    await _make_appointment(db_session, enrolled_org, completed_session, AppointmentType.appoint)
    await _make_appointment(db_session, enrolled_org, completed_session, AppointmentType.callback)
    await _make_appointment(db_session, enrolled_org, completed_session, AppointmentType.callback)

    resp = await auth_client.get("/api/firm/dashboard/stats")
    data = resp.json()
    assert data["total_appointments"] == 1
    assert data["total_callbacks"] == 2


async def test_dashboard_stats_shows_aggregate_rating(auth_client, enrolled_org, db_session):
    enrolled_org.aggregate_rating = 4.5
    enrolled_org.aggregate_review_count = 3
    db_session.add(enrolled_org)
    await db_session.commit()

    resp = await auth_client.get("/api/firm/dashboard/stats")
    data = resp.json()
    assert data["aggregate_rating"] == 4.5
    assert data["aggregate_review_count"] == 3


async def test_dashboard_stats_recent_appointments_shape(
    auth_client, enrolled_org, db_session, completed_session
):
    await _make_appointment(db_session, enrolled_org, completed_session, AppointmentType.appoint)

    resp = await auth_client.get("/api/firm/dashboard/stats")
    recent = resp.json()["recent_appointments"]
    assert len(recent) == 1
    appt = recent[0]
    assert "id" in appt
    assert "type" in appt
    assert "status" in appt
    assert "client_name" in appt
    assert appt["client_name"] == "Test Client"


async def test_dashboard_stats_recent_appointments_capped_at_10(
    auth_client, enrolled_org, db_session, completed_session
):
    for _ in range(12):
        await _make_appointment(
            db_session, enrolled_org, completed_session, AppointmentType.appoint
        )

    resp = await auth_client.get("/api/firm/dashboard/stats")
    assert len(resp.json()["recent_appointments"]) == 10


async def test_dashboard_stats_unauthenticated_returns_401(client):
    resp = await client.get("/api/firm/dashboard/stats")
    assert resp.status_code == 401
