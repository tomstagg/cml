"""Admin API: organisation management and enrollment."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.organisation import Organisation
from app.services.email import send_enrollment_invitation

router = APIRouter(prefix="/organisations", tags=["admin-organisations"])


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
        stmt = stmt.where(Organisation.trading_name.ilike(f"%{search}%"))
    stmt = stmt.order_by(Organisation.trading_name).limit(limit).offset(offset)

    result = await db.execute(stmt)
    orgs = result.scalars().all()

    count_stmt = select(func.count(Organisation.id))
    if enrolled is not None:
        count_stmt = count_stmt.where(Organisation.enrolled == enrolled)
    if search:
        count_stmt = count_stmt.where(Organisation.trading_name.ilike(f"%{search}%"))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": [
            {
                "id": str(o.id),
                "cml_firm_id": o.cml_firm_id,
                "sra_number": o.sra_number,
                "name": o.name,
                "trading_name": o.trading_name,
                "enrolled": o.enrolled,
                "excluded": o.excluded,
                "active_in_pilot": o.active_in_pilot,
                "referral_email": o.referral_email,
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
    if not org.referral_email:
        raise HTTPException(status_code=400, detail="Organisation has no referral email on record")

    org.enrollment_token = uuid.uuid4()
    org.enrollment_token_used = False
    db.add(org)
    await db.flush()

    enrollment_url = f"{settings.app_url}/enroll/{org.enrollment_token}"
    await send_enrollment_invitation(org.referral_email, org.trading_name, enrollment_url)

    return {
        "message": f"Enrollment invitation sent to {org.referral_email}",
        "enrollment_token": str(org.enrollment_token),
    }
