"""
SQLAlchemy model for user expenses.
"""

import enum
import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, TimestampMixin


class ExpenseCategory(str, enum.Enum):
    """Allowed expense categories."""

    HOUSING = "housing"
    TRANSPORTATION = "transportation"
    FOOD = "food"
    UTILITIES = "utilities"
    INSURANCE = "insurance"
    HEALTHCARE = "healthcare"
    ENTERTAINMENT = "entertainment"
    SUBSCRIPTIONS = "subscriptions"
    OTHER = "other"


class ExpenseFrequency(str, enum.Enum):
    """Allowed recurrence frequencies."""

    ONE_TIME = "one_time"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    ANNUALLY = "annually"


class Expense(TimestampMixin, Base):
    """Represents a single expense record for a user."""

    __tablename__ = "expenses"
    __table_args__ = (
        Index("ix_expenses_user_id", "user_id"),
        Index("ix_expenses_user_category", "user_id", "category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    frequency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ExpenseFrequency.MONTHLY.value,
    )
    is_recurring: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Expense(id={self.id!r}, category={self.category!r}, "
            f"amount={self.amount!r}, frequency={self.frequency!r})>"
        )
