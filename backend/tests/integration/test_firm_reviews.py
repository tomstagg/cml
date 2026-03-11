"""Integration tests for firm review management endpoints."""

import uuid

import pytest_asyncio

from app.models.review import Review, ReviewSource


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def cml_review(db_session, enrolled_org):
    review = Review(
        org_id=enrolled_org.id,
        source=ReviewSource.cml,
        rating=4.0,
        text="Very professional service throughout.",
        reviewer_name="Alice Johnson",
    )
    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)
    return review


@pytest_asyncio.fixture
async def google_review(db_session, enrolled_org):
    review = Review(
        org_id=enrolled_org.id,
        source=ReviewSource.google,
        rating=5.0,
        text="Highly recommend this firm.",
        reviewer_name="Bob Williams",
        external_id="google-external-123",
    )
    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)
    return review


# ── GET /api/firm/reviews ─────────────────────────────────────────────────────


async def test_list_reviews_empty(auth_client):
    resp = await auth_client.get("/api/firm/reviews")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_reviews_returns_all_sources(auth_client, cml_review, google_review):
    resp = await auth_client.get("/api/firm/reviews")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    sources = {r["source"] for r in data}
    assert sources == {"cml", "google"}


async def test_list_reviews_unauthenticated_returns_401(client):
    resp = await client.get("/api/firm/reviews")
    assert resp.status_code == 401


async def test_list_reviews_contains_expected_fields(auth_client, cml_review):
    resp = await auth_client.get("/api/firm/reviews")
    assert resp.status_code == 200
    review = resp.json()[0]
    assert "id" in review
    assert "source" in review
    assert "rating" in review
    assert "text" in review
    assert "reported" in review


# ── POST /api/firm/reviews/{review_id}/respond ────────────────────────────────


async def test_respond_to_review_success(auth_client, cml_review):
    resp = await auth_client.post(
        f"/api/firm/reviews/{cml_review.id}/respond",
        json={"response_text": "Thank you for your kind feedback!"},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Response submitted"


async def test_respond_to_review_persists_response(auth_client, cml_review, db_session):
    await auth_client.post(
        f"/api/firm/reviews/{cml_review.id}/respond",
        json={"response_text": "We appreciate your review."},
    )
    await db_session.refresh(cml_review)
    assert cml_review.firm_response == "We appreciate your review."
    assert cml_review.firm_response_at is not None


async def test_respond_to_unknown_review_returns_404(auth_client):
    resp = await auth_client.post(
        f"/api/firm/reviews/{uuid.uuid4()}/respond",
        json={"response_text": "Thanks!"},
    )
    assert resp.status_code == 404


async def test_respond_unauthenticated_returns_401(client, cml_review):
    resp = await client.post(
        f"/api/firm/reviews/{cml_review.id}/respond",
        json={"response_text": "Thanks!"},
    )
    assert resp.status_code == 401


# ── POST /api/firm/reviews/{review_id}/report ─────────────────────────────────


async def test_report_review_success(auth_client, cml_review):
    resp = await auth_client.post(
        f"/api/firm/reviews/{cml_review.id}/report",
        json={"reason": "This review contains offensive language."},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Review reported for admin review"


async def test_report_review_sets_reported_flag(auth_client, cml_review, db_session):
    await auth_client.post(
        f"/api/firm/reviews/{cml_review.id}/report",
        json={"reason": "Fake review from a non-client."},
    )
    await db_session.refresh(cml_review)
    assert cml_review.reported is True
    assert cml_review.reported_at is not None


async def test_report_already_reported_review_returns_409(auth_client, cml_review):
    await auth_client.post(
        f"/api/firm/reviews/{cml_review.id}/report",
        json={"reason": "Initial report reason here."},
    )
    resp = await auth_client.post(
        f"/api/firm/reviews/{cml_review.id}/report",
        json={"reason": "Duplicate report reason here."},
    )
    assert resp.status_code == 409


async def test_report_unknown_review_returns_404(auth_client):
    resp = await auth_client.post(
        f"/api/firm/reviews/{uuid.uuid4()}/report",
        json={"reason": "Some reason for reporting this review."},
    )
    assert resp.status_code == 404


async def test_report_unauthenticated_returns_401(client, cml_review):
    resp = await client.post(
        f"/api/firm/reviews/{cml_review.id}/report",
        json={"reason": "Reporting this review for investigation."},
    )
    assert resp.status_code == 401
