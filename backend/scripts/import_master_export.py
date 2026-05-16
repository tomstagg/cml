"""Master Export workbook → CML database ingestion.

Reads the seven Master Export data tabs (Firms / Reputation / Complaints
history / Regulatory history / Price / Distance) as CSV exports and
upserts them into the data model. Idempotent: parent rows (organisations)
are upserted by ``cml_firm_id``; child collections (offices, price_card,
summaries) are deleted and re-inserted on each run.

Expected CSV files in ``--input-dir``:
    firms.csv         (one row per firm, Firms tab)
    reputation.csv    (Reputation tab)
    complaints.csv    (Complaints history tab)
    regulatory.csv    (Regulatory history tab)
    price.csv         (Price tab — has two header rows)
    distance.csv      (one row per office, Distance tab)

Usage:
    docker-compose exec backend python scripts/import_master_export.py \\
        --input-dir scripts/seed_data/master_export

    # Skip postcode geocoding (Fetchify) — useful locally when no key.
    docker-compose exec backend python scripts/import_master_export.py \\
        --input-dir scripts/seed_data/master_export --no-geocode

    # Dry-run inside a transaction (rolls back at the end).
    docker-compose exec backend python scripts/import_master_export.py \\
        --input-dir scripts/seed_data/master_export --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import csv
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.complaints_summary import ComplaintsSummary
from app.models.office import Office, OfficeType
from app.models.organisation import Organisation
from app.models.price_card import PriceCard, PriceType
from app.models.regulatory_summary import RegulatorySummary
from app.services.geocoding import geocode_postcode

# Anchor purchase prices on the Price tab (£150k → £1.5m, 7 anchors per matter).
ANCHORS: tuple[int, ...] = (150_000, 250_000, 500_000, 750_000, 1_000_000, 1_250_000, 1_500_000)

PRICE_TYPE_MAP = {
    "estimated": PriceType.estimated,
    "verified": PriceType.verified,
    "no data": PriceType.no_data,
}

OFFICE_TYPE_MAP = {
    "BRANCH": OfficeType.branch,
    "HO": OfficeType.ho,
}


# ── CSV helpers ───────────────────────────────────────────────────────────────


def _normalise_key(key: str) -> str:
    """Whitespace-normalise a header so callers can match on intent."""
    return " ".join(key.lower().split())


def _row_get(row: dict, *candidates: str) -> str:
    """Look up a column value tolerantly (case- and whitespace-insensitive)."""
    norm = {_normalise_key(k): k for k in row.keys()}
    for candidate in candidates:
        key = _normalise_key(candidate)
        if key in norm:
            return row[norm[key]] or ""
    return ""


def _blank_to_none(value: str) -> str | None:
    s = (value or "").strip()
    return s if s else None


def _parse_bool(value: str) -> bool:
    return (value or "").strip().upper() in ("TRUE", "YES", "1")


def _parse_int(value: str) -> int | None:
    s = (value or "").strip()
    if not s or s.upper() == "MISSING DATA":
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def _parse_float(value: str) -> float | None:
    s = (value or "").strip()
    if not s or s.upper() == "MISSING DATA":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _read_price_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    """Price tab has a section header row and a column header row; return the
    column-header row plus body rows.
    """
    with path.open(newline="") as f:
        rows = list(csv.reader(f))
    if len(rows) < 3:
        raise RuntimeError(f"price.csv has only {len(rows)} rows; expected ≥3")
    return rows[1], rows[2:]


# ── Ingestion stages ──────────────────────────────────────────────────────────


async def _upsert_firms(db: AsyncSession, rows: list[dict]) -> dict[str, Organisation]:
    by_id: dict[str, Organisation] = {}
    for row in rows:
        cml_id = _row_get(row, "CML firm ID").strip()
        if not cml_id:
            continue

        existing = await db.execute(select(Organisation).where(Organisation.cml_firm_id == cml_id))
        org = existing.scalar_one_or_none()
        if org is None:
            org = Organisation(
                cml_firm_id=cml_id,
                sra_number="",
                name="",
                trading_name="",
            )
            db.add(org)

        org.sra_number = _row_get(row, "SRA ID").strip()
        org.name = _row_get(row, "Firm name").strip()
        org.trading_name = _row_get(row, "Trading name (for display)").strip()
        org.excluded = _parse_bool(_row_get(row, "EXCLUDE FROM RESULTS"))
        org.exclusion_reason = _blank_to_none(_row_get(row, "Exclusion reason"))
        org.conveyancing_confirmed = _parse_bool(_row_get(row, "Conveyancing confirmed?"))
        org.transparency_statement_captured = _parse_bool(
            _row_get(row, "Transparency statement captured?")
        )
        org.enrolled = _parse_bool(_row_get(row, "Signed up?"))
        org.proceed_enabled = _parse_bool(_row_get(row, "Proceed enabled?"))
        org.callback_enabled = _parse_bool(_row_get(row, "Callback enabled?"))
        org.active_in_pilot = _parse_bool(_row_get(row, "Active in pilot"))
        org.phone = _blank_to_none(_row_get(row, "Telephone number"))

        # The sheet sometimes records "0" as a placeholder for missing referral email.
        referral = _blank_to_none(_row_get(row, "Referral email"))
        org.referral_email = None if referral == "0" else referral

        await db.flush()
        by_id[cml_id] = org

    return by_id


async def _upsert_reputation(
    db: AsyncSession, rows: list[dict], orgs: dict[str, Organisation]
) -> None:
    for row in rows:
        cml_id = _row_get(row, "CML firm ID").strip()
        org = orgs.get(cml_id)
        if org is None:
            continue
        org.google_review_count = _parse_int(_row_get(row, "Google review count (all offices)"))
        org.google_rating = _parse_float(
            _row_get(row, "Google review average rating (all offices)")
        )
        org.adjusted_reputation_value = _parse_float(_row_get(row, "Adjusted reputation value"))

        # Some "Google reviews URL" cells contain display text like "talbots law - Google Maps"
        # instead of a real URL — those are dropped.
        url = _blank_to_none(_row_get(row, "Google reviews URL"))
        if url and not url.lower().startswith(("http://", "https://")):
            url = None
        org.google_reviews_url = url
    await db.flush()


async def _replace_complaints(
    db: AsyncSession, rows: list[dict], orgs: dict[str, Organisation]
) -> int:
    inserted = 0
    org_ids = [o.id for o in orgs.values()]
    if org_ids:
        await db.execute(delete(ComplaintsSummary).where(ComplaintsSummary.org_id.in_(org_ids)))
    for row in rows:
        cml_id = _row_get(row, "CML firm ID").strip()
        org = orgs.get(cml_id)
        if org is None:
            continue
        db.add(
            ComplaintsSummary(
                org_id=org.id,
                score=_parse_float(_row_get(row, "Complaints score")) or 0.0,
                stars=_parse_int(_row_get(row, "Stars")) or 0,
                display_text=_row_get(row, "Complaints history").strip() or "—",
                decision_count_text=_blank_to_none(_row_get(row, "Decision count text")),
                scale_context=_blank_to_none(_row_get(row, "Scale context")),
                issue_one=_blank_to_none(_row_get(row, "Issue one")),
                issue_two=_blank_to_none(_row_get(row, "Issue two")),
                issue_three=_blank_to_none(_row_get(row, "Issue three")),
                external_url=_blank_to_none(_row_get(row, "LeO hyperlink")),
            )
        )
        inserted += 1
    await db.flush()
    return inserted


async def _replace_regulatory(
    db: AsyncSession, rows: list[dict], orgs: dict[str, Organisation]
) -> int:
    inserted = 0
    org_ids = [o.id for o in orgs.values()]
    if org_ids:
        await db.execute(delete(RegulatorySummary).where(RegulatorySummary.org_id.in_(org_ids)))
    for row in rows:
        cml_id = _row_get(row, "CML firm ID").strip()
        org = orgs.get(cml_id)
        if org is None:
            continue
        # An EXCLUDE FROM SEARCH RESULTS flag on the Regulatory tab is the
        # alternative source for org.excluded (catalogue note). If it's set
        # to TRUE here and the Firms tab didn't already flag it, propagate.
        reg_excluded = _parse_bool(_row_get(row, "EXCLUDE FROM SEARCH RESULTS"))
        if reg_excluded and not org.excluded:
            org.excluded = True

        db.add(
            RegulatorySummary(
                org_id=org.id,
                score=_parse_float(_row_get(row, "Regulatory history score")) or 0.0,
                stars=_parse_int(_row_get(row, "Stars")) or 0,
                display_text=_row_get(row, "Regulatory history").strip() or "—",
                decision_count_text=_blank_to_none(_row_get(row, "Decision count text")),
                outcome_one=_blank_to_none(_row_get(row, "Outcome type - outcome one")),
                outcome_two=_blank_to_none(_row_get(row, "Outcome type - outcome two")),
                outcome_three=_blank_to_none(_row_get(row, "Outcome type - outcome three")),
                external_url=_blank_to_none(_row_get(row, "SRA link")),
            )
        )
        inserted += 1
    await db.flush()
    return inserted


def _parse_anchors(row: list[str], start: int) -> dict[int, float | None]:
    out: dict[int, float | None] = {}
    for i, anchor in enumerate(ANCHORS):
        out[anchor] = _parse_float(row[start + i] if start + i < len(row) else "")
    return out


def _parse_named_list(
    row: list[str], header: list[str], start: int, end: int
) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for i in range(start, end):
        if i >= len(header):
            break
        name = " ".join(header[i].split())  # collapse runs of whitespace in display names
        raw = row[i].strip() if i < len(row) else ""
        amount = _parse_float(raw) or 0.0
        items.append({"name": name, "amount": amount})
    return items


def _build_pricing(row: list[str], header: list[str]) -> dict:
    return {
        "freehold": {
            "purchase": _parse_anchors(row, 3),
            "sale": _parse_anchors(row, 10),
        },
        "leasehold": {
            "purchase": _parse_anchors(row, 17),
            "sale": _parse_anchors(row, 24),
        },
        "modifiers": _parse_named_list(row, header, 31, 39),
        "additional_costs": _parse_named_list(row, header, 39, 44),
        "disbursements": _parse_named_list(row, header, 44, 45),
    }


async def _replace_price_cards(
    db: AsyncSession, header: list[str], body: list[list[str]], orgs: dict[str, Organisation]
) -> int:
    inserted = 0
    org_ids = [o.id for o in orgs.values()]
    if org_ids:
        await db.execute(delete(PriceCard).where(PriceCard.org_id.in_(org_ids)))
    for row in body:
        if not row or not row[0].strip():
            continue
        cml_id = row[0].strip()
        org = orgs.get(cml_id)
        if org is None:
            continue
        price_type_str = (row[2] if len(row) > 2 else "").strip().lower()
        price_type = PRICE_TYPE_MAP.get(price_type_str, PriceType.no_data)
        db.add(
            PriceCard(
                org_id=org.id,
                price_type=price_type,
                pricing=_build_pricing(row, header),
            )
        )
        inserted += 1
    await db.flush()
    return inserted


async def _replace_offices(
    db: AsyncSession,
    firms_rows: list[dict],
    distance_rows: list[dict],
    orgs: dict[str, Organisation],
    *,
    geocode: bool,
) -> tuple[int, int]:
    org_ids = [o.id for o in orgs.values()]
    if org_ids:
        await db.execute(delete(Office).where(Office.org_id.in_(org_ids)))

    # Postcode → (lat, lng) cache so we don't geocode the same postcode twice.
    coord_cache: dict[str, tuple[float, float] | None] = {}

    async def lookup(postcode: str) -> tuple[float | None, float | None]:
        if not geocode:
            return None, None
        key = postcode.strip().upper()
        if key not in coord_cache:
            coord_cache[key] = await geocode_postcode(postcode)
        coords = coord_cache[key]
        return (coords[0], coords[1]) if coords else (None, None)

    # Primary office (one per firm) from the Firms tab.
    primary_count = 0
    primary_keys: set[tuple[str, str]] = set()
    for row in firms_rows:
        cml_id = _row_get(row, "CML firm ID").strip()
        org = orgs.get(cml_id)
        if org is None:
            continue
        postcode = _row_get(row, "Postcode").strip()
        if not postcode:
            continue
        lat, lng = await lookup(postcode)
        office_type_str = _row_get(row, "Office type").strip().upper()
        office_type = OFFICE_TYPE_MAP.get(office_type_str)
        db.add(
            Office(
                org_id=org.id,
                address_line1=_blank_to_none(_row_get(row, "Address")),
                city=_blank_to_none(_row_get(row, "Town")),
                postcode=postcode,
                lat=lat,
                lng=lng,
                is_primary=True,
                office_type=office_type,
            )
        )
        primary_keys.add((cml_id, postcode.upper()))
        primary_count += 1

    # Non-primary offices from the Distance tab; skip rows that duplicate the
    # primary office postcode for the same firm.
    secondary_count = 0
    for row in distance_rows:
        cml_id = _row_get(row, "CML firm ID").strip()
        org = orgs.get(cml_id)
        if org is None:
            continue
        postcode = _row_get(row, "Postcode (all offices)", "Postcode").strip()
        if not postcode:
            continue
        if (cml_id, postcode.upper()) in primary_keys:
            continue
        lat, lng = await lookup(postcode)
        db.add(
            Office(
                org_id=org.id,
                city=_blank_to_none(_row_get(row, "Office")),
                postcode=postcode,
                lat=lat,
                lng=lng,
                is_primary=False,
            )
        )
        secondary_count += 1

    await db.flush()
    return primary_count, secondary_count


# ── Orchestration ─────────────────────────────────────────────────────────────


async def run(input_dir: Path, *, geocode: bool, dry_run: bool) -> None:
    firms = _read_csv(input_dir / "firms.csv")
    reputation = _read_csv(input_dir / "reputation.csv")
    complaints = _read_csv(input_dir / "complaints.csv")
    regulatory = _read_csv(input_dir / "regulatory.csv")
    distance = _read_csv(input_dir / "distance.csv")
    price_header, price_body = _read_price_csv(input_dir / "price.csv")

    print(
        f"Loaded {len(firms)} firms, {len(reputation)} reputation, "
        f"{len(complaints)} complaints, {len(regulatory)} regulatory, "
        f"{len(price_body)} price, {len(distance)} distance rows"
    )

    async with async_session_factory() as db:
        try:
            orgs = await _upsert_firms(db, firms)
            print(f"  organisations upserted: {len(orgs)}")
            await _upsert_reputation(db, reputation, orgs)
            print("  reputation columns updated")
            n = await _replace_complaints(db, complaints, orgs)
            print(f"  complaints_summary rows: {n}")
            n = await _replace_regulatory(db, regulatory, orgs)
            print(f"  regulatory_summary rows: {n}")
            n = await _replace_price_cards(db, price_header, price_body, orgs)
            print(f"  price_cards: {n}")
            primary, secondary = await _replace_offices(db, firms, distance, orgs, geocode=geocode)
            print(f"  offices: {primary} primary + {secondary} secondary")

            if dry_run:
                await db.rollback()
                print("DRY-RUN — rolled back.")
            else:
                await db.commit()
                print("Committed.")
        except Exception:
            await db.rollback()
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path(__file__).parent / "seed_data" / "master_export",
        help="Directory containing the seven CSV exports.",
    )
    parser.add_argument(
        "--no-geocode",
        dest="geocode",
        action="store_false",
        default=True,
        help="Skip Fetchify postcode geocoding (offices land with NULL lat/lng).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run inside a transaction and roll back at the end.",
    )
    args = parser.parse_args()

    if not args.input_dir.is_dir():
        raise SystemExit(f"Input directory not found: {args.input_dir}")

    asyncio.run(run(args.input_dir, geocode=args.geocode, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
