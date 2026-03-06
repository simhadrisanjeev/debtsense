"""
SQLAlchemy model for user income sources.
"""

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, TimestampMixin


class Income(TimestampMixin, Base):
    """Represents a recurring or one-time income source for a user."""

    __tablename__ = "income"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Income source category",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Income amount in the source currency",
    )
    frequency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Payment frequency",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    __table_args__ = (
        Index("ix_income_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Income id={self.id!s} source={self.source!r} "
            f"amount={self.amount} frequency={self.frequency!r}>"
        )
