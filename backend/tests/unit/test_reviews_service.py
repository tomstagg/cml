"""Unit tests for the reviews service: aggregate rating calculation and Google sync."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.models.organisation import Organisation
from app.models.review import Review, ReviewSource
from app.services.reviews import (
    fetch_google_reviews,
    recalculate_aggregate_rating,
    search_google_place_id,
    sync_all_google_reviews,
    sync_google_reviews_for_org,
)


# ── Helpers / fixtures ────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def org_with_place_id(db_session, enrolled_org):
    enrolled_org.google_place_id = "ChIJtestplaceid"
    db_session.add(enrolled_org)
    await db_session.commit()
    await db_session.refresh(enrolled_org)
    return enrolled_org


async def _add_review(db_session, org, source, rating, reported=False):
    review = Review(
        org_id=org.id,
        source=source,
        rating=rating,
        text="Test review text.",
        reported=reported,
    )
    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)
    return review


# ── recalculate_aggregate_rating ──────────────────────────────────────────────


async def test_aggregate_no_reviews(db_session, enrolled_org):
    await recalculate_aggregate_rating(db_session, enrolled_org)
    await db_session.commit()
    await db_session.refresh(enrolled_org)
    assert enrolled_org.aggregate_rating is None
    assert enrolled_org.aggregate_review_count == 0


async def test_aggregate_cml_only(db_session, enrolled_org):
    await _add_review(db_session, enrolled_org, ReviewSource.cml, 5.0)
    await _add_review(db_session, enrolled_org, ReviewSource.cml, 3.0)
    await recalculate_aggregate_rating(db_session, enrolled_org)
    await db_session.commit()
    await db_session.refresh(enrolled_org)
    # CML weighted 2x: (5 + 3) * 2 / (2 * 2) = 16/4 = 4.0
    assert enrolled_org.aggregate_rating == 4.0
    assert enrolled_org.aggregate_review_count == 2


async def test_aggregate_google_only(db_session, enrolled_org):
    await _add_review(db_session, enrolled_org, ReviewSource.google, 4.0)
    await recalculate_aggregate_rating(db_session, enrolled_org)
    await db_session.commit()
    await db_session.refresh(enrolled_org)
    # Google weighted 1x: 4.0 / 1 = 4.0
    assert enrolled_org.aggregate_rating == 4.0
    assert enrolled_org.aggregate_review_count == 1


async def test_aggregate_mixed_weights(db_session, enrolled_org):
    """CML reviews count 2x vs Google 1x in the weighted average."""
    await _add_review(db_session, enrolled_org, ReviewSource.cml, 5.0)  # contributes 10
    await _add_review(db_session, enrolled_org, ReviewSource.google, 1.0)  # contributes 1
    await recalculate_aggregate_rating(db_session, enrolled_org)
    await db_session.commit()
    await db_session.refresh(enrolled_org)
    # (5*2 + 1*1) / (1*2 + 1*1) = 11/3 ≈ 3.7
    assert enrolled_org.aggregate_rating == 3.7
    assert enrolled_org.aggregate_review_count == 2


async def test_aggregate_excludes_reported_cml_reviews(db_session, enrolled_org):
    """Reported CML reviews must not count toward the aggregate."""
    await _add_review(db_session, enrolled_org, ReviewSource.cml, 5.0, reported=False)
    await _add_review(db_session, enrolled_org, ReviewSource.cml, 1.0, reported=True)
    await recalculate_aggregate_rating(db_session, enrolled_org)
    await db_session.commit()
    await db_session.refresh(enrolled_org)
    # Only the 5.0 review counts: (5*2) / 2 = 5.0
    assert enrolled_org.aggregate_rating == 5.0
    assert enrolled_org.aggregate_review_count == 1


async def test_aggregate_resets_to_none_when_all_reviews_removed(db_session, enrolled_org):
    """After removing all reviews, rating should reset to None."""
    # First calculate with a review present
    await _add_review(db_session, enrolled_org, ReviewSource.google, 4.0)
    await recalculate_aggregate_rating(db_session, enrolled_org)
    await db_session.commit()

    # Now simulate no reviews (different org with no reviews)
    empty_org = Organisation(
        sra_number="SRA000999",
        name="Empty Org",
        enrolled=True,
        aggregate_rating=4.0,
        aggregate_review_count=1,
    )
    db_session.add(empty_org)
    await db_session.commit()
    await db_session.refresh(empty_org)

    await recalculate_aggregate_rating(db_session, empty_org)
    await db_session.commit()
    await db_session.refresh(empty_org)
    assert empty_org.aggregate_rating is None
    assert empty_org.aggregate_review_count == 0


# ── fetch_google_reviews ──────────────────────────────────────────────────────


async def test_fetch_google_reviews_no_api_key():
    """Returns empty list when no API key is configured."""
    with patch("app.services.reviews.settings") as mock_settings:
        mock_settings.google_places_api_key = None
        result = await fetch_google_reviews("ChIJtest")
    assert result == []


async def test_fetch_google_reviews_empty_place_id():
    with patch("app.services.reviews.settings") as mock_settings:
        mock_settings.google_places_api_key = "fake-key"
        result = await fetch_google_reviews("")
    assert result == []


async def test_fetch_google_reviews_success():
    mock_reviews = [{"rating": 5, "text": "Great!", "author_name": "Alice", "time": 1234567890}]
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"result": {"reviews": mock_reviews}}

    with (
        patch("app.services.reviews.settings") as mock_settings,
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        mock_settings.google_places_api_key = "fake-key"
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await fetch_google_reviews("ChIJtest")

    assert result == mock_reviews


async def test_fetch_google_reviews_http_error_returns_empty():
    """HTTP errors are caught and return an empty list."""
    import httpx

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=MagicMock()
    )

    with (
        patch("app.services.reviews.settings") as mock_settings,
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        mock_settings.google_places_api_key = "fake-key"
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await fetch_google_reviews("ChIJtest")

    assert result == []


# ── search_google_place_id ────────────────────────────────────────────────────


async def test_search_place_id_no_api_key():
    with patch("app.services.reviews.settings") as mock_settings:
        mock_settings.google_places_api_key = None
        result = await search_google_place_id("Test Firm", "SW1A 1AA")
    assert result is None


async def test_search_place_id_success():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "candidates": [{"place_id": "ChIJfound", "name": "Test Law Firm"}]
    }

    with (
        patch("app.services.reviews.settings") as mock_settings,
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        mock_settings.google_places_api_key = "fake-key"
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await search_google_place_id("Test Law Firm", "SW1A 1AA")

    assert result == "ChIJfound"


async def test_search_place_id_no_candidates_returns_none():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"candidates": []}

    with (
        patch("app.services.reviews.settings") as mock_settings,
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        mock_settings.google_places_api_key = "fake-key"
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await search_google_place_id("Unknown Firm", "E1 1AA")

    assert result is None


# ── sync_google_reviews_for_org ───────────────────────────────────────────────


async def test_sync_no_place_id_returns_zero(db_session, enrolled_org):
    enrolled_org.google_place_id = None
    count = await sync_google_reviews_for_org(db_session, enrolled_org)
    assert count == 0


async def test_sync_stores_new_reviews(db_session, org_with_place_id):
    google_reviews = [
        {"rating": 5, "text": "Excellent!", "author_name": "Bob", "time": 1111111111},
        {"rating": 4, "text": "Very good", "author_name": "Carol", "time": 2222222222},
    ]
    with patch("app.services.reviews.fetch_google_reviews", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = google_reviews
        count = await sync_google_reviews_for_org(db_session, org_with_place_id)

    assert count == 2
    result = await db_session.execute(
        select(Review).where(
            Review.org_id == org_with_place_id.id,
            Review.source == ReviewSource.google,
        )
    )
    assert len(result.scalars().all()) == 2


async def test_sync_skips_duplicate_reviews(db_session, org_with_place_id):
    """Second sync with identical external_ids must not insert duplicates."""
    google_reviews = [{"rating": 5, "text": "Great", "author_name": "Dave", "time": 9999999999}]
    with patch("app.services.reviews.fetch_google_reviews", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = google_reviews
        count1 = await sync_google_reviews_for_org(db_session, org_with_place_id)
        count2 = await sync_google_reviews_for_org(db_session, org_with_place_id)

    assert count1 == 1
    assert count2 == 0


async def test_sync_updates_aggregate_rating(db_session, org_with_place_id):
    google_reviews = [{"rating": 4.0, "text": "Good", "author_name": "Eve", "time": 5555555555}]
    with patch("app.services.reviews.fetch_google_reviews", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = google_reviews
        await sync_google_reviews_for_org(db_session, org_with_place_id)

    await db_session.commit()
    await db_session.refresh(org_with_place_id)
    assert org_with_place_id.aggregate_rating == 4.0


async def test_sync_skips_reviews_without_time(db_session, org_with_place_id):
    """Reviews missing a 'time' field (used as external_id) are skipped."""
    google_reviews = [{"rating": 5, "text": "No timestamp", "author_name": "Frank"}]
    with patch("app.services.reviews.fetch_google_reviews", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = google_reviews
        count = await sync_google_reviews_for_org(db_session, org_with_place_id)

    assert count == 0


# ── sync_all_google_reviews ───────────────────────────────────────────────────


async def test_sync_all_skips_orgs_without_place_id(db_session, enrolled_org):
    enrolled_org.google_place_id = None
    db_session.add(enrolled_org)
    await db_session.commit()

    result = await sync_all_google_reviews(db_session)
    assert result["orgs_synced"] == 0
    assert result["new_reviews"] == 0


async def test_sync_all_processes_orgs_with_place_id(db_session, enrolled_org):
    enrolled_org.google_place_id = "ChIJsomeplace"
    db_session.add(enrolled_org)
    await db_session.commit()

    google_reviews = [{"rating": 4, "text": "Good firm.", "author_name": "Gina", "time": 7777777}]
    with patch("app.services.reviews.fetch_google_reviews", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = google_reviews
        result = await sync_all_google_reviews(db_session)

    assert result["orgs_synced"] == 1
    assert result["new_reviews"] == 1
