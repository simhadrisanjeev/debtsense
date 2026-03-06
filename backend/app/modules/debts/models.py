"""
SQLAlchemy model for user debts.

Supports credit cards, student loans, mortgages, auto loans,
personal loans, medical debt, and other categories.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, TimestampMixin


class Debt(TimestampMixin, Base):
    """A single debt instrument belonging to a user."""

    __tablename__ = "debts"

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
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable label, e.g. 'Chase Visa'",
    )
    debt_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="credit_card | student_loan | mortgage | auto_loan | personal_loan | medical | other",
    )
    principal_balance: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Original principal balance",
    )
    current_balance: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Current outstanding balance",
    )
    interest_rate: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="APR as a decimal, e.g. 0.1999 for 19.99%",
    )
    minimum_payment: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Monthly minimum payment amount",
    )
    due_date: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Day of month the payment is due (1-31)",
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date the debt was originated or first tracked",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    __table_args__ = (
        Index("ix_debts_user_active", "user_id", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"<Debt(id={self.id!r}, user_id={self.user_id!r}, "
            f"name={self.name!r}, balance={self.current_balance!r})>"
        )
