"""Public, unauthenticated endpoint that mirrors every Meta Pixel event the
frontend fires so the founder retains a Meta-independent funnel record.
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.limiter import limiter
from app.models.analytics_event import AnalyticsEvent
from app.schemas.analytics import AnalyticsEventCreate

router = APIRouter(prefix="/events", tags=["analytics"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("120/minute")
async def record_event(
    request: Request,
    body: AnalyticsEventCreate,
    db: AsyncSession = Depends(get_db),
):
    event = AnalyticsEvent(
        session_id=body.session_id,
        event_type=body.event_type,
        metadata_=body.metadata or {},
    )
    db.add(event)
    await db.flush()
    return {"id": str(event.id)}
