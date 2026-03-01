import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReviewSubmit(BaseModel):
    token: uuid.UUID
    rating: float = Field(..., ge=1, le=5)
    text: str = Field(..., min_length=10, max_length=2000)
    reviewer_name: str | None = Field(None, max_length=255)


class ReviewResponse(BaseModel):
    id: uuid.UUID
    source: str
    rating: float
    text: str | None
    reviewer_name: str | None
    firm_response: str | None
    firm_response_at: datetime | None
    created_at: datetime
    reported: bool

    model_config = {"from_attributes": True}


class FirmReviewResponse(BaseModel):
    response_text: str = Field(..., max_length=500)


class ReviewReport(BaseModel):
    reason: str = Field(..., max_length=500)
