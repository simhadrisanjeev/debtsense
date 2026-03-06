"""
FastAPI router for analytics events, dashboard stats, and monthly snapshots.
"""

import uuid
from datetime import date

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.modules.analytics.schemas import (
    DashboardStats,
    EventCreate,
    EventResponse,
    SnapshotResponse,
)
from app.modules.analytics.service import AnalyticsService

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _service(db: DbSession) -> AnalyticsService:
    """Shorthand factory -- keeps route signatures clean."""
    return AnalyticsService(db)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log an analytics event",
)
async def log_event(
    payload: EventCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> EventResponse:
    """Record a new analytics event for the authenticated user."""
    service = _service(db)
    event = await service.track_event(current_user.id, payload)
    return EventResponse.model_validate(event)


@router.get(
    "/dashboard",
    response_model=DashboardStats,
    summary="Get dashboard statistics",
)
async def get_dashboard(
    db: DbSession,
    current_user: CurrentUser,
) -> DashboardStats:
    """Return aggregated financial dashboard statistics for the user."""
    service = _service(db)
    return await service.get_dashboard_stats(current_user.id)


@router.get(
    "/snapshots",
    response_model=list[SnapshotResponse],
    summary="List monthly snapshots",
)
async def list_snapshots(
    db: DbSession,
    current_user: CurrentUser,
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(24, ge=1, le=120, description="Max records to return"),
) -> list[SnapshotResponse]:
    """Return a paginated list of monthly financial snapshots."""
    service = _service(db)
    snapshots = await service.get_snapshots(
        current_user.id,
        offset=offset,
        limit=limit,
    )
    return [SnapshotResponse.model_validate(s) for s in snapshots]


@router.get(
    "/events",
    response_model=list[EventResponse],
    summary="List recent events",
)
async def list_events(
    db: DbSession,
    current_user: CurrentUser,
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
) -> list[EventResponse]:
    """Return a paginated list of analytics events for the user."""
    service = _service(db)
    events = await service.list_events(
        current_user.id,
        offset=offset,
        limit=limit,
    )
    return [EventResponse.model_validate(e) for e in events]
