"""Public API: chat session management."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
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
    QUESTIONS,
    dynamic_options,
    find_question,
    first_question,
    get_pathway,
    is_flow_complete,
    next_question,
    validate_answer,
)
from app.services.email import send_session_save_email

router = APIRouter(prefix="/sessions", tags=["sessions"])

SESSION_EXPIRY_DAYS = 30


@router.get("/schema")
async def get_intake_schema():
    """Return the full conveyancing intake schema with pathway metadata so the
    frontend stepper can render the pathway-specific step sequence once the
    user picks Q1.
    """
    return {
        "practice_area": "residential_conveyancing",
        "questions": [
            {
                "id": q["id"],
                "step": q["step"],
                "section": q.get("section"),
                "text": q["text"],
                "type": q["type"],
                "pathways": q["pathways"],
                "options": q.get("options"),
                "tenure_options": q.get("tenure_options"),
                "placeholder": q.get("placeholder"),
                "hint": q.get("hint"),
            }
            for q in QUESTIONS
        ],
    }


def _format_question(q: dict | None, answers: dict) -> QuestionResponse | None:
    if q is None:
        return None
    options = q.get("options")
    if q["type"] == "checkbox_group":
        options = dynamic_options(q["id"], answers)
    return QuestionResponse(
        id=q["id"],
        step=q["step"],
        section=q.get("section"),
        text=q["text"],
        type=q["type"],
        pathways=q["pathways"],
        options=options,
        tenure_options=q.get("tenure_options"),
        placeholder=q.get("placeholder"),
        hint=q.get("hint"),
    )


def _build_session_response(session: ChatSession, current_question: dict | None) -> SessionResponse:
    answers = session.answers or {}
    return SessionResponse(
        session_id=session.id,
        practice_area=session.practice_area,
        pathway=get_pathway(answers),
        current_question=_format_question(current_question, answers),
        message_history=session.message_history or [],
        answers=answers,
        is_complete=is_flow_complete(answers),
        expires_at=session.expires_at,
    )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new chat session and return Q1."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRY_DAYS)
    first_q = first_question()

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
    current_q = next_question(session.answers or {})
    return _build_session_response(session, current_q)


@router.post("/{session_id}/answer", response_model=SessionResponse)
async def submit_answer(
    session_id: uuid.UUID,
    body: AnswerSubmit,
    db: AsyncSession = Depends(get_db),
):
    """Submit an answer and receive the next question (or null if complete)."""
    session = await _get_valid_session(db, session_id)

    answers = dict(session.answers or {})

    if is_flow_complete(answers):
        raise HTTPException(status_code=400, detail="Session is already complete")

    ok, error = validate_answer(body.question_id, body.answer, answers)
    if not ok:
        raise HTTPException(status_code=400, detail=error)

    answers[body.question_id] = body.answer

    history = list(session.message_history or [])
    history.append(
        {
            "role": "user",
            "content": _format_answer_for_history(body.answer),
            "question_id": body.question_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    next_q = next_question(answers)
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
    session.results_cache = None
    db.add(session)

    return _build_session_response(session, next_q)


@router.patch("/{session_id}/answer", response_model=SessionResponse)
async def patch_answer(
    session_id: uuid.UUID,
    body: AnswerSubmit,
    db: AsyncSession = Depends(get_db),
):
    """Overwrite a single answer (used by revise-mode on the results page)."""
    session = await _get_valid_session(db, session_id)
    answers = dict(session.answers or {})

    ok, error = validate_answer(body.question_id, body.answer, answers)
    if not ok:
        raise HTTPException(status_code=400, detail=error)

    answers[body.question_id] = body.answer
    session.answers = answers
    session.results_cache = None
    db.add(session)

    pathway = get_pathway(answers)
    patched = find_question(body.question_id, pathway)
    return _build_session_response(session, patched)


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


def _format_answer_for_history(answer) -> str:
    """Render an answer payload as a short string for the chat transcript."""
    if isinstance(answer, str):
        return answer
    if isinstance(answer, list):
        return ", ".join(answer) if answer else "(none selected)"
    if isinstance(answer, dict):
        return "; ".join(f"{k}={v}" for k, v in answer.items())
    return str(answer)
