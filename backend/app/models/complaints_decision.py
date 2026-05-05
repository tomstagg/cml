import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ComplaintsDecision(Base):
    """A single Legal Ombudsman decision against a firm.

    Severity band, severity score, and remedy-amount score are pre-computed at
    ingest so the runtime ranker only consumes structured numbers
    (Annex One §6, §6.10–§6.18).
    """

    __tablename__ = "complaints_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False
    )

    decision_id: Mapped[str | None] = mapped_column(String(50))
    decision_date: Mapped[date | None] = mapped_column(Date)
    remedy_type: Mapped[str | None] = mapped_column(String(100))

    severity_band: Mapped[int] = mapped_column(Integer, nullable=False)
    severity_score: Mapped[float] = mapped_column(Float, nullable=False)

    remedy_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    remedy_amount_score: Mapped[float] = mapped_column(Float, nullable=False)

    complaint_handling_penalty: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    source_url: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    organisation: Mapped["Organisation"] = relationship(back_populates="complaints_decisions")
