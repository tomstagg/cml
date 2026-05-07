"""Integration tests for the firm dashboard 2×2 grid (Phase G2)."""

from datetime import datetime, timedelta, timezone

from app.models.analytics_event import AnalyticsEvent
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.models.review import Review, ReviewSource


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _make_appointment(db_session, org, session, appt_type, *, age_days: int = 0):
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
    if age_days:
        appt.created_at = datetime.now(timezone.utc) - timedelta(days=age_days)
        await db_session.commit()
    return appt


async def _make_review(db_session, org, *, age_days: int = 0):
    review = Review(
        org_id=org.id,
        source=ReviewSource.cml,
        rating=5,
        text="Great service",
        reviewer_name="Client",
    )
    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)
    if age_days:
        review.created_at = datetime.now(timezone.utc) - timedelta(days=age_days)
        await db_session.commit()
    return review


# ── GET /api/firm/dashboard/stats ─────────────────────────────────────────────


async def test_dashboard_stats_empty_state(auth_client):
    resp = await auth_client.get("/api/firm/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {
        "new_appointments_30d": 0,
        "video_call_requests_30d": 0,
        "appearances_in_results_30d": 0,
        "new_reviews_30d": 0,
    }


async def test_dashboard_stats_counts_appointments_within_30d(
    auth_client, enrolled_org, db_session, completed_session
):
    await _make_appointment(db_session, enrolled_org, completed_session, AppointmentType.appoint)
    await _make_appointment(db_session, enrolled_org, completed_session, AppointmentType.appoint)
    # Callbacks should not count toward new appointments.
    await _make_appointment(db_session, enrolled_org, completed_session, AppointmentType.callback)

    resp = await auth_client.get("/api/firm/dashboard/stats")
    assert resp.json()["new_appointments_30d"] == 2


async def test_dashboard_stats_excludes_appointments_older_than_30d(
    auth_client, enrolled_org, db_session, completed_session
):
    await _make_appointment(
        db_session, enrolled_org, completed_session, AppointmentType.appoint, age_days=45
    )
    await _make_appointment(db_session, enrolled_org, completed_session, AppointmentType.appoint)

    resp = await auth_client.get("/api/firm/dashboard/stats")
    assert resp.json()["new_appointments_30d"] == 1


async def test_dashboard_stats_video_call_requests_is_placeholder_zero(auth_client):
    resp = await auth_client.get("/api/firm/dashboard/stats")
    assert resp.json()["video_call_requests_30d"] == 0


async def test_dashboard_stats_counts_recent_reviews(auth_client, enrolled_org, db_session):
    await _make_review(db_session, enrolled_org)
    await _make_review(db_session, enrolled_org)
    await _make_review(db_session, enrolled_org, age_days=45)

    resp = await auth_client.get("/api/firm/dashboard/stats")
    assert resp.json()["new_reviews_30d"] == 2


async def test_dashboard_stats_counts_appearances_from_analytics_events(
    auth_client, enrolled_org, db_session
):
    db_session.add_all(
        [
            AnalyticsEvent(
                event_type="results_viewed",
                metadata_={
                    "org_ids": [str(enrolled_org.id), "00000000-0000-0000-0000-000000000001"]
                },
            ),
            AnalyticsEvent(
                event_type="results_viewed",
                metadata_={"org_ids": [str(enrolled_org.id)]},
            ),
            # Different org — should not count.
            AnalyticsEvent(
                event_type="results_viewed",
                metadata_={"org_ids": ["00000000-0000-0000-0000-000000000002"]},
            ),
            # Different event type — should not count.
            AnalyticsEvent(
                event_type="proceed",
                metadata_={"org_id": str(enrolled_org.id)},
            ),
        ]
    )
    await db_session.commit()

    resp = await auth_client.get("/api/firm/dashboard/stats")
    assert resp.json()["appearances_in_results_30d"] == 2


async def test_dashboard_stats_unauthenticated_returns_401(client):
    resp = await client.get("/api/firm/dashboard/stats")
    assert resp.status_code == 401
