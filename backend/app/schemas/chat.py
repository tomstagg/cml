import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    practice_area: str = "probate"


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
    is_complete: bool
    expires_at: datetime


class SessionSaveRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
