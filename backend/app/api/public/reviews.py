"""Public API: submit CML native reviews."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.review import Review, ReviewInvitation, ReviewSource
from app.models.organisation import Organisation
from app.schemas.review import ReviewSubmit, ReviewResponse
from app.services.reviews import recalculate_aggregate_rating

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/invitation/{token}")
async def get_review_invitation(token: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get review invitation details (firm name etc.) for the review form."""
    inv_result = await db.execute(select(ReviewInvitation).where(ReviewInvitation.token == token))
    invitation = inv_result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invitation.used_at:
        raise HTTPException(status_code=410, detail="This review link has already been used")
    if invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="This review link has expired")

    # Load org via appointment
    from app.models.appointment import Appointment

    appt_result = await db.execute(
        select(Appointment).where(Appointment.id == invitation.appointment_id)
    )
    appt = appt_result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    org_result = await db.execute(select(Organisation).where(Organisation.id == appt.org_id))
    org = org_result.scalar_one_or_none()

    return {
        "token": token,
        "firm_name": org.name if org else "Your solicitor",
        "expires_at": invitation.expires_at,
    }


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def submit_review(body: ReviewSubmit, db: AsyncSession = Depends(get_db)):
    """Submit a CML native review via invitation token."""
    inv_result = await db.execute(
        select(ReviewInvitation).where(ReviewInvitation.token == body.token)
    )
    invitation = inv_result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invitation.used_at:
        raise HTTPException(status_code=410, detail="This review link has already been used")
    if invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="This review link has expired")

    from app.models.appointment import Appointment

    appt_result = await db.execute(
        select(Appointment).where(Appointment.id == invitation.appointment_id)
    )
    appt = appt_result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    review = Review(
        org_id=appt.org_id,
        source=ReviewSource.cml,
        rating=body.rating,
        text=body.text,
        reviewer_name=body.reviewer_name,
    )
    db.add(review)

    invitation.used_at = datetime.now(timezone.utc)
    db.add(invitation)

    await db.flush()

    # Recalculate aggregate
    org_result = await db.execute(select(Organisation).where(Organisation.id == appt.org_id))
    org = org_result.scalar_one_or_none()
    if org:
        await recalculate_aggregate_rating(db, org)

    return review
