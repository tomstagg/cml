import uuid
from typing import Literal

from pydantic import BaseModel, Field

EventType = Literal[
    "page_view",
    "intake_started",
    "intake_completed",
    "scorecard_chosen",
    "results_viewed",
    "proceed",
    "callback",
]


class AnalyticsEventCreate(BaseModel):
    event_type: EventType
    session_id: uuid.UUID | None = None
    metadata: dict = Field(default_factory=dict)
