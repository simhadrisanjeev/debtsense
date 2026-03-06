"""
FastAPI router for expense endpoints.

All routes are scoped to the authenticated user.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DbSession
from app.modules.expenses.schemas import (
    ExpenseCreate,
    ExpenseResponse,
    ExpenseSummary,
    ExpenseUpdate,
)
from app.modules.expenses.service import ExpenseService

router = APIRouter()


# ---------------------------------------------------------------------------
# Placeholder auth dependency — replace with real implementation once the
# auth module exposes ``get_current_user``.
# ---------------------------------------------------------------------------

async def _get_current_user_id() -> uuid.UUID:
    """
    Temporary stub that returns a hard-coded user id.

    TODO: Replace with a proper dependency that extracts the user id from
    the JWT bearer token (e.g. ``app.modules.auth.dependencies.get_current_user``).
    """
    return uuid.UUID("00000000-0000-0000-0000-000000000000")


CurrentUserId = Annotated[uuid.UUID, Depends(_get_current_user_id)]


# ---------------------------------------------------------------------------
# Helper to build a service instance from the request session.
# ---------------------------------------------------------------------------

def _service(session: AsyncSession) -> ExpenseService:
    return ExpenseService(session)


# ---------------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new expense",
)
async def create_expense(
    payload: ExpenseCreate,
    user_id: CurrentUserId,
    session: DbSession,
) -> ExpenseResponse:
    """Create a new expense record for the authenticated user."""
    expense = await _service(session).create(user_id, payload)
    return ExpenseResponse.model_validate(expense)


@router.get(
    "",
    response_model=list[ExpenseResponse],
    summary="List expenses",
)
async def list_expenses(
    user_id: CurrentUserId,
    session: DbSession,
    active_only: bool = Query(True, description="Return only active expenses"),
) -> list[ExpenseResponse]:
    """Return all expenses for the authenticated user."""
    expenses = await _service(session).list_by_user(user_id, active_only=active_only)
    return [ExpenseResponse.model_validate(e) for e in expenses]


@router.get(
    "/summary",
    response_model=ExpenseSummary,
    summary="Spending breakdown by category",
)
async def get_expense_summary(
    user_id: CurrentUserId,
    session: DbSession,
) -> ExpenseSummary:
    """Return an aggregated spending summary grouped by category."""
    return await _service(session).get_breakdown_by_category(user_id)


@router.get(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Get a single expense",
)
async def get_expense(
    expense_id: uuid.UUID,
    user_id: CurrentUserId,
    session: DbSession,
) -> ExpenseResponse:
    """Retrieve a specific expense by id."""
    expense = await _service(session).get_by_id(user_id, expense_id)
    return ExpenseResponse.model_validate(expense)


@router.patch(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Update an expense",
)
async def update_expense(
    expense_id: uuid.UUID,
    payload: ExpenseUpdate,
    user_id: CurrentUserId,
    session: DbSession,
) -> ExpenseResponse:
    """Partially update an existing expense."""
    expense = await _service(session).update(user_id, expense_id, payload)
    return ExpenseResponse.model_validate(expense)


@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an expense",
)
async def delete_expense(
    expense_id: uuid.UUID,
    user_id: CurrentUserId,
    session: DbSession,
) -> None:
    """Permanently remove an expense record."""
    await _service(session).delete(user_id, expense_id)
