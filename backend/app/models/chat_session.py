import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScorecardPreference(str, enum.Enum):
    balanced = "balanced"
    reputation = "reputation"
    price = "price"
    complaints = "complaints"
    regulatory = "regulatory"
    distance = "distance"
    offices = "offices"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_area: Mapped[str] = mapped_column(
        String(50), nullable=False, default="residential_conveyancing"
    )

    answers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    message_history: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    results_cache: Mapped[dict | None] = mapped_column(JSONB)

    scorecard_preference: Mapped[ScorecardPreference] = mapped_column(
        Enum(ScorecardPreference, name="scorecard_preference"),
        nullable=False,
        default=ScorecardPreference.balanced,
    )
    include_distance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    save_email: Mapped[str | None] = mapped_column(String(255))

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="session")
