import uuid
from pydantic import BaseModel


class QuoteBreakdown(BaseModel):
    base_fee: float
    adjustments: list[dict]
    fees_subtotal: float
    vat: float
    disbursements: list[dict]
    disbursements_total: float
    total: float
    currency: str
    pricing_model: str


class FirmResult(BaseModel):
    rank: int
    org_id: uuid.UUID
    name: str
    sra_number: str
    auth_status: str
    enrolled: bool
    website_url: str | None
    aggregate_rating: float | None
    aggregate_review_count: int | None
    postcode: str | None
    city: str | None
    distance_km: float | None
    quote: QuoteBreakdown | None
    score: float


class SearchResponse(BaseModel):
    session_id: uuid.UUID
    results: list[FirmResult]
    total: int
    postcode: str | None
