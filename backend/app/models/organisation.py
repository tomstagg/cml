import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # External keys
    cml_firm_id: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    sra_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    trading_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Contact
    phone: Mapped[str | None] = mapped_column(String(30))
    referral_email: Mapped[str | None] = mapped_column(String(255))

    # Exclusion (broader than SRA intervention — Annex One §8.13)
    excluded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exclusion_reason: Mapped[str | None] = mapped_column(Text)

    # Pilot data-quality / participation flags (sourced from Master Export "Firms" tab)
    conveyancing_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    transparency_statement_captured: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    enrolled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    proceed_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    callback_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active_in_pilot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Firm-portal enrollment token (backend-generated, not from spreadsheet)
    enrollment_token: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), unique=True)
    enrollment_token_used: Mapped[bool] = mapped_column(Boolean, default=False)

    # Reputation (pre-baked in spreadsheet)
    google_rating: Mapped[float | None] = mapped_column(Float)
    google_review_count: Mapped[int | None] = mapped_column()
    google_reviews_url: Mapped[str | None] = mapped_column(String(500))
    adjusted_reputation_value: Mapped[float | None] = mapped_column(Float)

    # Provenance
    master_export_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    offices: Mapped[list["Office"]] = relationship(
        back_populates="organisation", cascade="all, delete-orphan"
    )
    price_card: Mapped["PriceCard | None"] = relationship(
        back_populates="organisation", cascade="all, delete-orphan", uselist=False
    )
    firm_users: Mapped[list["FirmUser"]] = relationship(
        back_populates="organisation", cascade="all, delete-orphan"
    )
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="organisation")
    reviews: Mapped[list["Review"]] = relationship(back_populates="organisation")
    complaints_summary: Mapped["ComplaintsSummary | None"] = relationship(
        back_populates="organisation", cascade="all, delete-orphan", uselist=False
    )
    regulatory_summary: Mapped["RegulatorySummary | None"] = relationship(
        back_populates="organisation", cascade="all, delete-orphan", uselist=False
    )
