"""
Pydantic v2 schemas for the Notifications module.

Provides request/response validation for notification CRUD
and batch operations.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class NotificationType(str, Enum):
    """Allowed notification types."""

    PAYMENT_DUE = "payment_due"
    DEBT_PAID_OFF = "debt_paid_off"
    MILESTONE = "milestone"
    TIP = "tip"
    SYSTEM = "system"


class NotificationChannel(str, Enum):
    """Delivery channel for a notification."""

    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class NotificationCreate(BaseModel):
    """Payload for creating a new notification."""

    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    notification_type: NotificationType
    channel: NotificationChannel = NotificationChannel.IN_APP

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Payment Due Soon",
                "body": "Your Chase Visa payment of $105.00 is due in 3 days.",
                "notification_type": "payment_due",
                "channel": "in_app",
            }
        }
    )


class MarkReadRequest(BaseModel):
    """Payload for marking notifications as read in batch."""

    notification_ids: list[uuid.UUID] = Field(
        ...,
        min_length=1,
        description="List of notification IDs to mark as read",
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class NotificationResponse(BaseModel):
    """Full notification record returned to the client."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    body: str
    notification_type: NotificationType
    channel: NotificationChannel
    is_read: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """Paginated notification list with unread count."""

    items: list[NotificationResponse]
    unread_count: int = Field(
        ...,
        description="Total number of unread notifications for the user",
    )
