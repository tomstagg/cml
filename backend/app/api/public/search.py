"""Public API: firm search and results."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.chat_session import ChatSession
from app.schemas.search import SearchResponse
from app.services.chat import get_complexity_flags, is_flow_complete
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
    else:
        results_data = await search_firms(db, session.answers)
        session.results_cache = {
            "results": results_data,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
        db.add(session)

    complexity = get_complexity_flags(session.answers)

    return SearchResponse(
        session_id=session_id,
        results=results_data,
        total=len(results_data),
        postcode=complexity.get("postcode"),
    )
