"""
FastAPI router for income CRUD endpoints.
"""

import uuid

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, DbSession
from app.modules.income.schemas import (
    IncomeCreate,
    IncomeResponse,
    IncomeUpdate,
    MonthlyTotalResponse,
)
from app.modules.income.service import IncomeService

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _service(db: DbSession) -> IncomeService:
    """Shorthand factory — keeps route signatures clean."""
    return IncomeService(db)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=list[IncomeResponse],
    summary="List all income sources",
)
async def list_incomes(
    db: DbSession,
    current_user: CurrentUser,
) -> list[IncomeResponse]:
    """Return every income record belonging to the authenticated user."""
    service = _service(db)
    records = await service.list_by_user(current_user.id)
    return [IncomeResponse.model_validate(r) for r in records]


@router.post(
    "/",
    response_model=IncomeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an income source",
)
async def create_income(
    payload: IncomeCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> IncomeResponse:
    """Persist a new income source for the authenticated user."""
    service = _service(db)
    income = await service.create(current_user.id, payload)
    return IncomeResponse.model_validate(income)


@router.get(
    "/total",
    response_model=MonthlyTotalResponse,
    summary="Get monthly income total",
)
async def get_monthly_total(
    db: DbSession,
    current_user: CurrentUser,
) -> MonthlyTotalResponse:
    """Compute the normalised monthly total across all active income sources."""
    service = _service(db)
    monthly_total, active_sources = await service.calculate_monthly_total(
        current_user.id,
    )
    return MonthlyTotalResponse(
        user_id=current_user.id,
        monthly_total=monthly_total,
        active_sources=active_sources,
    )


@router.get(
    "/{income_id}",
    response_model=IncomeResponse,
    summary="Get a single income source",
)
async def get_income(
    income_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> IncomeResponse:
    """Retrieve one income record by its ID (must belong to the caller)."""
    service = _service(db)
    income = await service.get_by_id(income_id, current_user.id)
    return IncomeResponse.model_validate(income)


@router.patch(
    "/{income_id}",
    response_model=IncomeResponse,
    summary="Update an income source",
)
async def update_income(
    income_id: uuid.UUID,
    payload: IncomeUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> IncomeResponse:
    """Partially update an existing income record."""
    service = _service(db)
    income = await service.update(income_id, current_user.id, payload)
    return IncomeResponse.model_validate(income)


@router.delete(
    "/{income_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an income source",
)
async def delete_income(
    income_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Permanently remove an income record."""
    service = _service(db)
    await service.delete(income_id, current_user.id)
