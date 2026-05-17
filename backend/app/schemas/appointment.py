import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class AppointmentCreate(BaseModel):
    session_id: uuid.UUID
    org_id: uuid.UUID
    type: str = Field(..., pattern="^(select|callback)$")
    client_name: str = Field(..., min_length=2, max_length=255)
    client_email: EmailStr
    client_phone: str | None = Field(None, max_length=30)
    preferred_time: str | None = Field(None, max_length=255)
    quoted_price: Decimal | None = None

    # Callback-only consents (legacy two-checkbox flow).
    consent_contacted: bool = False
    consent_terms: bool = False

    # Select-only fields (CML Select workflow).
    data_sharing_consent: bool = False
    purchase_property_postcode: str | None = Field(None, max_length=16)
    sale_property_postcode: str | None = Field(None, max_length=16)
    price_type: Literal["estimated", "verified"] | None = None


class ConflictCheckRequest(BaseModel):
    outcome: str = Field(..., pattern="^(clear|conflict)$")


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
