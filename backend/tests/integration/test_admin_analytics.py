"""Integration tests for GET /api/admin/analytics/export."""

import csv
import io
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest_asyncio

from app.models.analytics_event import AnalyticsEvent


@pytest_asyncio.fixture
async def seed_events(db_session):
    """Three events spread over three days so date-bounded queries are testable."""
    base = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
    events = [
        AnalyticsEvent(
            session_id=uuid.uuid4(),
            event_type="page_view",
            metadata_={"page": "/"},
            created_at=base,
        ),
        AnalyticsEvent(
            session_id=uuid.uuid4(),
            event_type="intake_started",
            metadata_={"session_id": "abc"},
            created_at=base + timedelta(days=1),
        ),
        AnalyticsEvent(
            session_id=None,
            event_type="proceed",
            metadata_={"org_id": "xyz", "quoted_price": 1250},
            created_at=base + timedelta(days=2),
        ),
    ]
    for e in events:
        db_session.add(e)
    await db_session.commit()
    return events


def _parse_csv(body: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(body)))


async def test_export_requires_admin_key(client):
    resp = await client.get("/api/admin/analytics/export")
    assert resp.status_code == 401


async def test_export_returns_all_events_when_no_bounds(admin_client, seed_events):
    resp = await admin_client.get("/api/admin/analytics/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment" in resp.headers["content-disposition"]

    rows = _parse_csv(resp.text)
    assert len(rows) == 3
    assert [r["event_type"] for r in rows] == [
        "page_view",
        "intake_started",
        "proceed",
    ]
    assert rows[2]["session_id"] == ""


async def test_export_filters_by_from(admin_client, seed_events):
    resp = await admin_client.get("/api/admin/analytics/export?from=2026-04-02")
    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    assert [r["event_type"] for r in rows] == ["intake_started", "proceed"]


async def test_export_filters_by_to_exclusive(admin_client, seed_events):
    resp = await admin_client.get("/api/admin/analytics/export?to=2026-04-03")
    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    assert [r["event_type"] for r in rows] == ["page_view", "intake_started"]


async def test_export_filters_by_range(admin_client, seed_events):
    resp = await admin_client.get("/api/admin/analytics/export?from=2026-04-02&to=2026-04-03")
    rows = _parse_csv(resp.text)
    assert [r["event_type"] for r in rows] == ["intake_started"]


async def test_export_metadata_is_json_encoded(admin_client, seed_events):
    resp = await admin_client.get("/api/admin/analytics/export?from=2026-04-03")
    rows = _parse_csv(resp.text)
    payload = json.loads(rows[0]["metadata"])
    assert payload == {"org_id": "xyz", "quoted_price": 1250}


async def test_export_rejects_invalid_date(admin_client):
    resp = await admin_client.get("/api/admin/analytics/export?from=not-a-date")
    assert resp.status_code == 400


async def test_export_empty_when_no_events(admin_client):
    resp = await admin_client.get("/api/admin/analytics/export")
    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    assert rows == []
