#!/usr/bin/env python3
"""Synthetic seed for Phase E smoke testing.

Creates 15 fake WMCA conveyancing firms with a mix of enrolment status,
SRA authorisation status, complaint + regulatory histories, office
counts and price cards — enough variety to exercise every column on the
results page (top-5, full market, severity bands, source links).

SRA numbers 9000000–9000099 are reserved for synthetic data and wiped
before re-seeding so the script is idempotent.

Usage:
    docker-compose exec backend python scripts/seed_synthetic.py
"""

import asyncio
import sys
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models.complaints_decision import ComplaintsDecision
from app.models.office import Office
from app.models.organisation import Organisation
from app.models.price_card import PriceCard
from app.models.regulatory_decision import (
    RegulatoryDecision,
    RegulatorySource,
    SraDecisionType,
)

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Approximate city-centre lat/lngs for WMCA postcode prefixes.
CITY = {
    "B": (52.4862, -1.8904, "Birmingham"),
    "CV": (52.4068, -1.5197, "Coventry"),
    "DY": (52.5128, -2.0814, "Dudley"),
    "WV": (52.5862, -2.1280, "Wolverhampton"),
    "WS": (52.5862, -1.9821, "Walsall"),
}

# Annex One §6.9 severity scores and §6.11 remedy-amount scores —
# pre-computed at ingest in the real importers, replicated here so this
# fixture matches the runtime contract.
SEVERITY_NO_REMEDY = (0, 0.5)
SEVERITY_NON_PEC = (1, 0.3)
SEVERITY_FEE = (2, 0.6)
SEVERITY_FINANCIAL = (3, 1.0)

AMT_ZERO = (Decimal("0"), 10.0)
AMT_300_749 = (Decimal("400"), 15.0)
AMT_1000_4999 = (Decimal("2500"), 22.0)
AMT_5000_9999 = (Decimal("7500"), 26.0)


def _bands(offset: int = 0):
    """Standard 4-band fee table with an optional cohort offset."""
    return [
        {"purchase_price_min": 0, "purchase_price_max": 250000, "fee": 950 + offset},
        {"purchase_price_min": 250000, "purchase_price_max": 500000, "fee": 1250 + offset},
        {"purchase_price_min": 500000, "purchase_price_max": 1000000, "fee": 1750 + offset},
        {"purchase_price_min": 1000000, "purchase_price_max": None, "fee": 2500 + offset},
    ]


ADJUSTMENTS = [
    {"name": "Leasehold supplement", "amount": 250, "condition": "tenure==leasehold"},
    {"name": "New build supplement", "amount": 200, "condition": "new_build==true"},
    {"name": "Help to Buy ISA admin", "amount": 75, "condition": "help_to_buy_isa==true"},
    {"name": "Shared ownership supplement", "amount": 250, "condition": "shared_ownership==true"},
    {"name": "Mortgage handling", "amount": 150, "condition": "mortgage==true"},
]

DISBURSEMENTS = [
    {"name": "Local authority search", "amount": 180, "vat_applies": True},
    {"name": "Drainage & water search", "amount": 65, "vat_applies": True},
    {"name": "Environmental search", "amount": 45, "vat_applies": True},
    {"name": "Bankruptcy search", "amount": 6, "vat_applies": False},
    {"name": "Land Registry priority search", "amount": 3, "vat_applies": False},
    {"name": "Land Registry registration fee", "amount": 150, "vat_applies": False},
]


def price_card(fee_offset: int = 0) -> dict:
    return {
        "practice_area": "residential_conveyancing",
        "matter_types": ["purchase", "sale", "purchase_and_sale", "remortgage"],
        "pricing_model": "band",
        "bands": _bands(fee_offset),
        "adjustments": ADJUSTMENTS,
        "included_disbursements": DISBURSEMENTS,
        "excluded_disbursements_note": (
            "Stamp Duty Land Tax, leasehold notice fees, ground rent apportionment "
            "and indemnity policies are excluded."
        ),
        "vat_applies_to_fees": True,
    }


# Each firm: (sra_number, name, postcode, city_key, enrolled, auth_status,
#             intervened, rating, review_count, fee_offset, office_count,
#             complaints, regulatory)
# complaints: list of (severity_tuple, amount_tuple, handling_penalty, days_ago)
# regulatory: list of (source, decision_type, deduction, sdt_fine, days_ago)
FIRMS = [
    (
        "9000001",
        "Lyndon Smith LLP",
        "B17 9LJ",
        "B",
        True,
        "authorised",
        False,
        4.7,
        132,
        0,
        1,
        [],
        [],
    ),
    (
        "9000002",
        "Whitmore & Partners",
        "B5 4UA",
        "B",
        True,
        "authorised",
        False,
        4.5,
        89,
        50,
        2,
        [(SEVERITY_NON_PEC, AMT_ZERO, False, 200)],
        [],
    ),
    (
        "9000003",
        "Coventry Legal Solutions",
        "CV1 3HJ",
        "CV",
        True,
        "authorised",
        False,
        4.2,
        56,
        -50,
        1,
        [],
        [("sra", SraDecisionType.rebuke, 5.0, None, 400)],
    ),
    (
        "9000004",
        "Bridge Street Solicitors",
        "DY1 1QT",
        "DY",
        True,
        "authorised",
        False,
        4.8,
        210,
        100,
        3,
        [],
        [],
    ),
    (
        "9000005",
        "Wolverhampton Conveyancing Co",
        "WV1 2HQ",
        "WV",
        True,
        "authorised",
        False,
        3.9,
        34,
        -100,
        1,
        [
            (SEVERITY_FEE, AMT_300_749, False, 150),
            (SEVERITY_NON_PEC, AMT_ZERO, True, 320),
        ],
        [("sra", SraDecisionType.fine_band_b, 15.0, None, 500)],
    ),
    (
        "9000006",
        "Walsall Property Lawyers",
        "WS1 1QW",
        "WS",
        True,
        "conditions",
        False,
        4.0,
        45,
        25,
        1,
        [(SEVERITY_NO_REMEDY, AMT_ZERO, False, 90)],
        [],
    ),
    (
        "9000007",
        "Heaton & Co",
        "B91 1RW",
        "B",
        False,
        "authorised",
        False,
        4.6,
        178,
        0,
        5,
        [],
        [],
    ),
    (
        "9000008",
        "Old Square Solicitors",
        "B3 1HG",
        "B",
        False,
        "authorised",
        False,
        4.3,
        102,
        -25,
        2,
        [(SEVERITY_NON_PEC, AMT_ZERO, False, 250)],
        [],
    ),
    (
        "9000009",
        "Edgbaston Legal",
        "B16 9NU",
        "B",
        False,
        "authorised",
        False,
        4.1,
        67,
        75,
        1,
        [],
        [],
    ),
    (
        "9000010",
        "Sutton Coldfield Conveyancers",
        "B73 6RG",
        "B",
        False,
        "authorised",
        False,
        4.4,
        91,
        0,
        1,
        [],
        [
            ("sra", SraDecisionType.rebuke, 5.0, None, 600),
            ("sdt", SraDecisionType.fine_band_a, 10.0, Decimal("8500"), 800),
        ],
    ),
    (
        "9000011",
        "Coventry Heritage Solicitors",
        "CV3 2BD",
        "CV",
        False,
        "authorised",
        False,
        3.8,
        22,
        -75,
        1,
        [(SEVERITY_FEE, AMT_300_749, False, 180)],
        [],
    ),
    (
        "9000012",
        "Black Country Legal",
        "DY8 1XJ",
        "DY",
        False,
        "authorised",
        False,
        4.5,
        63,
        50,
        1,
        [],
        [],
    ),
    (
        "9000013",
        "Wolverhampton Old Hall",
        "WV3 9DZ",
        "WV",
        False,
        "authorised",
        False,
        3.7,
        15,
        -150,
        1,
        [
            (SEVERITY_FINANCIAL, AMT_5000_9999, True, 120),
            (SEVERITY_FINANCIAL, AMT_1000_4999, False, 400),
        ],
        [("sra", SraDecisionType.fine_band_c, 40.0, None, 700)],
    ),
    (
        "9000014",
        "Penn Common Solicitors",
        "WV4 5HX",
        "WV",
        False,
        "authorised",
        False,
        4.2,
        40,
        25,
        1,
        [],
        [],
    ),
    # Intervened firm: must NOT appear in results (Annex One §8.13).
    (
        "9000015",
        "Chambers Bridge Lawyers (DEFUNCT)",
        "B12 0BJ",
        "B",
        False,
        "authorised",
        True,
        3.0,
        5,
        0,
        1,
        [],
        [],
    ),
]


def _office_for(prefix: str, postcode: str, idx: int) -> dict:
    lat, lng, city = CITY[prefix]
    # Spread additional offices ~1km apart so distance varies sensibly.
    return {
        "address_line1": f"{idx + 1} High Street",
        "city": city,
        "county": "West Midlands",
        "postcode": postcode if idx == 0 else postcode[:-1] + str((idx + 1) % 10),
        "lat": lat + idx * 0.01,
        "lng": lng + idx * 0.01,
        "is_primary": idx == 0,
    }


async def seed() -> None:
    async with SessionLocal() as db:
        # Wipe any prior synthetic rows so re-runs are clean. Cascading
        # deletes on offices / price_cards / complaints / regulatory all
        # follow from organisations.
        existing = await db.execute(
            select(Organisation).where(Organisation.sra_number.like("90000%"))
        )
        prior = existing.scalars().all()
        if prior:
            await db.execute(delete(Organisation).where(Organisation.id.in_([o.id for o in prior])))
            print(f"Removed {len(prior)} prior synthetic firm(s).")

        for spec in FIRMS:
            (
                sra,
                name,
                postcode,
                prefix,
                enrolled,
                auth_status,
                intervened,
                rating,
                reviews,
                fee_offset,
                office_count,
                complaints,
                regulatory,
            ) = spec

            org = Organisation(
                sra_number=sra,
                name=name,
                auth_status=auth_status,
                website_url=f"https://example.com/{sra}",
                phone="0121 000 0000",
                email=f"hello@{sra}.example.com",
                enrolled=enrolled,
                enrollment_token=uuid.uuid4() if not enrolled else None,
                intervened=intervened,
                aggregate_rating=rating,
                aggregate_review_count=reviews,
            )
            for i in range(office_count):
                org.offices.append(Office(**_office_for(prefix, postcode, i)))

            # Every synthetic firm gets a price card so the intervened
            # case proves the §8.13 filter (not the missing-price filter).
            org.price_cards.append(
                PriceCard(
                    practice_area="residential_conveyancing",
                    pricing=price_card(fee_offset),
                    confidence=1.0,
                    active=True,
                )
            )

            for severity, amount, handling, days_ago in complaints:
                band, sev_score = severity
                amt_value, amt_score = amount
                org.complaints_decisions.append(
                    ComplaintsDecision(
                        decision_id=f"LEO-{sra}-{days_ago}",
                        decision_date=date.today().replace(year=date.today().year - 1),
                        remedy_type="synthetic",
                        severity_band=band,
                        severity_score=sev_score,
                        remedy_amount=amt_value if amt_value > 0 else None,
                        remedy_amount_score=amt_score,
                        complaint_handling_penalty=handling,
                        source_url=f"https://www.legalombudsman.org.uk/decisions/{sra}-{days_ago}",
                    )
                )

            for source, decision_type, deduction, sdt_fine, days_ago in regulatory:
                org.regulatory_decisions.append(
                    RegulatoryDecision(
                        source=RegulatorySource(source),
                        decision_id=f"{source.upper()}-{sra}-{days_ago}",
                        decision_date=date.today().replace(year=date.today().year - 2),
                        decision_type=decision_type,
                        deduction=deduction,
                        sdt_fine_amount=sdt_fine,
                        source_url=f"https://www.sra.org.uk/decisions/{sra}-{days_ago}",
                    )
                )

            db.add(org)

        await db.commit()
        print(f"Seeded {len(FIRMS)} synthetic firms.")
        print("  - 6 enrolled (top-5 contactable will be drawn from these)")
        print("  - 8 not enrolled but priced (full market only)")
        print("  - 1 intervened (filtered out per Annex One §8.13)")


if __name__ == "__main__":
    asyncio.run(seed())
