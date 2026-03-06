"""
Pydantic v2 schemas for the users module.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    """Public representation of a user returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    subscription_tier: str
    created_at: datetime


class UserUpdate(BaseModel):
    """Fields a user is allowed to change on their own profile."""

    first_name: str | None = Field(default=None, max_length=150)
    last_name: str | None = Field(default=None, max_length=150)


class UserProfileResponse(UserResponse):
    """Extended user profile with additional detail fields."""

    is_verified: bool
    updated_at: datetime
