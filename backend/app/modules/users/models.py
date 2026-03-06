"""
User SQLAlchemy model.
"""

import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, TimestampMixin


class User(TimestampMixin, Base):
    """Application user account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="",
    )
    last_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    subscription_tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="free",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
