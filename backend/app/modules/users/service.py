"""
Business logic for user operations.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.users.models import User
from app.modules.users.schemas import UserUpdate


class UserService:
    """Stateless service layer for user CRUD operations."""

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
        """Fetch a single user by primary key or raise ``NotFoundError``."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise NotFoundError("User", str(user_id))
        return user

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        """Return the user matching *email*, or ``None`` if not found."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        user: User,
        payload: UserUpdate,
    ) -> User:
        """Apply partial updates from *payload* to *user* and flush changes."""
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def deactivate(db: AsyncSession, user: User) -> User:
        """Soft-delete a user by setting ``is_active`` to ``False``."""
        user.is_active = False
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
