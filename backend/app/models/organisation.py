import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sra_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_status: Mapped[str] = mapped_column(String(50), nullable=False, default="authorised")
    website_url: Mapped[str | None] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255))

    # Enrollment
    enrolled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enrollment_token: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), unique=True)
    enrollment_token_used: Mapped[bool] = mapped_column(Boolean, default=False)

    # Google Places
    google_place_id: Mapped[str | None] = mapped_column(String(255))
    google_rating: Mapped[float | None] = mapped_column()
    google_review_count: Mapped[int | None] = mapped_column()

    # Aggregate rating (computed, cached)
    aggregate_rating: Mapped[float | None] = mapped_column()
    aggregate_review_count: Mapped[int | None] = mapped_column()

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
    price_cards: Mapped[list["PriceCard"]] = relationship(
        back_populates="organisation", cascade="all, delete-orphan"
    )
    firm_users: Mapped[list["FirmUser"]] = relationship(
        back_populates="organisation", cascade="all, delete-orphan"
    )
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="organisation")
    reviews: Mapped[list["Review"]] = relationship(back_populates="organisation")
