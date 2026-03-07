"""Firm dashboard: price card management."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.firm_user import FirmUser
from app.models.price_card import PriceCard
from app.schemas.firm import PriceCardCreate, PriceCardResponse
from app.services.price_calc import calculate_quote
from app.services.chat import get_complexity_flags

router = APIRouter(prefix="/pricing", tags=["firm-pricing"])


@router.get("", response_model=list[PriceCardResponse])
async def list_price_cards(
    current_user: FirmUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PriceCard).where(PriceCard.org_id == current_user.org_id))
    return result.scalars().all()


@router.post("", response_model=PriceCardResponse, status_code=status.HTTP_201_CREATED)
async def create_price_card(
    body: PriceCardCreate,
    current_user: FirmUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Deactivate existing cards for this practice area
    existing_result = await db.execute(
        select(PriceCard).where(
            PriceCard.org_id == current_user.org_id,
            PriceCard.practice_area == body.practice_area,
            PriceCard.active == True,
        )
    )
    for old_card in existing_result.scalars().all():
        old_card.active = False
        db.add(old_card)

    card = PriceCard(
        org_id=current_user.org_id,
        practice_area=body.practice_area,
        pricing=body.pricing.model_dump(),
        active=True,
    )
    db.add(card)
    await db.flush()
    return card


@router.get("/{card_id}", response_model=PriceCardResponse)
async def get_price_card(
    card_id: uuid.UUID,
    current_user: FirmUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    card = await _get_card(db, card_id, current_user.org_id)
    return card


@router.put("/{card_id}", response_model=PriceCardResponse)
async def update_price_card(
    card_id: uuid.UUID,
    body: PriceCardCreate,
    current_user: FirmUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    card = await _get_card(db, card_id, current_user.org_id)
    card.pricing = body.pricing.model_dump()
    card.practice_area = body.practice_area
    db.add(card)
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_price_card(
    card_id: uuid.UUID,
    current_user: FirmUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    card = await _get_card(db, card_id, current_user.org_id)
    card.active = False
    db.add(card)


@router.post("/{card_id}/preview")
async def preview_price_card(
    card_id: uuid.UUID,
    current_user: FirmUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Preview a calculated quote for the price card with sample inputs."""
    card = await _get_card(db, card_id, current_user.org_id)

    sample_answers = {
        "service_type": "full_administration",
        "estate_value": "100k_325k",
        "iht400": "no",
        "overseas_assets": "no",
        "investments_count": "simple",
        "uk_property_count": "1",
    }
    complexity = get_complexity_flags(sample_answers)
    quote = calculate_quote(card.pricing, complexity)

    return {
        "card_id": card_id,
        "sample_inputs": sample_answers,
        "quote": quote,
    }


async def _get_card(db: AsyncSession, card_id: uuid.UUID, org_id: uuid.UUID) -> PriceCard:
    result = await db.execute(
        select(PriceCard).where(PriceCard.id == card_id, PriceCard.org_id == org_id)
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Price card not found")
    return card
