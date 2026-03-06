"""
Business-logic service layer for notification CRUD and batch operations.

All database access is performed through async SQLAlchemy sessions.
The service never commits or rolls back -- the caller (or the
``get_db`` dependency) owns the session lifecycle.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import NotificationCreate


class NotificationService:
    """Encapsulates all notification-related data operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
        is_read: bool | None = None,
    ) -> list[Notification]:
        """Return a paginated, optionally filtered list of notifications."""
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if is_read is not None:
            stmt = stmt.where(Notification.is_read == is_read)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        """Return the total number of unread notifications for the user."""
        stmt = (
            select(func.count(Notification.id))
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def create_notification(
        self,
        user_id: uuid.UUID,
        payload: NotificationCreate,
    ) -> Notification:
        """Persist a new notification for the user."""
        notification = Notification(
            user_id=user_id,
            title=payload.title,
            body=payload.body,
            notification_type=payload.notification_type.value,
            channel=payload.channel.value,
        )
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def mark_as_read(
        self,
        user_id: uuid.UUID,
        notification_ids: list[uuid.UUID],
    ) -> int:
        """Mark a batch of notifications as read.

        Returns the number of rows updated. Only notifications belonging
        to the specified user are affected.
        """
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.id.in_(notification_ids),
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount  # type: ignore[return-value]

    async def delete(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Hard-delete a notification.

        Raises ``NotFoundError`` when the record does not exist or
        belongs to a different user.
        """
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        notification = result.scalar_one_or_none()
        if notification is None:
            raise NotFoundError("Notification", str(notification_id))

        await self._session.delete(notification)
        await self._session.flush()
