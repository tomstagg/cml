import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

import enum


class ReviewSource(str, enum.Enum):
    cml = "cml"
    google = "google"


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False
    )

    source: Mapped[ReviewSource] = mapped_column(
        Enum(ReviewSource, name="review_source"), nullable=False
    )

    rating: Mapped[float] = mapped_column(Numeric(2, 1), nullable=False)
    text: Mapped[str | None] = mapped_column(Text)
    reviewer_name: Mapped[str | None] = mapped_column(String(255))

    # For Google reviews: their unique review ID
    external_id: Mapped[str | None] = mapped_column(String(255))

    # Firm response
    firm_response: Mapped[str | None] = mapped_column(Text)
    firm_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Moderation
    reported: Mapped[bool] = mapped_column(default=False, nullable=False)
    reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    organisation: Mapped["Organisation"] = relationship(back_populates="reviews")


class ReviewInvitation(Base):
    __tablename__ = "review_invitations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    appointment: Mapped["Appointment"] = relationship(back_populates="review_invitation")
