"""
FastAPI router for authentication endpoints.
"""

from fastapi import APIRouter, status

from app.core.dependencies import DbSession
from app.modules.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate with email and password",
)
async def login(body: LoginRequest, db: DbSession) -> TokenResponse:
    """Exchange valid credentials for an access / refresh token pair."""
    return await AuthService.login(
        db=db,
        email=body.email,
        password=body.password,
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(body: RegisterRequest, db: DbSession) -> TokenResponse:
    """Create a new user and return an initial token pair."""
    return await AuthService.register(
        db=db,
        email=body.email,
        password=body.password,
        first_name=body.first_name,
        last_name=body.last_name,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh an access token",
)
async def refresh(body: RefreshRequest, db: DbSession) -> TokenResponse:
    """Exchange a valid refresh token for a new access / refresh token pair."""
    return await AuthService.refresh_token(
        db=db,
        refresh_token=body.refresh_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a refresh token",
)
async def logout(body: RefreshRequest, db: DbSession) -> None:
    """Revoke the supplied refresh token so it can no longer be used."""
    await AuthService.logout(
        db=db,
        refresh_token=body.refresh_token,
    )
