"""
FastAPI router for debt CRUD and summary endpoints.
"""

import uuid

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.modules.debts.schemas import (
    DebtCreate,
    DebtResponse,
    DebtSummary,
    DebtUpdate,
)
from app.modules.debts.service import DebtService

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _service(db: DbSession) -> DebtService:
    """Shorthand factory -- keeps route signatures clean."""
    return DebtService(db)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=list[DebtResponse],
    summary="List debts",
)
async def list_debts(
    db: DbSession,
    current_user: CurrentUser,
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
    active_only: bool = Query(True, description="Only return active debts"),
) -> list[DebtResponse]:
    """Return a paginated list of debts belonging to the authenticated user."""
    service = _service(db)
    debts = await service.list_debts(
        current_user.id,
        offset=offset,
        limit=limit,
        active_only=active_only,
    )
    return [DebtResponse.model_validate(d) for d in debts]


@router.post(
    "/",
    response_model=DebtResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a debt",
)
async def create_debt(
    payload: DebtCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> DebtResponse:
    """Persist a new debt record for the authenticated user."""
    service = _service(db)
    debt = await service.create(current_user.id, payload)
    return DebtResponse.model_validate(debt)


@router.get(
    "/summary",
    response_model=DebtSummary,
    summary="Get debt summary",
)
async def get_debt_summary(
    db: DbSession,
    current_user: CurrentUser,
) -> DebtSummary:
    """Return aggregated statistics across all active debts for the user."""
    service = _service(db)
    return await service.get_summary(current_user.id)


@router.get(
    "/{debt_id}",
    response_model=DebtResponse,
    summary="Get a single debt",
)
async def get_debt(
    debt_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> DebtResponse:
    """Retrieve one debt record by its ID (must belong to the caller)."""
    service = _service(db)
    debt = await service.get_by_id(debt_id, current_user.id)
    return DebtResponse.model_validate(debt)


@router.patch(
    "/{debt_id}",
    response_model=DebtResponse,
    summary="Update a debt",
)
async def update_debt(
    debt_id: uuid.UUID,
    payload: DebtUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> DebtResponse:
    """Partially update an existing debt record."""
    service = _service(db)
    debt = await service.update(debt_id, current_user.id, payload)
    return DebtResponse.model_validate(debt)


@router.delete(
    "/{debt_id}",
    response_model=DebtResponse,
    summary="Soft-delete a debt",
)
async def delete_debt(
    debt_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> DebtResponse:
    """Soft-delete a debt by marking it inactive.

    The record is not physically removed. The updated debt (with
    ``is_active=False``) is returned so the client can confirm the change.
    """
    service = _service(db)
    debt = await service.delete(debt_id, current_user.id)
    return DebtResponse.model_validate(debt)
