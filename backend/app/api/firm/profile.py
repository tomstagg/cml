"""Firm dashboard: profile and organisation management."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.firm_user import FirmUser
from app.models.organisation import Organisation
from app.schemas.firm import OrganisationResponse, OrganisationUpdate

router = APIRouter(prefix="/profile", tags=["firm-profile"])


@router.get("", response_model=OrganisationResponse)
async def get_profile(
    current_user: FirmUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org = await _get_org(db, current_user.org_id)
    return org


@router.patch("", response_model=OrganisationResponse)
async def update_profile(
    body: OrganisationUpdate,
    current_user: FirmUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org = await _get_org(db, current_user.org_id)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(org, field, value)

    db.add(org)
    return org


async def _get_org(db: AsyncSession, org_id: uuid.UUID) -> Organisation:
    result = await db.execute(
        select(Organisation).where(Organisation.id == org_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return org
