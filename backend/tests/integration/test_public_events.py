"""Integration tests for POST /api/public/events (analytics mirror)."""

import uuid

from sqlalchemy import select

from app.models.analytics_event import AnalyticsEvent


async def test_record_event_persists_to_db(client, verify_session):
    session_id = uuid.uuid4()
    resp = await client.post(
        "/api/public/events",
        json={
            "event_type": "results_viewed",
            "session_id": str(session_id),
            "metadata": {"top_five_count": 5, "full_count": 42},
        },
    )
    assert resp.status_code == 202
    event_id = uuid.UUID(resp.json()["id"])

    result = await verify_session.execute(
        select(AnalyticsEvent).where(AnalyticsEvent.id == event_id)
    )
    event = result.scalar_one()
    assert event.event_type == "results_viewed"
    assert event.session_id == session_id
    assert event.metadata_ == {"top_five_count": 5, "full_count": 42}


async def test_record_event_allows_null_session_id(client, verify_session):
    resp = await client.post(
        "/api/public/events",
        json={
            "event_type": "page_view",
            "metadata": {"page": "/conveyancing", "referrer": "https://google.com"},
        },
    )
    assert resp.status_code == 202

    result = await verify_session.execute(
        select(AnalyticsEvent).where(AnalyticsEvent.event_type == "page_view")
    )
    event = result.scalar_one()
    assert event.session_id is None
    assert event.metadata_["page"] == "/conveyancing"


async def test_record_event_rejects_unknown_event_type(client):
    resp = await client.post(
        "/api/public/events",
        json={"event_type": "purchase_complete", "metadata": {}},
    )
    assert resp.status_code == 422


async def test_record_event_defaults_metadata(client, verify_session):
    resp = await client.post(
        "/api/public/events",
        json={"event_type": "intake_started", "session_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 202

    result = await verify_session.execute(
        select(AnalyticsEvent).where(AnalyticsEvent.event_type == "intake_started")
    )
    event = result.scalar_one()
    assert event.metadata_ == {}


async def test_record_event_no_auth_required(client):
    """Endpoint must accept anonymous traffic — frontend fires before any session exists."""
    resp = await client.post(
        "/api/public/events",
        json={"event_type": "page_view", "metadata": {"page": "/"}},
    )
    assert resp.status_code == 202
