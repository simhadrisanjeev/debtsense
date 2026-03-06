"""
Reusable FastAPI dependencies.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.core.security import decode_token

if TYPE_CHECKING:
    from app.modules.users.models import User

# Annotated shortcut for database session injection
DbSession = Annotated[AsyncSession, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    """Extract and validate the current user from the JWT bearer token."""
    payload = decode_token(token)
    subject: str | None = payload.get("sub")
    if subject is None:
        raise AuthenticationError("Token payload missing subject")

    try:
        user_id = uuid.UUID(subject)
    except ValueError as exc:
        raise AuthenticationError("Invalid user identifier in token") from exc

    # Late import to avoid circular dependency with modules
    from app.modules.users.models import User as UserModel

    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise AuthenticationError("User account is deactivated")

    return user


# Annotated shortcut for current-user injection
CurrentUser = Annotated[Any, Depends(get_current_user)]
