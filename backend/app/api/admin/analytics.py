"""Admin CSV export of analytics_events for offline funnel analysis."""

import csv
import io
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.analytics_event import AnalyticsEvent

router = APIRouter(prefix="/analytics", tags=["admin-analytics"])


def _parse_bound(label: str, value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        normalised = value.replace("Z", "+00:00") if "T" in value else value
        dt = datetime.fromisoformat(normalised)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {label} timestamp: {exc}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@router.get("/export")
async def export_events_csv(
    from_: str | None = Query(None, alias="from"),
    to: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Half-open ``[from, to)``. Bounds accept ``YYYY-MM-DD`` or ISO-8601;
    naive inputs are interpreted as UTC. Either bound may be omitted.
    """
    from_dt = _parse_bound("from", from_)
    to_dt = _parse_bound("to", to)

    stmt = select(AnalyticsEvent).order_by(AnalyticsEvent.created_at)
    if from_dt is not None:
        stmt = stmt.where(AnalyticsEvent.created_at >= from_dt)
    if to_dt is not None:
        stmt = stmt.where(AnalyticsEvent.created_at < to_dt)

    result = await db.execute(stmt)
    events = result.scalars().all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "created_at", "event_type", "session_id", "metadata"])
    for ev in events:
        writer.writerow(
            [
                str(ev.id),
                ev.created_at.isoformat(),
                ev.event_type,
                str(ev.session_id) if ev.session_id else "",
                json.dumps(ev.metadata_ or {}, sort_keys=True),
            ]
        )

    filename = f"analytics_events_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
