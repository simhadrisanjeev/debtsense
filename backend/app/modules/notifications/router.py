"""
FastAPI router for notification listing, read-status, and deletion.
"""

import uuid

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.modules.notifications.schemas import (
    MarkReadRequest,
    NotificationListResponse,
    NotificationResponse,
)
from app.modules.notifications.service import NotificationService

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _service(db: DbSession) -> NotificationService:
    """Shorthand factory -- keeps route signatures clean."""
    return NotificationService(db)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="List notifications",
)
async def list_notifications(
    db: DbSession,
    current_user: CurrentUser,
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
    is_read: bool | None = Query(None, description="Filter by read status"),
) -> NotificationListResponse:
    """Return a paginated list of notifications with unread count."""
    service = _service(db)
    notifications = await service.list_for_user(
        current_user.id,
        offset=offset,
        limit=limit,
        is_read=is_read,
    )
    unread_count = await service.get_unread_count(current_user.id)
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        unread_count=unread_count,
    )


@router.get(
    "/unread-count",
    response_model=dict,
    summary="Get unread notification count",
)
async def get_unread_count(
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Return the total number of unread notifications."""
    service = _service(db)
    count = await service.get_unread_count(current_user.id)
    return {"unread_count": count}


@router.patch(
    "/mark-read",
    response_model=dict,
    summary="Mark notifications as read",
)
async def mark_read(
    payload: MarkReadRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Mark a batch of notifications as read."""
    service = _service(db)
    updated = await service.mark_as_read(current_user.id, payload.notification_ids)
    return {"updated_count": updated}


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a notification",
)
async def delete_notification(
    notification_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Hard-delete a notification belonging to the authenticated user."""
    service = _service(db)
    await service.delete(notification_id, current_user.id)
