import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ScorecardPreferenceLiteral = Literal[
    "balanced",
    "reputation",
    "price",
    "complaints",
    "regulatory",
    "distance",
    "offices",
]


class SessionCreate(BaseModel):
    practice_area: str = "residential_conveyancing"


class AnswerSubmit(BaseModel):
    question_id: str
    answer: str | list[str]


class QuestionOption(BaseModel):
    value: str
    label: str
    description: str | None = None
    hint: str | None = None


class QuestionResponse(BaseModel):
    id: str
    step: int
    text: str
    type: str
    options: list[QuestionOption] | None = None
    placeholder: str | None = None
    hint: str | None = None


class MessageItem(BaseModel):
    role: str  # "system" | "user"
    content: str
    question_id: str | None = None
    timestamp: datetime


class SessionResponse(BaseModel):
    session_id: uuid.UUID
    practice_area: str
    current_question: QuestionResponse | None
    message_history: list[dict]
    answers: dict
    scorecard_preference: ScorecardPreferenceLiteral = "balanced"
    include_distance: bool = False
    is_complete: bool
    expires_at: datetime


class SessionSaveRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)


class ScorecardPreferenceUpdate(BaseModel):
    scorecard_preference: ScorecardPreferenceLiteral
    include_distance: bool = False
