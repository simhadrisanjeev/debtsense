"""
SQLAlchemy model for user income entries with allocation-month support.

Supports real-world salary timing: income received on March 31 can be
allocated to April's budget via the allocation_month field.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, TimestampMixin


def calculate_allocation_month(date_received: date, allocation_type: str) -> date:
    """Determine which month's budget an income entry is allocated to.

    Args:
        date_received: The actual date the income was received.
        allocation_type: ``"same_month"`` or ``"next_month"``.

    Returns:
        A :class:`date` set to the 1st of the target month.
    """
    if allocation_type == "next_month":
        if date_received.month == 12:
            return date(date_received.year + 1, 1, 1)
        return date(date_received.year, date_received.month + 1, 1)
    return date(date_received.year, date_received.month, 1)


class IncomeEntry(TimestampMixin, Base):
    """Represents a single income entry with allocation-month tracking."""

    __tablename__ = "income_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    income_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="salary|freelance|business|bonus|gift|investment|other",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Income amount in the source currency",
    )
    date_received: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Actual date the income was received",
    )
    allocation_month: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="First day of the month this income is allocated to",
    )
    is_recurring: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )
    recurring_day: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Day of month for recurring income (1-31)",
    )
    income_allocation_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="same_month",
        comment="same_month|next_month",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    __table_args__ = (
        Index("ix_income_entries_user_id", "user_id"),
        Index("ix_income_entries_user_allocation", "user_id", "allocation_month"),
    )

    def __repr__(self) -> str:
        return (
            f"<IncomeEntry id={self.id!s} type={self.income_type!r} "
            f"amount={self.amount} alloc={self.allocation_month}>"
        )
