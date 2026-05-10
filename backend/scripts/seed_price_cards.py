#!/usr/bin/env python3
"""Pre-load active conveyancing price cards + enrol participating firms (J4).

The MVP has no admin pricing form — every WMCA firm is priced and (where
applicable) flagged as enrolled by the founder via this script. Run it
after `import_sra_csv.py` has created the organisations.

Annex One §3 requires the full WMCA market to be ranked, so every firm
gets an active price card — not just the enrolled subset. The top-5
contactable extractor in the search service then filters on
`enrolled=true`, so the "whole of market / fully independent" claim
holds.

Source of truth is `seed_synthetic.FIRMS` (with `enrolled` flagging the
participating subset) so the synthetic dataset and the ops bootstrap
stay aligned. When real firms come on board, edit FIRMS in
seed_synthetic.py and re-run this script.

Two side-effects per firm:
  1. A single active conveyancing PriceCard is upserted on
     (org_id, residential_conveyancing). Re-running replaces in place.
  2. If the firm spec has `enrolled=True`, `Organisation.enrolled` is
     set to True. The firm-portal `/enroll/{token}` flow exists but is
     bypassed for the pilot — this script is canonical.

Usage:
    docker-compose exec backend python scripts/seed_price_cards.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models.organisation import Organisation
from app.models.price_card import PriceCard
from scripts.seed_synthetic import FIRMS, price_card

PRACTICE_AREA = "residential_conveyancing"


async def seed_price_cards() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        created = 0
        updated = 0
        skipped = 0
        newly_enrolled = 0

        for spec in FIRMS:
            sra = spec[0]
            enrolled_target = spec[4]
            fee_offset = spec[9]

            org = (
                await db.execute(select(Organisation).where(Organisation.sra_number == sra))
            ).scalar_one_or_none()
            if not org:
                print(f"  Skipping {sra}: organisation not found (run import_sra_csv first?)")
                skipped += 1
                continue

            if enrolled_target and not org.enrolled:
                org.enrolled = True
                db.add(org)
                newly_enrolled += 1

            pricing = price_card(fee_offset)

            existing = (
                await db.execute(
                    select(PriceCard).where(
                        PriceCard.org_id == org.id,
                        PriceCard.practice_area == PRACTICE_AREA,
                        PriceCard.active.is_(True),
                    )
                )
            ).scalar_one_or_none()

            if existing:
                existing.pricing = pricing
                existing.confidence = 1.0
                db.add(existing)
                updated += 1
            else:
                db.add(
                    PriceCard(
                        org_id=org.id,
                        practice_area=PRACTICE_AREA,
                        pricing=pricing,
                        confidence=1.0,
                        active=True,
                    )
                )
                created += 1

        await db.commit()
        print(
            f"Price cards: {created} created, {updated} updated, {skipped} skipped; "
            f"{newly_enrolled} newly enrolled"
        )


if __name__ == "__main__":
    asyncio.run(seed_price_cards())
