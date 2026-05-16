import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RegulatorySummary(Base):
    """Pre-computed SRA/SDT regulatory summary for a firm.

    Sourced from the Master Export workbook (Regulatory history tab) where
    cleansing/normalisation is performed upstream of the ranker.
    """

    __tablename__ = "regulatory_summary"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    score: Mapped[float] = mapped_column(Float, nullable=False)
    stars: Mapped[int] = mapped_column(Integer, nullable=False)
    display_text: Mapped[str] = mapped_column(String(255), nullable=False)
    decision_count_text: Mapped[str | None] = mapped_column(String(255))
    outcome_one: Mapped[str | None] = mapped_column(String(255))
    outcome_two: Mapped[str | None] = mapped_column(String(255))
    outcome_three: Mapped[str | None] = mapped_column(String(255))
    external_url: Mapped[str | None] = mapped_column(String(500))

    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organisation: Mapped["Organisation"] = relationship(back_populates="regulatory_summary")
