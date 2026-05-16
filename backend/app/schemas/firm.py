import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class FirmLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class FirmLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    org_id: uuid.UUID
    user_id: uuid.UUID
    email: str
    role: str


class FirmRegisterRequest(BaseModel):
    enrollment_token: uuid.UUID
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    accept_terms: bool


class OrganisationUpdate(BaseModel):
    phone: str | None = Field(None, max_length=30)
    referral_email: str | None = Field(None, max_length=255)


class OfficeResponse(BaseModel):
    id: uuid.UUID
    address_line1: str | None
    city: str | None
    postcode: str
    is_primary: bool
    office_type: str | None

    model_config = {"from_attributes": True}


class OrganisationResponse(BaseModel):
    id: uuid.UUID
    cml_firm_id: str
    sra_number: str
    name: str
    trading_name: str
    phone: str | None
    referral_email: str | None
    enrolled: bool
    excluded: bool
    exclusion_reason: str | None
    conveyancing_confirmed: bool
    transparency_statement_captured: bool
    proceed_enabled: bool
    callback_enabled: bool
    active_in_pilot: bool
    google_rating: float | None
    google_review_count: int | None
    google_reviews_url: str | None
    adjusted_reputation_value: float | None
    offices: list[OfficeResponse]

    model_config = {"from_attributes": True}


# ── Conveyancing price card ───────────────────────────────────────────────────
#
# Mirrors the Master Export "Price" tab verbatim. Anchor prices are keyed by
# the seven CML-determined purchase-price anchors (£150k, £250k, £500k, £750k,
# £1m, £1.25m, £1.5m). `null` indicates "MISSING DATA" in the upstream sheet.

AnchorPrices = dict[int, float | None]


class TransactionPrices(BaseModel):
    purchase: AnchorPrices = {}
    sale: AnchorPrices = {}


class PriceModifier(BaseModel):
    """A transaction-specific adjustment applied when the matter qualifies."""

    name: str
    amount: float


class AdditionalCost(BaseModel):
    """Standing additional fee charged for a specific administrative task."""

    name: str
    amount: float


class Disbursement(BaseModel):
    """Disbursement passed through to the client; VAT handled separately."""

    name: str
    amount: float


class PriceCardData(BaseModel):
    freehold: TransactionPrices = TransactionPrices()
    leasehold: TransactionPrices = TransactionPrices()
    modifiers: list[PriceModifier] = []
    additional_costs: list[AdditionalCost] = []
    disbursements: list[Disbursement] = []


class PriceCardResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    price_type: str
    pricing: dict
    updated_at: datetime

    model_config = {"from_attributes": True}


class ComplaintsSummaryResponse(BaseModel):
    score: float
    stars: int
    display_text: str
    decision_count_text: str | None
    scale_context: str | None
    issue_one: str | None
    issue_two: str | None
    issue_three: str | None
    external_url: str | None
    last_updated: datetime

    model_config = {"from_attributes": True}


class RegulatorySummaryResponse(BaseModel):
    score: float
    stars: int
    display_text: str
    decision_count_text: str | None
    outcome_one: str | None
    outcome_two: str | None
    outcome_three: str | None
    external_url: str | None
    last_updated: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    """Counts for the firm dashboard 2×2 grid (last 30 days)."""

    new_appointments_30d: int
    video_call_requests_30d: int
    appearances_in_results_30d: int
    new_reviews_30d: int
