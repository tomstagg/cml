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


class FactorScores(BaseModel):
    """Per-factor scores out of 100, retained at full precision."""

    reputation: float
    price: float | None
    complaints: float
    regulatory: float
    distance: float | None
    offices: float


class DecisionSource(BaseModel):
    decision_date: str | None
    url: str


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
    office_count: int = 1
    quote: QuoteBreakdown | None
    factor_scores: FactorScores | None = None
    complaints_sources: list[DecisionSource] = []
    regulatory_sources: list[DecisionSource] = []
    score: float


class SearchResponse(BaseModel):
    """Full-market ranking + top-5 contactable extracted from it.

    `results` is the full WMCA market in rank order.
    `top_five_contactable` is the highest-ranked enrolled firms, drawn from
    the same ranking (Annex One §3.5 sequencing rule).
    """

    session_id: uuid.UUID
    results: list[FirmResult]
    # Populated in Phase D when the 6-factor ranker lands. Until then, the
    # legacy search service returns the empty list and clients fall back to
    # `results`.
    top_five_contactable: list[FirmResult] = []
    total: int
    postcode: str | None
    scorecard_preference: str = "balanced"
    include_distance: bool = False
