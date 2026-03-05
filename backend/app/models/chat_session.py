import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_area: Mapped[str] = mapped_column(String(50), nullable=False, default="probate")

    # Step-by-step answers keyed by question id
    answers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Full message history for chat UI replay
    message_history: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Cached results (invalidated when answers change)
    results_cache: Mapped[dict | None] = mapped_column(JSONB)

    # "Save for later" email
    save_email: Mapped[str | None] = mapped_column(String(255))

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="session")
