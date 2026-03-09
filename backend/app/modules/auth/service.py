"""
Business logic for authentication: login, registration, token refresh, logout.
"""

import uuid
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.modules.auth.models import RefreshToken
from app.modules.auth.schemas import TokenResponse, TokenUser

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _persist_refresh_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    token: str,
) -> RefreshToken:
    """Store a refresh token in the database."""
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    )
    record = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
    )
    db.add(record)
    await db.flush()
    return record


async def _issue_token_pair(
    db: AsyncSession,
    user_id: uuid.UUID,
    extra_claims: dict | None = None,
    user: object | None = None,
) -> TokenResponse:
    """Create an access + refresh token pair and persist the refresh token."""
    subject = str(user_id)
    access = create_access_token(subject, extra_claims=extra_claims)
    refresh = create_refresh_token(subject)
    await _persist_refresh_token(db, user_id, refresh)
    token_user = TokenUser.model_validate(user) if user is not None else None
    return TokenResponse(access_token=access, refresh_token=refresh, user=token_user)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class AuthService:
    """Static methods that encapsulate authentication workflows."""

    @staticmethod
    async def login(
        db: AsyncSession,
        email: str,
        password: str,
    ) -> TokenResponse:
        """Validate credentials and return a fresh token pair."""
        # Import here to avoid circular imports between modules
        from app.modules.users.models import User  # noqa: WPS433

        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None or not _verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        return await _issue_token_pair(db, user.id, user=user)

    @staticmethod
    async def register(
        db: AsyncSession,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> TokenResponse:
        """Create a new user account and return a token pair."""
        from app.modules.users.models import User  # noqa: WPS433

        # Check for duplicate email
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none() is not None:
            raise ConflictError(f"A user with email '{email}' already exists")

        user = User(
            email=email,
            hashed_password=_hash_password(password),
            first_name=first_name,
            last_name=last_name,
        )
        db.add(user)
        await db.flush()

        return await _issue_token_pair(db, user.id, user=user)

    @staticmethod
    async def refresh_token(
        db: AsyncSession,
        refresh_token: str,
    ) -> TokenResponse:
        """Rotate a refresh token: revoke the old one, issue a new pair."""
        # Decode and validate the JWT
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id = uuid.UUID(payload["sub"])

        # Look up the persisted token
        stmt = select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            RefreshToken.revoked.is_(False),
        )
        result = await db.execute(stmt)
        stored = result.scalar_one_or_none()

        if stored is None:
            raise AuthenticationError("Refresh token is invalid or has been revoked")

        if stored.expires_at < datetime.now(timezone.utc):
            raise AuthenticationError("Refresh token has expired")

        # Revoke the old token (rotation)
        stored.revoked = True
        await db.flush()

        return await _issue_token_pair(db, user_id)

    @staticmethod
    async def logout(
        db: AsyncSession,
        refresh_token: str,
    ) -> None:
        """Revoke a refresh token so it cannot be reused."""
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.token == refresh_token,
                RefreshToken.revoked.is_(False),
            )
            .values(revoked=True)
        )
        await db.execute(stmt)
