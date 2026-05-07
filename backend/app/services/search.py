"""Six-factor conveyancing search — Annex One §3.5 sequencing.

Ranks every in-scope firm across the full WMCA market using the selected
scorecard, then extracts the top-5 contactable (enrolled) firms from that
ranking. Per §3.5 this ordering is critical to preserve CML's "whole of
market" / "fully independent" positioning: enrolled firms are never
ranked separately.

Eligibility (§8.13): firms with an SRA Intervention are removed from the
results entirely. Pilot scope (Quoted Prices only): firms without an
active conveyancing price card cannot be priced and are excluded. Once
the Estimated Price path lands post-pilot this restriction goes away.
"""

import math
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.organisation import Organisation
from app.services.chat import get_intake_flags
from app.services.geocoding import geocode_postcode
from app.services.price_calc import calculate_total_effective_price
from app.services.ranking import (
    adjusted_reputation_value,
    normalise_price,
    normalise_reputation,
    score_complaints,
    score_distance,
    score_offices,
    score_regulatory,
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


async def search_firms(db: AsyncSession, answers: dict) -> dict:
    """Return ``{"results": full_market, "top_five_contactable": top5}``.

    Both lists carry rich result rows (rank, factor scores, quote
    breakdown, etc.) so the API layer can hand them straight to the
    client without further transformation.
    """
    flags = get_intake_flags(answers)
    postcode = flags.get("property_postcode") or ""
    preference = flags.get("scorecard_preference", "balanced")
    include_distance = bool(flags.get("include_distance", False))

    consumer_coords = None
    if include_distance and postcode:
        consumer_coords = await geocode_postcode(postcode)

    # Load every non-intervened firm with all the data the ranker needs in
    # one query — eager-loaded so the loop below is pure Python.
    stmt = (
        select(Organisation)
        .where(Organisation.intervened == False)  # noqa: E712 — SQLA expression
        .options(
            selectinload(Organisation.offices),
            selectinload(Organisation.price_cards),
            selectinload(Organisation.complaints_decisions),
            selectinload(Organisation.regulatory_decisions),
        )
    )
    orgs = (await db.execute(stmt)).scalars().all()

    candidates = []
    for org in orgs:
        active_card = next(
            (
                c
                for c in org.price_cards
                if c.active and c.practice_area == "residential_conveyancing"
            ),
            None,
        )
        if active_card is None:
            continue
        quote = calculate_total_effective_price(active_card.pricing, flags)
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
                "card": active_card,
                "quote": quote,
                "distance_km": firm_distance,
                "office_count": max(len(org.offices), 1),
            }
        )

    if not candidates:
        return {"results": [], "top_five_contactable": []}

    cand_by_id = {str(c["org"].id): c for c in candidates}

    # Relative factors — normalised across the full results set.
    arvs = {
        oid: adjusted_reputation_value(c["org"].aggregate_rating, c["org"].aggregate_review_count)
        for oid, c in cand_by_id.items()
    }
    rep_scores = normalise_reputation(arvs)
    price_scores = normalise_price({oid: c["quote"]["total"] for oid, c in cand_by_id.items()})

    if include_distance:
        distance_inputs = {
            oid: c["distance_km"] for oid, c in cand_by_id.items() if c["distance_km"] is not None
        }
        distance_scores = score_distance(distance_inputs)
    else:
        distance_scores = {}

    # Build rankable firms with absolute + normalised factor scores.
    rankable = []
    for oid, c in cand_by_id.items():
        scores = FactorScores(
            reputation=rep_scores.get(oid, 50.0),
            price=price_scores.get(oid, 50.0),
            complaints=score_complaints(c["org"].complaints_decisions),
            regulatory=score_regulatory(c["org"].regulatory_decisions),
            # When distance is excluded the weight is 0 so the value is
            # arithmetically inert — 50 keeps it neutral if the weight
            # is ever non-zero by accident.
            distance=distance_scores.get(oid, 50.0),
            offices=score_offices(c["office_count"]),
        )
        rankable.append(RankableFirm(org_id=oid, name=c["org"].name, scores=scores))

    ranked = apply(rankable, preference, include_distance)

    full_results: list[dict] = []
    for rank, (firm, overall) in enumerate(ranked, start=1):
        c = cand_by_id[firm.org_id]
        org = c["org"]
        office = c["office"]
        complaints_sources = [
            {
                "decision_date": d.decision_date.isoformat() if d.decision_date else None,
                "url": d.source_url,
            }
            for d in sorted(
                org.complaints_decisions,
                key=lambda d: d.decision_date or date.min,
                reverse=True,
            )
            if d.source_url
        ]
        regulatory_sources = [
            {
                "decision_date": d.decision_date.isoformat() if d.decision_date else None,
                "url": d.source_url,
            }
            for d in sorted(
                org.regulatory_decisions,
                key=lambda d: d.decision_date or date.min,
                reverse=True,
            )
            if d.source_url
        ]

        full_results.append(
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
                "complaints_sources": complaints_sources,
                "regulatory_sources": regulatory_sources,
                # Display only the final overall score is rounded — §5.7.4
                # mandates internal precision.
                "score": round(overall),
            }
        )

    top_five_contactable = [r for r in full_results if r["enrolled"]][:5]

    return {"results": full_results, "top_five_contactable": top_five_contactable}
