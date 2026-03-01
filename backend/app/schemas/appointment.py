import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class AppointmentCreate(BaseModel):
    session_id: uuid.UUID
    org_id: uuid.UUID
    type: str = Field(..., pattern="^(appoint|callback)$")
    client_name: str = Field(..., min_length=2, max_length=255)
    client_email: EmailStr
    client_phone: str | None = Field(None, max_length=30)
    preferred_time: str | None = Field(None, max_length=255)
    quoted_price: Decimal | None = None
    consent_contacted: bool = Field(..., description="Consent to be contacted by firm")
    consent_terms: bool = Field(..., description="Accept terms and conditions")


class AppointmentResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    type: str
    status: str
    client_name: str
    client_email: str
    client_phone: str | None
    preferred_time: str | None
    quoted_price: Decimal | None
    created_at: datetime

    model_config = {"from_attributes": True}
