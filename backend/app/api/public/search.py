"""Public API: firm search and results."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.chat_session import ChatSession
from app.schemas.search import SearchResponse
from app.services.chat import get_intake_flags, is_flow_complete
from app.services.search import search_firms

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/{session_id}", response_model=SearchResponse)
async def get_results(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Get ranked firm results for a completed chat session.
    Results are cached on the session; cache is invalidated when answers change.
    """
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Session has expired")
    if not is_flow_complete(session.answers or {}):
        raise HTTPException(status_code=400, detail="Chat session is not yet complete")

    # Use cache if available
    if session.results_cache:
        results_data = session.results_cache.get("results", [])
        top_five = session.results_cache.get("top_five_contactable", [])
    else:
        payload = await search_firms(db, session.answers)
        results_data = payload["results"]
        top_five = payload["top_five_contactable"]
        session.results_cache = {
            "results": results_data,
            "top_five_contactable": top_five,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
        db.add(session)

    flags = get_intake_flags(session.answers or {})

    return SearchResponse(
        session_id=session_id,
        results=results_data,
        top_five_contactable=top_five,
        total=len(results_data),
        postcode=flags.get("property_postcode") or None,
        scorecard_preference=session.scorecard_preference.value
        if session.scorecard_preference
        else "balanced",
        include_distance=bool(session.include_distance),
    )
