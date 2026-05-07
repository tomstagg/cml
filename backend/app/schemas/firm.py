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
    website_url: str | None = Field(None, max_length=500)
    phone: str | None = Field(None, max_length=30)
    email: str | None = Field(None, max_length=255)


class OfficeResponse(BaseModel):
    id: uuid.UUID
    address_line1: str | None
    address_line2: str | None
    city: str | None
    county: str | None
    postcode: str
    is_primary: bool

    model_config = {"from_attributes": True}


class OrganisationResponse(BaseModel):
    id: uuid.UUID
    sra_number: str
    name: str
    auth_status: str
    website_url: str | None
    phone: str | None
    email: str | None
    enrolled: bool
    aggregate_rating: float | None
    aggregate_review_count: int | None
    offices: list[OfficeResponse]

    model_config = {"from_attributes": True}


# ── Conveyancing price card ───────────────────────────────────────────────────
class PriceCardBand(BaseModel):
    """Fee band keyed off purchase price (Annex One §10 / requirements §5.2)."""

    purchase_price_min: float = 0
    purchase_price_max: float | None = None
    fee: float
    currency: str = "GBP"


class PriceCardAdjustment(BaseModel):
    """Conditional supplement applied when an answer evaluates truthy.

    Supported `condition` strings (matched in price_calc):
      tenure==leasehold | new_build==true | help_to_buy_isa==true |
      shared_ownership==true | mortgage==true
    """

    name: str
    amount: float
    condition: str | None = None


class PriceCardDisbursement(BaseModel):
    """Included disbursement, stored exclusive of VAT with a per-row VAT flag."""

    name: str
    amount: float
    vat_applies: bool = False


class PriceCardData(BaseModel):
    practice_area: str = "residential_conveyancing"
    matter_types: list[str] = ["purchase", "sale", "purchase_and_sale", "remortgage"]
    pricing_model: str = Field("band", pattern="^(fixed|band)$")
    bands: list[PriceCardBand] = []
    adjustments: list[PriceCardAdjustment] = []
    included_disbursements: list[PriceCardDisbursement] = []
    excluded_disbursements_note: str | None = None
    vat_applies_to_fees: bool = True


class PriceCardCreate(BaseModel):
    practice_area: str = "residential_conveyancing"
    pricing: PriceCardData


class PriceCardResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    practice_area: str
    pricing: dict
    active: bool
    updated_at: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    """Counts for the firm dashboard 2×2 grid (last 30 days)."""

    new_appointments_30d: int
    video_call_requests_30d: int
    appearances_in_results_30d: int
    new_reviews_30d: int
