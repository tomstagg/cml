#!/usr/bin/env python3
"""
Import SRA authorised firms CSV → organisations + offices.

Usage:
    python scripts/import_sra_csv.py --csv path/to/sra_firms.csv [--region "Greater London"] [--geocode]

The SRA CSV can be downloaded from:
https://www.sra.org.uk/consumers/using-legal-services/check-solicitor-firm/

Expected columns (flexible — script tries multiple column name variants):
  - Organisation name
  - SRA number
  - Status (authorised/revoked etc.)
  - Address fields
  - Postcode
  - Website
  - Phone
  - Email
"""

import argparse
import asyncio
import csv
import sys
from pathlib import Path

# Add backend root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models.organisation import Organisation
from app.models.office import Office
from app.services.geocoding import geocode_postcode

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Column name mappings (handle SRA CSV variations)
COL_ALIASES = {
    "name": ["Organisation name", "Name", "Firm name", "organisation_name"],
    "sra_number": ["SRA number", "sra_number", "SRA ID", "Reference number"],
    "auth_status": ["Status", "auth_status", "Authorisation status"],
    "address_line1": ["Address line 1", "address_line1", "Address 1"],
    "address_line2": ["Address line 2", "address_line2", "Address 2"],
    "city": ["City", "city", "Town"],
    "county": ["County", "county"],
    "postcode": ["Postcode", "postcode", "Post code", "ZIP"],
    "website_url": ["Website", "website_url", "URL", "Web address"],
    "phone": ["Phone", "phone", "Telephone", "Tel"],
    "email": ["Email", "email", "Email address"],
}


def resolve_col(row: dict, field: str) -> str | None:
    for alias in COL_ALIASES.get(field, [field]):
        if alias in row:
            return row[alias].strip() or None
    return None


async def import_csv(csv_path: str, region_filter: str | None, do_geocode: bool):
    print(f"Reading {csv_path}...")
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Found {len(rows)} rows in CSV")

    async with SessionLocal() as db:
        created = 0
        skipped = 0
        updated = 0

        for row in rows:
            sra_number = resolve_col(row, "sra_number")
            if not sra_number:
                skipped += 1
                continue

            auth_status = (resolve_col(row, "auth_status") or "authorised").lower()

            # Filter to authorised only
            if "authorised" not in auth_status and auth_status != "authorised":
                skipped += 1
                continue

            postcode = resolve_col(row, "postcode") or ""
            city = resolve_col(row, "city") or ""

            # Region filter (by city or county)
            if region_filter:
                county = resolve_col(row, "county") or ""
                if region_filter.lower() not in city.lower() and region_filter.lower() not in county.lower() and region_filter.lower() not in postcode.lower():
                    skipped += 1
                    continue

            name = resolve_col(row, "name")
            if not name:
                skipped += 1
                continue

            # Upsert organisation
            existing = await db.execute(
                select(Organisation).where(Organisation.sra_number == sra_number)
            )
            org = existing.scalar_one_or_none()

            if org:
                org.name = name
                org.auth_status = auth_status
                org.website_url = resolve_col(row, "website_url")
                org.phone = resolve_col(row, "phone")
                org.email = resolve_col(row, "email")
                db.add(org)
                updated += 1
            else:
                org = Organisation(
                    sra_number=sra_number,
                    name=name,
                    auth_status=auth_status,
                    website_url=resolve_col(row, "website_url"),
                    phone=resolve_col(row, "phone"),
                    email=resolve_col(row, "email"),
                )
                db.add(org)
                await db.flush()
                created += 1

            # Upsert primary office
            office_result = await db.execute(
                select(Office).where(Office.org_id == org.id, Office.is_primary == True)
            )
            office = office_result.scalar_one_or_none()

            lat_lng = None
            if do_geocode and postcode:
                lat_lng = await geocode_postcode(postcode)
                if lat_lng:
                    print(f"  Geocoded {postcode} → {lat_lng}")

            location = None
            if lat_lng:
                from geoalchemy2 import WKTElement
                location = WKTElement(f"POINT({lat_lng[1]} {lat_lng[0]})", srid=4326)

            if not office:
                office = Office(
                    org_id=org.id,
                    address_line1=resolve_col(row, "address_line1"),
                    address_line2=resolve_col(row, "address_line2"),
                    city=city,
                    county=resolve_col(row, "county"),
                    postcode=postcode,
                    is_primary=True,
                    location=location,
                )
                db.add(office)
            else:
                office.postcode = postcode
                office.city = city
                if location:
                    office.location = location
                db.add(office)

        await db.commit()
        print(f"\nImport complete: {created} created, {updated} updated, {skipped} skipped")


def main():
    parser = argparse.ArgumentParser(description="Import SRA CSV data")
    parser.add_argument("--csv", required=True, help="Path to SRA CSV file")
    parser.add_argument("--region", help="Filter by region (city/county name)")
    parser.add_argument("--geocode", action="store_true", help="Geocode postcodes via Fetchify")
    args = parser.parse_args()

    asyncio.run(import_csv(args.csv, args.region, args.geocode))


if __name__ == "__main__":
    main()
