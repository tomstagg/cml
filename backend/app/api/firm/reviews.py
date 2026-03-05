"""Firm dashboard: view and respond to reviews."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.firm_user import FirmUser
from app.models.review import Review
from app.schemas.review import FirmReviewResponse, ReviewResponse, ReviewReport

router = APIRouter(prefix="/reviews", tags=["firm-reviews"])


@router.get("", response_model=list[ReviewResponse])
async def list_reviews(
    current_user: FirmUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Review)
        .where(Review.org_id == current_user.org_id)
        .order_by(Review.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{review_id}/respond")
async def respond_to_review(
    review_id: uuid.UUID,
    body: FirmReviewResponse,
    current_user: FirmUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    review = await _get_review(db, review_id, current_user.org_id)
    review.firm_response = body.response_text
    review.firm_response_at = datetime.now(timezone.utc)
    db.add(review)
    return {"message": "Response submitted"}


@router.post("/{review_id}/report")
async def report_review(
    review_id: uuid.UUID,
    body: ReviewReport,
    current_user: FirmUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    review = await _get_review(db, review_id, current_user.org_id)
    if review.reported:
        raise HTTPException(status_code=409, detail="Review already reported")
    review.reported = True
    review.reported_at = datetime.now(timezone.utc)
    db.add(review)
    return {"message": "Review reported for admin review"}


async def _get_review(db: AsyncSession, review_id: uuid.UUID, org_id: uuid.UUID) -> Review:
    result = await db.execute(
        select(Review).where(Review.id == review_id, Review.org_id == org_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review
