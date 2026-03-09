"""
Pydantic v2 request / response schemas for the auth module.
"""

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """Credentials for email + password authentication."""

    model_config = ConfigDict(strict=True)

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    """Payload for new user registration."""

    model_config = ConfigDict(strict=True)

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)


class TokenUser(BaseModel):
    """Minimal user info included in token responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str


class TokenResponse(BaseModel):
    """JWT token pair returned after successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: TokenUser | None = None


class RefreshRequest(BaseModel):
    """Payload for refreshing an access token."""

    refresh_token: str
