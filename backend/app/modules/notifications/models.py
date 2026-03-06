"""
SQLAlchemy model for user notifications (in-app, email, push).
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, TimestampMixin


class Notification(TimestampMixin, Base):
    """A notification sent to a user via one or more channels."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="payment_due | debt_paid_off | milestone | tip | system",
    )
    channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="in_app",
        comment="in_app | email | push",
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "is_read"),
        Index("ix_notifications_user_type", "user_id", "notification_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<Notification(id={self.id!r}, user_id={self.user_id!r}, "
            f"type={self.notification_type!r}, is_read={self.is_read!r})>"
        )
