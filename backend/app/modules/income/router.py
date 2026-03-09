"""
FastAPI router for income CRUD endpoints with allocation-month support.
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.modules.income.schemas import (
    IncomeCreate,
    IncomeResponse,
    IncomeUpdate,
    MonthlyIncomeSummaryResponse,
)
from app.modules.income.service import IncomeService

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _service(db: DbSession) -> IncomeService:
    """Shorthand factory — keeps route signatures clean."""
    return IncomeService(db)


def _parse_month(month_str: str) -> date:
    """Parse a ``YYYY-MM`` string into a :class:`date` set to the 1st."""
    try:
        parts = month_str.split("-")
        return date(int(parts[0]), int(parts[1]), 1)
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="month must be in YYYY-MM format (e.g. 2026-04)",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=list[IncomeResponse],
    summary="List all income entries",
)
async def list_incomes(
    db: DbSession,
    current_user: CurrentUser,
) -> list[IncomeResponse]:
    """Return every income entry belonging to the authenticated user."""
    service = _service(db)
    records = await service.list_by_user(current_user.id)
    return [IncomeResponse.model_validate(r) for r in records]


@router.post(
    "/",
    response_model=IncomeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an income entry",
)
async def create_income(
    payload: IncomeCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> IncomeResponse:
    """Persist a new income entry with auto-computed allocation month."""
    service = _service(db)
    entry = await service.create(current_user.id, payload)
    return IncomeResponse.model_validate(entry)


@router.get(
    "/total",
    response_model=MonthlyIncomeSummaryResponse,
    summary="Get monthly income summary",
)
async def get_monthly_total(
    db: DbSession,
    current_user: CurrentUser,
    month: str | None = Query(
        None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="Month in YYYY-MM format (defaults to current month)",
    ),
) -> MonthlyIncomeSummaryResponse:
    """Return an aggregated income summary for the given month."""
    service = _service(db)
    target = _parse_month(month) if month else None
    summary = await service.get_income_summary(current_user.id, target)
    return MonthlyIncomeSummaryResponse(**summary)


@router.get(
    "/month/{month}",
    response_model=list[IncomeResponse],
    summary="List income entries for an allocation month",
)
async def list_income_by_month(
    month: str,
    db: DbSession,
    current_user: CurrentUser,
) -> list[IncomeResponse]:
    """Return all income entries allocated to the given month (YYYY-MM)."""
    target = _parse_month(month)
    service = _service(db)
    entries = await service.list_by_allocation_month(current_user.id, target)
    return [IncomeResponse.model_validate(e) for e in entries]


@router.get(
    "/{income_id}",
    response_model=IncomeResponse,
    summary="Get a single income entry",
)
async def get_income(
    income_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> IncomeResponse:
    """Retrieve one income entry by its ID (must belong to the caller)."""
    service = _service(db)
    entry = await service.get_by_id(income_id, current_user.id)
    return IncomeResponse.model_validate(entry)


@router.patch(
    "/{income_id}",
    response_model=IncomeResponse,
    summary="Update an income entry",
)
async def update_income(
    income_id: uuid.UUID,
    payload: IncomeUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> IncomeResponse:
    """Partially update an existing income entry."""
    service = _service(db)
    entry = await service.update(income_id, current_user.id, payload)
    return IncomeResponse.model_validate(entry)


@router.delete(
    "/{income_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an income entry",
)
async def delete_income(
    income_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Permanently remove an income entry."""
    service = _service(db)
    await service.delete(income_id, current_user.id)
