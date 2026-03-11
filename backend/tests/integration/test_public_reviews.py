"""Integration tests for the public review submission flow."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest_asyncio

from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.models.review import ReviewInvitation


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def test_appointment(db_session, enrolled_org, completed_session):
    appt = Appointment(
        session_id=completed_session.id,
        org_id=enrolled_org.id,
        type=AppointmentType.appoint,
        status=AppointmentStatus.completed,
        client_name="Jane Smith",
        client_email="jane@example.com",
        consent_contacted=True,
        consent_terms=True,
    )
    db_session.add(appt)
    await db_session.commit()
    await db_session.refresh(appt)
    return appt


@pytest_asyncio.fixture
async def valid_invitation(db_session, test_appointment):
    inv = ReviewInvitation(
        appointment_id=test_appointment.id,
        email="jane@example.com",
        token=uuid.uuid4(),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(inv)
    await db_session.commit()
    await db_session.refresh(inv)
    return inv


@pytest_asyncio.fixture
async def used_invitation(db_session, test_appointment):
    inv = ReviewInvitation(
        appointment_id=test_appointment.id,
        email="jane@example.com",
        token=uuid.uuid4(),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        used_at=datetime.now(timezone.utc),
    )
    db_session.add(inv)
    await db_session.commit()
    await db_session.refresh(inv)
    return inv


@pytest_asyncio.fixture
async def expired_invitation(db_session, test_appointment):
    inv = ReviewInvitation(
        appointment_id=test_appointment.id,
        email="jane@example.com",
        token=uuid.uuid4(),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(inv)
    await db_session.commit()
    await db_session.refresh(inv)
    return inv


# ── GET /api/public/reviews/invitation/{token} ────────────────────────────────


async def test_get_invitation_returns_firm_name(client, valid_invitation, enrolled_org):
    resp = await client.get(f"/api/public/reviews/invitation/{valid_invitation.token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["firm_name"] == enrolled_org.name
    assert "expires_at" in data


async def test_get_invitation_not_found_returns_404(client):
    resp = await client.get(f"/api/public/reviews/invitation/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_get_invitation_already_used_returns_410(client, used_invitation):
    resp = await client.get(f"/api/public/reviews/invitation/{used_invitation.token}")
    assert resp.status_code == 410
    assert "already been used" in resp.json()["detail"]


async def test_get_invitation_expired_returns_410(client, expired_invitation):
    resp = await client.get(f"/api/public/reviews/invitation/{expired_invitation.token}")
    assert resp.status_code == 410
    assert "expired" in resp.json()["detail"]


# ── POST /api/public/reviews ──────────────────────────────────────────────────


async def test_submit_review_returns_201(client, valid_invitation):
    resp = await client.post(
        "/api/public/reviews",
        json={
            "token": str(valid_invitation.token),
            "rating": 5,
            "text": "Excellent service, very professional and efficient throughout.",
            "reviewer_name": "Jane Smith",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["rating"] == 5.0
    assert data["source"] == "cml"
    assert data["reported"] is False


async def test_submit_review_marks_invitation_used(client, valid_invitation, db_session):
    await client.post(
        "/api/public/reviews",
        json={
            "token": str(valid_invitation.token),
            "rating": 4,
            "text": "Good service overall, would recommend to others.",
        },
    )
    await db_session.refresh(valid_invitation)
    assert valid_invitation.used_at is not None


async def test_submit_review_updates_aggregate_rating(
    client, valid_invitation, enrolled_org, db_session
):
    await client.post(
        "/api/public/reviews",
        json={
            "token": str(valid_invitation.token),
            "rating": 5,
            "text": "Excellent service and very professional team throughout.",
        },
    )
    await db_session.refresh(enrolled_org)
    assert enrolled_org.aggregate_rating == 5.0
    assert enrolled_org.aggregate_review_count == 1


async def test_submit_review_invalid_token_returns_404(client):
    resp = await client.post(
        "/api/public/reviews",
        json={
            "token": str(uuid.uuid4()),
            "rating": 4,
            "text": "Good service overall, nothing to complain about.",
        },
    )
    assert resp.status_code == 404


async def test_submit_review_used_invitation_returns_410(client, used_invitation):
    resp = await client.post(
        "/api/public/reviews",
        json={
            "token": str(used_invitation.token),
            "rating": 3,
            "text": "Average service but got the job done in the end.",
        },
    )
    assert resp.status_code == 410


async def test_submit_review_expired_invitation_returns_410(client, expired_invitation):
    resp = await client.post(
        "/api/public/reviews",
        json={
            "token": str(expired_invitation.token),
            "rating": 3,
            "text": "Average service but got the job done eventually.",
        },
    )
    assert resp.status_code == 410


async def test_submit_review_rating_above_max_returns_422(client, valid_invitation):
    resp = await client.post(
        "/api/public/reviews",
        json={
            "token": str(valid_invitation.token),
            "rating": 6,
            "text": "Rating too high to be valid here.",
        },
    )
    assert resp.status_code == 422


async def test_submit_review_rating_below_min_returns_422(client, valid_invitation):
    resp = await client.post(
        "/api/public/reviews",
        json={
            "token": str(valid_invitation.token),
            "rating": 0,
            "text": "Rating too low to be valid here.",
        },
    )
    assert resp.status_code == 422


async def test_submit_review_text_too_short_returns_422(client, valid_invitation):
    resp = await client.post(
        "/api/public/reviews",
        json={
            "token": str(valid_invitation.token),
            "rating": 4,
            "text": "Short",
        },
    )
    assert resp.status_code == 422


async def test_submit_review_without_reviewer_name_is_allowed(client, valid_invitation):
    """reviewer_name is optional."""
    resp = await client.post(
        "/api/public/reviews",
        json={
            "token": str(valid_invitation.token),
            "rating": 4,
            "text": "Good service overall and would use them again.",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["reviewer_name"] is None
