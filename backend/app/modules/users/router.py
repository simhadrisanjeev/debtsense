"""
Users API endpoints.
"""

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, DbSession
from app.modules.users.schemas import UserProfileResponse, UserUpdate
from app.modules.users.service import UserService

router = APIRouter()


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_current_user_profile(
    current_user: CurrentUser,
) -> UserProfileResponse:
    """Return the authenticated user's full profile."""
    return UserProfileResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
)
async def update_current_user_profile(
    payload: UserUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> UserProfileResponse:
    """Update first name and/or last name for the authenticated user."""
    updated = await UserService.update_profile(db, current_user, payload)
    return UserProfileResponse.model_validate(updated)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate current user account",
)
async def deactivate_current_user(
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Soft-delete the authenticated user's account by marking it inactive."""
    await UserService.deactivate(db, current_user)
