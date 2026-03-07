import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

import enum


class AppointmentType(str, enum.Enum):
    appoint = "appoint"
    callback = "callback"


class AppointmentStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False
    )

    type: Mapped[AppointmentType] = mapped_column(
        Enum(AppointmentType, name="appointment_type"), nullable=False
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status"),
        nullable=False,
        default=AppointmentStatus.pending,
    )

    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_email: Mapped[str] = mapped_column(String(255), nullable=False)
    client_phone: Mapped[str | None] = mapped_column(String(30))
    preferred_time: Mapped[str | None] = mapped_column(String(255))

    # Quote snapshot at time of appointment
    quoted_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    quote_breakdown: Mapped[str | None] = mapped_column(Text)

    # GDPR consent captured
    consent_contacted: Mapped[bool] = mapped_column(default=False, nullable=False)
    consent_terms: Mapped[bool] = mapped_column(default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    session: Mapped["ChatSession"] = relationship(back_populates="appointments")
    organisation: Mapped["Organisation"] = relationship(back_populates="appointments")
    review_invitation: Mapped["ReviewInvitation | None"] = relationship(
        back_populates="appointment"
    )
