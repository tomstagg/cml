"""Firm dashboard: price card management.

One price card per firm (residential conveyancing only for the pilot).
When a firm submits via this portal it is recorded as ``verified`` pricing;
``estimated`` and ``no_data`` only enter the system via the Master Export
ingestion path.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.firm_user import FirmUser
from app.models.price_card import PriceCard, PriceType
from app.schemas.firm import PriceCardData, PriceCardResponse
from app.services.chat import get_intake_flags
from app.services.price_calc import calculate_total_effective_price

router = APIRouter(prefix="/pricing", tags=["firm-pricing"])


@router.get("", response_model=PriceCardResponse | None)
async def get_price_card(
    current_user: FirmUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PriceCard).where(PriceCard.org_id == current_user.org_id))
    return result.scalar_one_or_none()


@router.put("", response_model=PriceCardResponse)
async def upsert_price_card(
    body: PriceCardData,
    current_user: FirmUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PriceCard).where(PriceCard.org_id == current_user.org_id))
    card = result.scalar_one_or_none()
    pricing_payload = body.model_dump()
    if card is None:
        card = PriceCard(
            org_id=current_user.org_id,
            price_type=PriceType.verified,
            pricing=pricing_payload,
        )
        db.add(card)
    else:
        card.price_type = PriceType.verified
        card.pricing = pricing_payload
        db.add(card)
    await db.flush()
    await db.refresh(card)
    return card


@router.post("/preview")
async def preview_price_card(
    current_user: FirmUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Preview a calculated quote for the firm's current price card."""
    result = await db.execute(select(PriceCard).where(PriceCard.org_id == current_user.org_id))
    card = result.scalar_one_or_none()
    if card is None:
        return {"quote": None, "sample_inputs": None}

    sample_answers = {
        "transaction_type": "buying",
        "purchase_tenure_type": "leasehold",
        "purchase_property_value": 275_000,
        "transaction_details": ["mortgage_required"],
        "distance_preference": "B1 1AA",
    }
    flags = get_intake_flags(sample_answers)
    quote = calculate_total_effective_price(card.pricing, flags, card.price_type)

    return {"sample_inputs": sample_answers, "quote": quote}
