"""
SQLAlchemy models for the Debts module.

Supports Indian and international debt types including credit cards,
personal loans, gold loans, informal loans, money lender debts,
and flexible repayment structures.
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
    Text,
    Uuid,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import Base, TimestampMixin


class Debt(TimestampMixin, Base):
    """A single debt instrument belonging to a user."""

    __tablename__ = "debts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
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
        comment="credit_card | personal_loan | gold_loan | home_loan | auto_loan | education_loan | informal_loan | money_lender | business_loan | chit_fund | other",
    )
    lender_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Name of the lender, bank, or person",
    )
    principal_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Original principal / sanctioned amount",
    )
    current_balance: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Current outstanding balance",
    )
    interest_rate: Mapped[float] = mapped_column(
        Numeric(7, 4),
        nullable=False,
        comment="Annual interest rate as decimal, e.g. 0.1999 for 19.99%",
    )
    interest_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="reducing_balance",
        comment="reducing_balance | flat_interest | monthly_interest | no_interest",
    )
    repayment_style: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="emi",
        comment="emi | interest_only | bullet_payment | flexible",
    )
    payment_frequency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="monthly",
        comment="weekly | monthly | quarterly | yearly | custom",
    )
    minimum_payment: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Minimum payment amount per period",
    )
    due_day_of_month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Day of month the payment is due (1-31)",
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date the debt was originated or first tracked",
    )
    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Expected payoff date (optional)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Free-form notes about this debt",
    )

    # Relationships
    payment_overrides: Mapped[list["DebtPaymentOverride"]] = relationship(
        back_populates="debt",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_debts_user_active", "user_id", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"<Debt(id={self.id!r}, user_id={self.user_id!r}, "
            f"name={self.name!r}, balance={self.current_balance!r})>"
        )


class DebtPaymentOverride(TimestampMixin, Base):
    """Custom payment amount for a specific month on a given debt."""

    __tablename__ = "debt_payment_overrides"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        primary_key=True,
        default=uuid.uuid4,
    )
    debt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("debts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    month_year: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        comment="YYYY-MM format, e.g. 2026-03",
    )
    custom_payment_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Custom payment for this month",
    )
    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional note explaining the override",
    )

    # Relationships
    debt: Mapped["Debt"] = relationship(back_populates="payment_overrides")

    __table_args__ = (
        UniqueConstraint("debt_id", "month_year", name="uq_override_debt_month"),
        Index("ix_override_debt_month", "debt_id", "month_year"),
    )

    def __repr__(self) -> str:
        return (
            f"<DebtPaymentOverride(id={self.id!r}, debt_id={self.debt_id!r}, "
            f"month={self.month_year!r}, amount={self.custom_payment_amount!r})>"
        )
