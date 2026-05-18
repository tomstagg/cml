"""Public API: firm search and results."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.appointment import Appointment, AppointmentType
from app.models.chat_session import ChatSession
from app.schemas.search import SearchResponse
from app.services.chat import build_intake_summary, get_intake_flags, is_flow_complete
from app.services.search import search_firms

router = APIRouter(prefix="/search", tags=["search"])

# Default cache key used when the consumer hasn't reordered the results.
DEFAULT_SCORECARD = "balanced"


@router.get("/{session_id}", response_model=SearchResponse)
async def get_results(
    session_id: uuid.UUID,
    scorecard_preference: str = Query(DEFAULT_SCORECARD),
    include_distance: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get ranked firm results for a completed chat session.

    `scorecard_preference` and `include_distance` are post-intake controls
    supplied as query params (no longer captured in the intake itself). The
    default ordering (`balanced` + auto-derived distance) is cached on the
    session; other orderings are computed fresh per request.
    """
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Session has expired")
    if not is_flow_complete(session.answers or {}):
        raise HTTPException(status_code=400, detail="Chat session is not yet complete")

    flags = get_intake_flags(session.answers or {})
    derived_distance = bool(flags.get("user_postcode"))
    effective_include_distance = derived_distance if include_distance is None else include_distance

    is_default_view = scorecard_preference == DEFAULT_SCORECARD and include_distance is None

    if is_default_view and session.results_cache:
        results_data = session.results_cache.get("results", [])
        top_five = session.results_cache.get("top_five_contactable", [])
    else:
        payload = await search_firms(
            db,
            session.answers,
            scorecard_preference=scorecard_preference,
            include_distance=effective_include_distance,
        )
        results_data = payload["results"]
        top_five = payload["top_five_contactable"]
        if is_default_view:
            session.results_cache = {
                "results": results_data,
                "top_five_contactable": top_five,
                "cached_at": datetime.now(timezone.utc).isoformat(),
            }
            db.add(session)

    callbacks_locked = (
        await db.execute(
            select(Appointment.id)
            .where(
                Appointment.session_id == session_id,
                Appointment.type == AppointmentType.callback,
            )
            .limit(1)
        )
    ).first() is not None

    return SearchResponse(
        session_id=session_id,
        results=results_data,
        top_five_contactable=top_five,
        total=len(results_data),
        postcode=flags.get("user_postcode") or None,
        scorecard_preference=scorecard_preference,
        include_distance=effective_include_distance,
        intake_summary=build_intake_summary(session.answers or {}),
        callbacks_locked=callbacks_locked,
    )
