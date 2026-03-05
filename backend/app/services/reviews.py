"""Google Places reviews sync + aggregate rating calculation."""

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.organisation import Organisation
from app.models.review import Review, ReviewSource

logger = logging.getLogger(__name__)


async def search_google_place_id(org_name: str, postcode: str) -> str | None:
    """Find a Google Place ID for a firm by name + postcode."""
    if not settings.google_places_api_key:
        return None

    query = f"{org_name} solicitors {postcode}"
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                url,
                params={
                    "input": query,
                    "inputtype": "textquery",
                    "fields": "place_id,name",
                    "key": settings.google_places_api_key,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                return candidates[0].get("place_id")
    except Exception as e:
        logger.error(f"Google Place ID search error: {e}")

    return None


async def fetch_google_reviews(place_id: str) -> list[dict]:
    """Fetch reviews for a Google Place ID."""
    if not settings.google_places_api_key or not place_id:
        return []

    url = "https://maps.googleapis.com/maps/api/place/details/json"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                url,
                params={
                    "place_id": place_id,
                    "fields": "name,rating,user_ratings_total,reviews",
                    "key": settings.google_places_api_key,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            result = data.get("result", {})
            return result.get("reviews", [])
    except Exception as e:
        logger.error(f"Google reviews fetch error: {e}")
        return []


async def sync_google_reviews_for_org(db: AsyncSession, org: Organisation) -> int:
    """Sync Google reviews for a single organisation. Returns count of new reviews."""
    if not org.google_place_id:
        return 0

    google_reviews = await fetch_google_reviews(org.google_place_id)
    if not google_reviews:
        return 0

    count = 0
    for gr in google_reviews:
        external_id = gr.get("time", "")
        if not external_id:
            continue

        external_id_str = str(external_id)

        # Check if already stored
        existing = await db.execute(
            select(Review).where(
                Review.org_id == org.id,
                Review.source == ReviewSource.google,
                Review.external_id == external_id_str,
            )
        )
        if existing.scalar_one_or_none():
            continue

        review = Review(
            org_id=org.id,
            source=ReviewSource.google,
            rating=float(gr.get("rating", 0)),
            text=gr.get("text"),
            reviewer_name=gr.get("author_name"),
            external_id=external_id_str,
            synced_at=datetime.now(timezone.utc),
        )
        db.add(review)
        count += 1

    await db.flush()
    await recalculate_aggregate_rating(db, org)
    return count


async def recalculate_aggregate_rating(db: AsyncSession, org: Organisation) -> None:
    """
    Recalculate and update the aggregate rating for an organisation.
    CML reviews weighted 2x, Google reviews 1x.
    """
    # CML reviews
    cml_result = await db.execute(
        select(func.count(Review.id), func.sum(Review.rating))
        .where(Review.org_id == org.id, Review.source == ReviewSource.cml, Review.reported == False)
    )
    cml_count, cml_sum = cml_result.one()
    cml_count = cml_count or 0
    cml_sum = float(cml_sum or 0)

    # Google reviews
    google_result = await db.execute(
        select(func.count(Review.id), func.sum(Review.rating))
        .where(Review.org_id == org.id, Review.source == ReviewSource.google)
    )
    google_count, google_sum = google_result.one()
    google_count = google_count or 0
    google_sum = float(google_sum or 0)

    # Weighted average: CML 2x
    weighted_sum = (cml_sum * 2) + google_sum
    weighted_count = (cml_count * 2) + google_count

    if weighted_count > 0:
        org.aggregate_rating = round(weighted_sum / weighted_count, 1)
        org.aggregate_review_count = cml_count + google_count
    else:
        org.aggregate_rating = None
        org.aggregate_review_count = 0

    db.add(org)


async def sync_all_google_reviews(db: AsyncSession) -> dict:
    """Weekly job: sync Google reviews for all enrolled firms with a Place ID."""
    result = await db.execute(
        select(Organisation).where(
            Organisation.enrolled == True,
            Organisation.google_place_id != None,
        )
    )
    orgs = result.scalars().all()

    total_new = 0
    synced_orgs = 0
    for org in orgs:
        new_count = await sync_google_reviews_for_org(db, org)
        total_new += new_count
        synced_orgs += 1

    return {"orgs_synced": synced_orgs, "new_reviews": total_new}
