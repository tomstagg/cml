"""Public API: chat session management."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.chat_session import ChatSession
from app.schemas.chat import (
    AnswerSubmit,
    QuestionResponse,
    SessionCreate,
    SessionResponse,
    SessionSaveRequest,
)
from app.services.chat import (
    PROBATE_QUESTIONS,
    QUESTION_INDEX,
    get_first_question,
    get_next_question,
    is_flow_complete,
)
from app.services.email import send_session_save_email
from app.config import settings

router = APIRouter(prefix="/sessions", tags=["sessions"])

SESSION_EXPIRY_DAYS = 30


def _format_question(q: dict | None) -> QuestionResponse | None:
    if q is None:
        return None
    return QuestionResponse(
        id=q["id"],
        step=q["step"],
        text=q["text"],
        type=q["type"],
        options=q.get("options"),
        placeholder=q.get("placeholder"),
        hint=q.get("hint"),
    )


def _build_session_response(session: ChatSession, current_question: dict | None) -> SessionResponse:
    return SessionResponse(
        session_id=session.id,
        practice_area=session.practice_area,
        current_question=_format_question(current_question),
        message_history=session.message_history or [],
        answers=session.answers or {},
        is_complete=is_flow_complete(session.answers or {}),
        expires_at=session.expires_at,
    )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new chat session and return the first question."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRY_DAYS)
    first_q = get_first_question()

    session = ChatSession(
        id=uuid.uuid4(),
        practice_area=body.practice_area,
        answers={},
        message_history=[
            {
                "role": "system",
                "content": first_q["text"],
                "question_id": first_q["id"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
        expires_at=expires_at,
    )
    db.add(session)
    await db.flush()

    return _build_session_response(session, first_q)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Resume a saved session."""
    session = await _get_valid_session(db, session_id)

    # Determine current question
    answered_ids = list((session.answers or {}).keys())
    if not answered_ids:
        current_q = get_first_question()
    elif is_flow_complete(session.answers):
        current_q = None
    else:
        last_answered = answered_ids[-1]
        current_q = get_next_question(last_answered, session.answers)

    return _build_session_response(session, current_q)


@router.post("/{session_id}/answer", response_model=SessionResponse)
async def submit_answer(
    session_id: uuid.UUID,
    body: AnswerSubmit,
    db: AsyncSession = Depends(get_db),
):
    """Submit an answer and receive the next question."""
    session = await _get_valid_session(db, session_id)

    if is_flow_complete(session.answers or {}):
        raise HTTPException(status_code=400, detail="Session is already complete")

    # Validate question exists
    if body.question_id not in QUESTION_INDEX:
        raise HTTPException(status_code=400, detail=f"Unknown question: {body.question_id}")

    # Record answer
    answers = dict(session.answers or {})
    answer_value = body.answer if isinstance(body.answer, str) else body.answer
    answers[body.question_id] = answer_value

    # Append to message history
    history = list(session.message_history or [])
    history.append(
        {
            "role": "user",
            "content": str(answer_value)
            if isinstance(answer_value, str)
            else ", ".join(answer_value),
            "question_id": body.question_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    # Determine next question
    next_q = get_next_question(body.question_id, answers)
    if next_q:
        history.append(
            {
                "role": "system",
                "content": next_q["text"],
                "question_id": next_q["id"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    session.answers = answers
    session.message_history = history
    session.results_cache = None  # Invalidate cache on new answer
    db.add(session)

    return _build_session_response(session, next_q)


@router.post("/{session_id}/save")
async def save_session(
    session_id: uuid.UUID,
    body: SessionSaveRequest,
    db: AsyncSession = Depends(get_db),
):
    """Save session email for resume URL."""
    session = await _get_valid_session(db, session_id)
    session.save_email = body.email
    db.add(session)

    resume_url = f"{settings.app_url}/chat?session={session_id}"
    await send_session_save_email(body.email, resume_url)

    return {"message": "Session saved. Check your email for the resume link."}


async def _get_valid_session(db: AsyncSession, session_id: uuid.UUID) -> ChatSession:
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Session has expired")
    return session
