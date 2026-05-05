import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RegulatorySource(str, enum.Enum):
    sra = "sra"
    sdt = "sdt"


class SraDecisionType(str, enum.Enum):
    rebuke = "rebuke"
    fine_band_a = "fine_band_a"
    fine_band_b = "fine_band_b"
    fine_band_c = "fine_band_c"
    fine_band_d = "fine_band_d"
    control_order = "control_order"
    disqualification = "disqualification"
    strike_off = "strike_off"
    intervention = "intervention"


class RegulatoryDecision(Base):
    """A single SRA or SDT regulatory decision against a firm.

    `deduction` is pre-computed from the Annex One §7 outcome tables so the
    runtime ranker only consumes structured numbers.
    """

    __tablename__ = "regulatory_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False
    )

    source: Mapped[RegulatorySource] = mapped_column(
        Enum(RegulatorySource, name="regulatory_source"), nullable=False
    )
    decision_id: Mapped[str | None] = mapped_column(String(50))
    decision_date: Mapped[date | None] = mapped_column(Date)
    decision_type: Mapped[SraDecisionType] = mapped_column(
        Enum(SraDecisionType, name="sra_decision_type"), nullable=False
    )

    deduction: Mapped[float] = mapped_column(Float, nullable=False)
    sdt_fine_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    source_url: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    organisation: Mapped["Organisation"] = relationship(back_populates="regulatory_decisions")
