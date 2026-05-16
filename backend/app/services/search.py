"""Six-factor conveyancing search — Annex One §3.5 sequencing.

Ranks every in-scope firm across the full WMCA market using the selected
scorecard, then extracts the top-5 contactable (enrolled) firms from that
ranking. Per §3.5 this ordering is critical to preserve CML's "whole of
market" / "fully independent" positioning: enrolled firms are never
ranked separately.

Eligibility (§8.13): firms with `excluded=True` are removed from results
entirely — this is the broader of (a) SRA intervention and (b) any other
CML safeguarding decision. Pilot scope: firms with `price_type='no_data'`
have no anchor prices and therefore cannot be priced; they are excluded
from results until a transparency statement is captured.

Reputation, complaints and regulatory scores arrive pre-computed from the
Master Export workbook (Annex One: "all ingestion / cleansing /
normalisation must complete prior to runtime").
"""

import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.organisation import Organisation
from app.models.price_card import PriceType
from app.services.chat import get_intake_flags
from app.services.geocoding import geocode_postcode
from app.services.price_calc import calculate_total_effective_price
from app.services.ranking import (
    normalise_price,
    normalise_reputation,
    score_distance,
    score_offices,
)
from app.services.scorecard import FactorScores, RankableFirm, apply


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Geodesic distance between two lat/lon points in km — Annex One §8.3.4."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def search_firms(
    db: AsyncSession,
    answers: dict,
    *,
    scorecard_preference: str = "balanced",
    include_distance: bool | None = None,
) -> dict:
    """Return ``{"results": full_market, "top_five_contactable": top5}``.

    Scorecard preference and distance inclusion are no longer captured in the
    intake — they're applied here as post-intake controls. If `include_distance`
    is None we derive it from the presence of a user postcode in the intake.
    """
    flags = get_intake_flags(answers)
    postcode = flags.get("user_postcode") or ""
    preference = scorecard_preference or "balanced"
    if include_distance is None:
        include_distance = bool(postcode)

    consumer_coords = None
    if include_distance and postcode:
        consumer_coords = await geocode_postcode(postcode)

    stmt = (
        select(Organisation)
        .where(Organisation.excluded == False)  # noqa: E712 — SQLA expression
        .options(
            selectinload(Organisation.offices),
            selectinload(Organisation.price_card),
            selectinload(Organisation.complaints_summary),
            selectinload(Organisation.regulatory_summary),
        )
    )
    orgs = (await db.execute(stmt)).scalars().all()

    candidates = []
    for org in orgs:
        card = org.price_card
        if card is None or card.price_type == PriceType.no_data:
            continue

        quote = calculate_total_effective_price(card.pricing, flags, card.price_type)
        if quote is None:
            continue

        primary_office = next((o for o in org.offices if o.is_primary), None) or (
            org.offices[0] if org.offices else None
        )

        firm_distance: float | None = None
        if include_distance and consumer_coords:
            distances = [
                haversine_km(consumer_coords[0], consumer_coords[1], o.lat, o.lng)
                for o in org.offices
                if o.lat is not None and o.lng is not None
            ]
            if distances:
                firm_distance = min(distances)

        candidates.append(
            {
                "org": org,
                "office": primary_office,
                "card": card,
                "quote": quote,
                "distance_km": firm_distance,
                "office_count": max(len(org.offices), 1),
            }
        )

    if not candidates:
        return {"results": [], "top_five_contactable": []}

    cand_by_id = {str(c["org"].id): c for c in candidates}

    rep_scores = normalise_reputation(
        {oid: float(c["org"].adjusted_reputation_value or 0.0) for oid, c in cand_by_id.items()}
    )
    price_scores = normalise_price({oid: c["quote"]["total"] for oid, c in cand_by_id.items()})

    if include_distance:
        distance_inputs = {
            oid: c["distance_km"] for oid, c in cand_by_id.items() if c["distance_km"] is not None
        }
        distance_scores = score_distance(distance_inputs)
    else:
        distance_scores = {}

    rankable = []
    for oid, c in cand_by_id.items():
        complaints_score = (
            c["org"].complaints_summary.score if c["org"].complaints_summary else 100.0
        )
        regulatory_score = (
            c["org"].regulatory_summary.score if c["org"].regulatory_summary else 100.0
        )
        scores = FactorScores(
            reputation=rep_scores.get(oid, 50.0),
            price=price_scores.get(oid, 50.0),
            complaints=float(complaints_score),
            regulatory=float(regulatory_score),
            distance=distance_scores.get(oid, 50.0),
            offices=score_offices(c["office_count"]),
        )
        rankable.append(RankableFirm(org_id=oid, name=c["org"].trading_name, scores=scores))

    ranked = apply(rankable, preference, include_distance)

    full_results: list[dict] = []
    for rank, (firm, overall) in enumerate(ranked, start=1):
        c = cand_by_id[firm.org_id]
        org = c["org"]
        office = c["office"]
        full_results.append(
            {
                "rank": rank,
                "org_id": str(org.id),
                "cml_firm_id": org.cml_firm_id,
                "name": org.name,
                "trading_name": org.trading_name,
                "sra_number": org.sra_number,
                "enrolled": org.enrolled,
                "google_rating": org.google_rating,
                "google_review_count": org.google_review_count,
                "google_reviews_url": org.google_reviews_url,
                "postcode": office.postcode if office else None,
                "city": office.city if office else None,
                "distance_km": (
                    round(c["distance_km"], 1) if c["distance_km"] is not None else None
                ),
                "office_count": c["office_count"],
                "quote": c["quote"],
                "factor_scores": {
                    "reputation": firm.scores.reputation,
                    "price": firm.scores.price,
                    "complaints": firm.scores.complaints,
                    "regulatory": firm.scores.regulatory,
                    "distance": firm.scores.distance if include_distance else None,
                    "offices": firm.scores.offices,
                },
                "complaints_url": (
                    org.complaints_summary.external_url if org.complaints_summary else None
                ),
                "regulatory_url": (
                    org.regulatory_summary.external_url if org.regulatory_summary else None
                ),
                "score": round(overall),
            }
        )

    top_five_contactable = [
        r
        for r in full_results
        if r["enrolled"]
        and r["org_id"] in {str(c["org"].id) for c in candidates if c["org"].active_in_pilot}
    ][:5]

    return {"results": full_results, "top_five_contactable": top_five_contactable}
