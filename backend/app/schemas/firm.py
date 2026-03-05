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


class PriceCardBand(BaseModel):
    estate_value_min: float = 0
    estate_value_max: float | None = None
    fee: float
    currency: str = "GBP"


class PriceCardAdjustment(BaseModel):
    name: str
    amount: float
    condition: str | None = None


class PriceCardDisbursement(BaseModel):
    name: str
    amount: float
    estimated: bool = False


class PriceCardData(BaseModel):
    practice_area: str = "probate"
    matter_types: list[str] = ["grant_only", "full_administration"]
    pricing_model: str = Field(..., pattern="^(fixed|band|percentage)$")
    bands: list[PriceCardBand] = []
    adjustments: list[PriceCardAdjustment] = []
    disbursements: list[PriceCardDisbursement] = []
    vat_applies_to_fees: bool = True
    percentage_rate: float | None = None


class PriceCardCreate(BaseModel):
    practice_area: str = "probate"
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
    total_appearances: int
    total_appointments: int
    total_callbacks: int
    aggregate_rating: float | None
    aggregate_review_count: int | None
    recent_appointments: list[dict]
