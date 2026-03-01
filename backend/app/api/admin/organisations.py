"""Admin API: organisation management and enrollment."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.organisation import Organisation
from app.schemas.firm import OrganisationResponse
from app.services.email import send_enrollment_invitation
from app.services.reviews import search_google_place_id
from app.config import settings

router = APIRouter(prefix="/organisations", tags=["admin-organisations"])

# Note: In production, protect these endpoints with an admin API key header.
# For MVP, they're accessible only from Railway private network.


@router.get("")
async def list_organisations(
    enrolled: bool | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Organisation)
    if enrolled is not None:
        stmt = stmt.where(Organisation.enrolled == enrolled)
    if search:
        stmt = stmt.where(Organisation.name.ilike(f"%{search}%"))
    stmt = stmt.order_by(Organisation.name).limit(limit).offset(offset)

    result = await db.execute(stmt)
    orgs = result.scalars().all()

    count_stmt = select(func.count(Organisation.id))
    if enrolled is not None:
        count_stmt = count_stmt.where(Organisation.enrolled == enrolled)
    if search:
        count_stmt = count_stmt.where(Organisation.name.ilike(f"%{search}%"))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": [
            {
                "id": str(o.id),
                "sra_number": o.sra_number,
                "name": o.name,
                "auth_status": o.auth_status,
                "enrolled": o.enrolled,
                "email": o.email,
                "website_url": o.website_url,
            }
            for o in orgs
        ],
    }


@router.post("/{org_id}/invite-enrollment")
async def invite_enrollment(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Generate enrollment token and send invitation email."""
    result = await db.execute(select(Organisation).where(Organisation.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    if org.enrolled:
        raise HTTPException(status_code=409, detail="Organisation is already enrolled")
    if not org.email:
        raise HTTPException(status_code=400, detail="Organisation has no email address on record")

    org.enrollment_token = uuid.uuid4()
    org.enrollment_token_used = False
    db.add(org)
    await db.flush()

    enrollment_url = f"{settings.app_url}/firm/enroll/{org.enrollment_token}"
    await send_enrollment_invitation(org.email, org.name, enrollment_url)

    return {
        "message": f"Enrollment invitation sent to {org.email}",
        "enrollment_token": str(org.enrollment_token),
    }


@router.post("/{org_id}/sync-google-place")
async def sync_google_place(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Search and store Google Place ID for a firm."""
    from app.models.office import Office

    result = await db.execute(select(Organisation).where(Organisation.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    office_result = await db.execute(
        select(Office).where(Office.org_id == org_id, Office.is_primary == True)
    )
    office = office_result.scalar_one_or_none()
    postcode = office.postcode if office else ""

    place_id = await search_google_place_id(org.name, postcode)
    if not place_id:
        raise HTTPException(status_code=404, detail="Could not find Google Place ID for this firm")

    org.google_place_id = place_id
    db.add(org)

    return {"place_id": place_id, "message": "Google Place ID stored"}
