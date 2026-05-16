import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PriceType(str, enum.Enum):
    estimated = "estimated"
    verified = "verified"
    no_data = "no_data"


class PriceCard(Base):
    __tablename__ = "price_cards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    price_type: Mapped[PriceType] = mapped_column(
        Enum(PriceType, name="price_type"), nullable=False, default=PriceType.no_data
    )

    # Verbatim JSONB shape — see PriceCardData schema (app/schemas/firm.py)
    pricing: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organisation: Mapped["Organisation"] = relationship(back_populates="price_card")
