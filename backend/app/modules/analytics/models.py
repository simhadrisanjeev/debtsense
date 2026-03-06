"""
SQLAlchemy models for user analytics events and monthly financial snapshots.
"""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, TimestampMixin


class AnalyticsEvent(TimestampMixin, Base):
    """A single analytics event recorded for a user action."""

    __tablename__ = "analytics_events"

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
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="debt_paid_off | payment_made | strategy_changed | simulation_run | advice_requested",
    )
    payload: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Arbitrary JSON metadata for the event",
    )

    __table_args__ = (
        Index("ix_analytics_events_user_type", "user_id", "event_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<AnalyticsEvent(id={self.id!r}, user_id={self.user_id!r}, "
            f"event_type={self.event_type!r})>"
        )


class MonthlySnapshot(TimestampMixin, Base):
    """Point-in-time monthly financial snapshot for a user."""

    __tablename__ = "monthly_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    snapshot_month: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="First day of the snapshot month (e.g. 2025-03-01)",
    )
    total_debt: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )
    total_income: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )
    total_expenses: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )
    debt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    __table_args__ = (
        Index("ix_monthly_snapshots_user_month", "user_id", "snapshot_month", unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<MonthlySnapshot(id={self.id!r}, user_id={self.user_id!r}, "
            f"month={self.snapshot_month!r})>"
        )
