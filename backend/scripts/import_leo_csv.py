#!/usr/bin/env python3
"""Import Legal Ombudsman decisions CSV → complaints_decisions.

Annex One §6 specifies how LeO data feeds the Complaints History factor.
This script normalises a publicly-downloaded LeO CSV into the structured
fields the runtime ranker consumes.

CSV is assumed to have already had firm names resolved to SRA numbers
(the §6 "one-time entity resolution" step). The pilot does this manually;
post-pilot a separate matcher would automate it.

Required CSV columns (flexible header aliases — see COL_ALIASES):
    decision_id, sra_number, decision_date, provider_type,
    poor_service_found, remedy_type, remedy_amount, complaint_handling,
    source_url

Filter rules per §6.4:
    - provider_type must be "Firm SRA" or "ABS Firm SRA" (otherwise barristers
      / individual practitioners — out of scope).
    - poor_service_found must be truthy.
    - sra_number must resolve to an Organisation in the DB.

Usage:
    python scripts/import_leo_csv.py --csv path/to/leo_decisions.csv
"""

import argparse
import asyncio
import csv
import re
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models.complaints_decision import ComplaintsDecision
from app.models.organisation import Organisation

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Annex One §6.7 — phrase → severity band. Phrases are matched
# case-insensitively against the comma-separated remedy_type field.
SEVERITY_BAND_NO_REMEDY = 0
SEVERITY_BAND_NON_PECUNIARY = 1
SEVERITY_BAND_FEE_REMEDY = 2
SEVERITY_BAND_FINANCIAL_COMPENSATION = 3

REMEDY_PHRASE_TO_BAND: dict[str, int] = {
    "no remedy": SEVERITY_BAND_NO_REMEDY,
    "other": SEVERITY_BAND_NON_PECUNIARY,
    "to apologise": SEVERITY_BAND_NON_PECUNIARY,
    "to complete work for the complainant": SEVERITY_BAND_NON_PECUNIARY,
    "to return papers": SEVERITY_BAND_NON_PECUNIARY,
    "to refund fees already paid": SEVERITY_BAND_FEE_REMEDY,
    "to waive unpaid fees": SEVERITY_BAND_FEE_REMEDY,
    "to limit fees to a specified amount": SEVERITY_BAND_FEE_REMEDY,
    "to pay compensation for emotional impact and/or disruption caused": SEVERITY_BAND_FINANCIAL_COMPENSATION,
    "to pay compensation of a specified amount for loss suffered": SEVERITY_BAND_FINANCIAL_COMPENSATION,
    "to pay a specified amount for expenses the complainant incurred in pursuing the complaint": SEVERITY_BAND_FINANCIAL_COMPENSATION,
    "to pay for someone else to complete the work": SEVERITY_BAND_FINANCIAL_COMPENSATION,
    "to take (and pay for) any specified action in the interests of the complainant": SEVERITY_BAND_FINANCIAL_COMPENSATION,
    "to pay interest on compensation": SEVERITY_BAND_FINANCIAL_COMPENSATION,
    "to pay interest on monies held": SEVERITY_BAND_FINANCIAL_COMPENSATION,
}

# §6.9 — band → severity score.
SEVERITY_SCORES: dict[int, float] = {
    SEVERITY_BAND_NO_REMEDY: 0.50,
    SEVERITY_BAND_NON_PECUNIARY: 0.30,
    SEVERITY_BAND_FEE_REMEDY: 0.60,
    SEVERITY_BAND_FINANCIAL_COMPENSATION: 1.00,
}

# §6.11 — remedy amount → score. Edges are inclusive.
REMEDY_AMOUNT_BANDS: list[tuple[Decimal, Decimal | None, float]] = [
    (Decimal("0"), Decimal("0"), 10),
    (Decimal("1"), Decimal("299"), 12),
    (Decimal("300"), Decimal("749"), 15),
    (Decimal("750"), Decimal("999"), 17),
    (Decimal("1000"), Decimal("4999"), 22),
    (Decimal("5000"), Decimal("9999"), 26),
    (Decimal("10000"), Decimal("14999"), 30),
    (Decimal("15000"), Decimal("19999"), 34),
    (Decimal("20000"), Decimal("24999"), 38),
    (Decimal("25000"), Decimal("29999"), 42),
    (Decimal("30000"), Decimal("34999"), 46),
    (Decimal("35000"), Decimal("39999"), 50),
    (Decimal("40000"), Decimal("44999"), 54),
    (Decimal("45000"), Decimal("49999"), 58),
    (Decimal("50000"), None, 62),
]

PROVIDER_TYPES_IN_SCOPE = {"firm sra", "abs firm sra"}

COL_ALIASES = {
    "decision_id": ["decision_id", "Decision ID", "Case reference"],
    "sra_number": ["sra_number", "SRA number", "SRA ID"],
    "decision_date": ["decision_date", "Date", "Decision date"],
    "provider_type": ["provider_type", "Provider type", "Service provider type"],
    "poor_service_found": [
        "poor_service_found",
        "Poor service",
        "Poor service found",
        "Outcome",
    ],
    "remedy_type": ["remedy_type", "Remedy type", "Remedies"],
    "remedy_amount": ["remedy_amount", "Remedy amount", "Amount"],
    "complaint_handling": [
        "complaint_handling",
        "Complaint handling",
        "Unreasonable complaint handling",
    ],
    "source_url": ["source_url", "URL", "Link"],
}


def _col(row: dict, field: str) -> str:
    for alias in COL_ALIASES[field]:
        if alias in row and row[alias] is not None:
            return str(row[alias]).strip()
    return ""


def _truthy(value: str) -> bool:
    return value.lower() in {"yes", "y", "true", "1", "poor service found"}


def _parse_remedy_amount(raw: str) -> Decimal | None:
    """Accepts £-prefixed numbers, comma thousands, plain numbers, or band
    strings like '£1,000–£4,999' — picks the lower bound for matching.
    Returns None if the field is empty or N/A (the latter only appears on
    excluded 'no poor service' rows so should never reach this script).
    """
    if not raw or raw.upper() == "N/A":
        return None
    cleaned = raw.replace("£", "").replace(",", "").strip()
    # Band-style: take the first numeric chunk.
    match = re.search(r"\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    return Decimal(match.group())


def _remedy_amount_score(amount: Decimal | None) -> float:
    if amount is None:
        return 10.0
    for lo, hi, score in REMEDY_AMOUNT_BANDS:
        if hi is None:
            if amount >= lo:
                return score
        elif lo <= amount <= hi:
            return score
    return 10.0


def _highest_severity_band(remedy_type_field: str) -> int:
    """A LeO decision may list multiple comma-separated remedy phrases.
    Annex One §6.7 implies one severity per decision — take the highest.
    """
    phrases = [p.strip().lower() for p in remedy_type_field.split(",") if p.strip()]
    bands = [REMEDY_PHRASE_TO_BAND[p] for p in phrases if p in REMEDY_PHRASE_TO_BAND]
    if not bands:
        return SEVERITY_BAND_NO_REMEDY
    return max(bands)


def _parse_date(raw: str) -> date | None:
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return date.fromisoformat(raw) if fmt == "%Y-%m-%d" else None
        except ValueError:
            pass
    # Fallback to dateutil-style permissive parse.
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


async def import_csv(csv_path: str) -> None:
    print(f"Reading {csv_path}...")
    with open(csv_path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    print(f"Found {len(rows)} rows")

    async with SessionLocal() as db:
        org_index: dict[str, Organisation] = {}
        result = await db.execute(select(Organisation))
        for org in result.scalars().all():
            org_index[org.sra_number] = org

        created = 0
        skipped = 0

        for row in rows:
            provider = _col(row, "provider_type").lower()
            if provider not in PROVIDER_TYPES_IN_SCOPE:
                skipped += 1
                continue
            if not _truthy(_col(row, "poor_service_found")):
                skipped += 1
                continue

            sra_number = _col(row, "sra_number")
            org = org_index.get(sra_number)
            if not org:
                skipped += 1
                continue

            decision_id = _col(row, "decision_id") or None
            # Idempotency: skip if we already imported this decision_id.
            if decision_id:
                existing = await db.execute(
                    select(ComplaintsDecision).where(
                        ComplaintsDecision.decision_id == decision_id,
                        ComplaintsDecision.org_id == org.id,
                    )
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

            severity_band = _highest_severity_band(_col(row, "remedy_type"))
            severity_score = SEVERITY_SCORES[severity_band]
            remedy_amount = _parse_remedy_amount(_col(row, "remedy_amount"))
            remedy_amount_score = _remedy_amount_score(remedy_amount)
            handling_penalty = _truthy(_col(row, "complaint_handling"))

            db.add(
                ComplaintsDecision(
                    org_id=org.id,
                    decision_id=decision_id,
                    decision_date=_parse_date(_col(row, "decision_date")),
                    remedy_type=_col(row, "remedy_type") or None,
                    severity_band=severity_band,
                    severity_score=severity_score,
                    remedy_amount=remedy_amount,
                    remedy_amount_score=remedy_amount_score,
                    complaint_handling_penalty=handling_penalty,
                    source_url=_col(row, "source_url") or None,
                )
            )
            created += 1

        await db.commit()
        print(f"Import complete: {created} created, {skipped} skipped")


def main():
    parser = argparse.ArgumentParser(description="Import Legal Ombudsman decisions CSV")
    parser.add_argument("--csv", required=True, help="Path to LeO decisions CSV")
    args = parser.parse_args()
    asyncio.run(import_csv(args.csv))


if __name__ == "__main__":
    main()
