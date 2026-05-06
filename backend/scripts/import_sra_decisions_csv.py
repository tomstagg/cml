#!/usr/bin/env python3
"""Import SRA + SDT regulatory decisions CSV → regulatory_decisions.

Annex One §7 specifies how SRA-published decisions feed the Regulatory
History factor. SRA decisions and SDT decisions share the same DB table
(distinguished by `source`) but use different deduction tables (§7.3 for
SRA, §7.5 for SDT).

Required CSV columns (flexible header aliases — see COL_ALIASES):
    sra_number, decision_id, decision_date, source, decision_type,
    sdt_fine_amount, source_url

`source` must be either "sra" or "sdt".
`decision_type` for SRA: rebuke | fixed_fine | fine_band_a | fine_band_b |
    fine_band_c | fine_band_d | fine_unbanded | conditions | intervention.
`decision_type` for SDT is ignored — the SDT deduction is derived from
    `sdt_fine_amount` per the §7.5 banding.

§8.13: an Intervention sets `Organisation.intervened = True` and is *not*
inserted as a scored decision (binary eligibility, not a deduction).

Usage:
    python scripts/import_sra_decisions_csv.py --csv path/to/decisions.csv
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
from app.models.organisation import Organisation
from app.models.regulatory_decision import (
    RegulatoryDecision,
    RegulatorySource,
    SraDecisionType,
)

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# §7.3 — SRA outcome → (enum decision_type, deduction).
# `fixed_fine`, `fine_unbanded` and `conditions` don't have dedicated enum
# values today; they map to the closest existing value. The deduction
# stored is the §7.3 value, which is the source of truth at runtime.
SRA_OUTCOME_MAP: dict[str, tuple[SraDecisionType, float]] = {
    "rebuke": (SraDecisionType.rebuke, 5.0),
    "fixed_fine": (SraDecisionType.fine_band_a, 6.0),
    "fine_band_a": (SraDecisionType.fine_band_a, 10.0),
    "fine_unbanded": (SraDecisionType.fine_band_a, 12.0),
    "fine_band_b": (SraDecisionType.fine_band_b, 15.0),
    "conditions": (SraDecisionType.control_order, 25.0),
    "fine_band_c": (SraDecisionType.fine_band_c, 40.0),
    "fine_band_d": (SraDecisionType.fine_band_d, 60.0),
}

# §7.5 — SDT fine amount band → (enum, deduction).
SDT_BANDS: list[tuple[Decimal, Decimal | None, SraDecisionType, float]] = [
    (Decimal("0"), Decimal("10000"), SraDecisionType.fine_band_a, 10.0),
    (Decimal("10001"), Decimal("25000"), SraDecisionType.fine_band_b, 15.0),
    (Decimal("25001"), Decimal("75000"), SraDecisionType.fine_band_b, 25.0),
    (Decimal("75001"), Decimal("200000"), SraDecisionType.fine_band_c, 40.0),
    (Decimal("200001"), Decimal("500000"), SraDecisionType.fine_band_d, 50.0),
    (Decimal("500001"), None, SraDecisionType.fine_band_d, 60.0),
]

COL_ALIASES = {
    "sra_number": ["sra_number", "SRA number", "SRA ID"],
    "decision_id": ["decision_id", "Decision ID"],
    "decision_date": ["decision_date", "Date", "Decision date"],
    "source": ["source", "Source"],
    "decision_type": ["decision_type", "Outcome type", "Decision type"],
    "sdt_fine_amount": ["sdt_fine_amount", "SDT fine", "Fine amount"],
    "source_url": ["source_url", "URL", "Link"],
}


def _col(row: dict, field: str) -> str:
    for alias in COL_ALIASES[field]:
        if alias in row and row[alias] is not None:
            return str(row[alias]).strip()
    return ""


def _parse_amount(raw: str) -> Decimal | None:
    if not raw:
        return None
    cleaned = raw.replace("£", "").replace(",", "").strip()
    match = re.search(r"\d+(?:\.\d+)?", cleaned)
    return Decimal(match.group()) if match else None


def _parse_date(raw: str) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _classify_sdt(fine_amount: Decimal) -> tuple[SraDecisionType, float]:
    for lo, hi, decision_type, deduction in SDT_BANDS:
        if hi is None:
            if fine_amount >= lo:
                return decision_type, deduction
        elif lo <= fine_amount <= hi:
            return decision_type, deduction
    return SraDecisionType.fine_band_a, 10.0


async def import_csv(csv_path: str) -> None:
    print(f"Reading {csv_path}...")
    with open(csv_path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    print(f"Found {len(rows)} rows")

    async with SessionLocal() as db:
        org_index: dict[str, Organisation] = {
            o.sra_number: o for o in (await db.execute(select(Organisation))).scalars().all()
        }

        created = 0
        interventions = 0
        skipped = 0

        for row in rows:
            sra_number = _col(row, "sra_number")
            org = org_index.get(sra_number)
            if not org:
                skipped += 1
                continue

            source_raw = _col(row, "source").lower()
            decision_type_raw = _col(row, "decision_type").lower()
            decision_id = _col(row, "decision_id") or None

            # §8.13 — Intervention: flip the binary flag, do not insert a
            # scored decision row.
            if decision_type_raw == "intervention":
                if not org.intervened:
                    org.intervened = True
                    db.add(org)
                    interventions += 1
                continue

            # Idempotency.
            if decision_id:
                existing = await db.execute(
                    select(RegulatoryDecision).where(
                        RegulatoryDecision.decision_id == decision_id,
                        RegulatoryDecision.org_id == org.id,
                    )
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

            sdt_fine_amount: Decimal | None = None
            if source_raw == "sdt":
                sdt_fine_amount = _parse_amount(_col(row, "sdt_fine_amount"))
                if sdt_fine_amount is None:
                    skipped += 1
                    continue
                source = RegulatorySource.sdt
                decision_type, deduction = _classify_sdt(sdt_fine_amount)
            elif source_raw == "sra":
                if decision_type_raw not in SRA_OUTCOME_MAP:
                    skipped += 1
                    continue
                source = RegulatorySource.sra
                decision_type, deduction = SRA_OUTCOME_MAP[decision_type_raw]
            else:
                skipped += 1
                continue

            db.add(
                RegulatoryDecision(
                    org_id=org.id,
                    source=source,
                    decision_id=decision_id,
                    decision_date=_parse_date(_col(row, "decision_date")),
                    decision_type=decision_type,
                    deduction=deduction,
                    sdt_fine_amount=sdt_fine_amount,
                    source_url=_col(row, "source_url") or None,
                )
            )
            created += 1

        await db.commit()
        print(
            f"Import complete: {created} decisions created, "
            f"{interventions} interventions flagged, {skipped} skipped"
        )


def main():
    parser = argparse.ArgumentParser(description="Import SRA / SDT decisions CSV")
    parser.add_argument("--csv", required=True, help="Path to decisions CSV")
    args = parser.parse_args()
    asyncio.run(import_csv(args.csv))


if __name__ == "__main__":
    main()
