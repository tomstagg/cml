import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


CallbackWindow = Literal["09:00-11:00", "11:00-13:00", "13:00-15:00", "15:00-17:00"]


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


class BulkCallbackFirm(BaseModel):
    org_id: uuid.UUID
    quoted_price: Decimal | None = None
    price_type: Literal["estimated", "verified"] | None = None


class BulkCallbackCreate(BaseModel):
    session_id: uuid.UUID
    client_name: str = Field(..., min_length=2, max_length=255)
    client_email: EmailStr
    client_phone: str = Field(..., max_length=30)
    preferred_callback_window: CallbackWindow
    data_sharing_consent: bool
    firms: list[BulkCallbackFirm] = Field(..., min_length=1, max_length=3)

    @field_validator("firms")
    @classmethod
    def _no_duplicate_orgs(cls, v: list[BulkCallbackFirm]) -> list[BulkCallbackFirm]:
        if len({f.org_id for f in v}) != len(v):
            raise ValueError("firms must be distinct")
        return v

    @field_validator("data_sharing_consent")
    @classmethod
    def _consent_must_be_true(cls, v: bool) -> bool:
        if not v:
            raise ValueError("data_sharing_consent must be true")
        return v


class BulkCallbackResponse(BaseModel):
    created: int
    appointment_ids: list[uuid.UUID]
