import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    practice_area: str = "residential_conveyancing"


class AnswerSubmit(BaseModel):
    question_id: str
    # Accepted shapes per question type:
    #   single_choice / tenure_with_unsure / optional_postcode → str
    #   currency → int | float | str
    #   checkbox_group → list[str]
    #   dual_property_block → dict[str, str | float]
    answer: str | int | float | list[str] | dict


class QuestionOption(BaseModel):
    value: str
    label: str
    description: str | None = None


class QuestionResponse(BaseModel):
    id: str
    step: int
    section: str | None = None
    text: str
    type: str
    pathways: list[str] | None = None
    options: list[QuestionOption] | None = None
    tenure_options: list[QuestionOption] | None = None
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
    pathway: str | None
    current_question: QuestionResponse | None
    message_history: list[dict]
    answers: dict
    is_complete: bool
    expires_at: datetime


class SessionSaveRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
