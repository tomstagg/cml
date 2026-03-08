"""Firm search and ranking service."""

import math
from decimal import Decimal

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organisation import Organisation
from app.models.office import Office
from app.models.price_card import PriceCard
from app.services.chat import get_complexity_flags
from app.services.price_calc import calculate_quote
from app.services.geocoding import geocode_postcode


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two lat/lon points."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def normalise(value: float, min_val: float, max_val: float) -> float:
    """Normalise a value to 0–1 range."""
    if max_val == min_val:
        return 0.5
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


async def search_firms(db: AsyncSession, answers: dict) -> list[dict]:
    """
    Query enrolled firms with active probate price cards,
    compute quotes, and rank by weighted score.

    Returns a list of firm result dicts, ordered by rank.
    """
    complexity = get_complexity_flags(answers)
    postcode = complexity.get("postcode", "")
    ranking_pref = complexity.get("ranking_preference", "balanced")

    # Fetch consumer lat/lng
    consumer_coords = None
    if postcode:
        consumer_coords = await geocode_postcode(postcode)

    # Query: enrolled orgs with active probate price cards + primary office
    stmt = (
        select(Organisation, PriceCard, Office)
        .join(
            PriceCard,
            and_(
                PriceCard.org_id == Organisation.id,
                PriceCard.active == True,
                PriceCard.practice_area == "probate",
            ),
        )
        .outerjoin(Office, and_(Office.org_id == Organisation.id, Office.is_primary == True))
        .where(Organisation.enrolled == True)
    )
    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        return []

    candidates = []
    for org, price_card, office in rows:
        quote = calculate_quote(price_card.pricing, complexity)
        if quote is None:
            continue

        # Distance
        distance_km = None
        if consumer_coords and office and office.lat is not None and office.lng is not None:
            distance_km = haversine_km(
                consumer_coords[0], consumer_coords[1], office.lat, office.lng
            )

        candidates.append(
            {
                "org": org,
                "price_card": price_card,
                "office": office,
                "quote": quote,
                "distance_km": distance_km,
            }
        )

    if not candidates:
        return []

    # Compute score components
    prices = [c["quote"]["total"] for c in candidates]
    min_price, max_price = min(prices), max(prices)

    distances = [c["distance_km"] for c in candidates if c["distance_km"] is not None]
    min_dist = min(distances) if distances else 0
    max_dist = max(distances) if distances else 1

    ratings = [c["org"].aggregate_rating or 0 for c in candidates]
    min_rating, max_rating = min(ratings), max(ratings)

    # Ranking weights by preference
    weight_map = {
        "price": {"price": 0.80, "reputation": 0.10, "distance": 0.10},
        "reputation": {"price": 0.20, "reputation": 0.70, "distance": 0.10},
        "distance": {"price": 0.20, "reputation": 0.10, "distance": 0.70},
        "balanced": {"price": 0.60, "reputation": 0.25, "distance": 0.15},
    }
    weights = weight_map.get(ranking_pref, weight_map["balanced"])

    for c in candidates:
        total = c["quote"]["total"]
        # Lower price → higher score (invert normalisation)
        price_score = 1.0 - normalise(total, min_price, max_price)

        # Higher rating → higher score
        rating = c["org"].aggregate_rating or 0
        reputation_score = normalise(rating, min_rating, max_rating)

        # Closer → higher score
        dist = c["distance_km"]
        if dist is not None:
            distance_score = 1.0 - normalise(dist, min_dist, max_dist)
        else:
            distance_score = 0.5  # neutral if unknown

        c["score"] = (
            price_score * weights["price"]
            + reputation_score * weights["reputation"]
            + distance_score * weights["distance"]
        )

    candidates.sort(key=lambda c: c["score"], reverse=True)

    results = []
    for rank, c in enumerate(candidates, start=1):
        org = c["org"]
        office = c["office"]
        results.append(
            {
                "rank": rank,
                "org_id": str(org.id),
                "name": org.name,
                "sra_number": org.sra_number,
                "auth_status": org.auth_status,
                "enrolled": org.enrolled,
                "website_url": org.website_url,
                "aggregate_rating": org.aggregate_rating,
                "aggregate_review_count": org.aggregate_review_count,
                "postcode": office.postcode if office else None,
                "city": office.city if office else None,
                "distance_km": round(c["distance_km"], 1) if c["distance_km"] is not None else None,
                "quote": c["quote"],
                "score": round(c["score"], 4),
            }
        )

    return results
