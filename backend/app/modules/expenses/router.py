"""
FastAPI router for expense endpoints.

All routes are scoped to the authenticated user.
"""

import uuid

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.modules.expenses.schemas import (
    ExpenseCreate,
    ExpenseResponse,
    ExpenseSummary,
    ExpenseUpdate,
)
from app.modules.expenses.service import ExpenseService

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper to build a service instance from the request session.
# ---------------------------------------------------------------------------

def _service(db: DbSession) -> ExpenseService:
    return ExpenseService(db)


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
    current_user: CurrentUser,
    db: DbSession,
) -> ExpenseResponse:
    """Create a new expense record for the authenticated user."""
    expense = await _service(db).create(current_user.id, payload)
    return ExpenseResponse.model_validate(expense)


@router.get(
    "",
    response_model=list[ExpenseResponse],
    summary="List expenses",
)
async def list_expenses(
    current_user: CurrentUser,
    db: DbSession,
    active_only: bool = Query(True, description="Return only active expenses"),
) -> list[ExpenseResponse]:
    """Return all expenses for the authenticated user."""
    expenses = await _service(db).list_by_user(current_user.id, active_only=active_only)
    return [ExpenseResponse.model_validate(e) for e in expenses]


@router.get(
    "/summary",
    response_model=ExpenseSummary,
    summary="Spending breakdown by category",
)
async def get_expense_summary(
    current_user: CurrentUser,
    db: DbSession,
) -> ExpenseSummary:
    """Return an aggregated spending summary grouped by category."""
    return await _service(db).get_breakdown_by_category(current_user.id)


@router.get(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Get a single expense",
)
async def get_expense(
    expense_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ExpenseResponse:
    """Retrieve a specific expense by id."""
    expense = await _service(db).get_by_id(current_user.id, expense_id)
    return ExpenseResponse.model_validate(expense)


@router.patch(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Update an expense",
)
async def update_expense(
    expense_id: uuid.UUID,
    payload: ExpenseUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ExpenseResponse:
    """Partially update an existing expense."""
    expense = await _service(db).update(current_user.id, expense_id, payload)
    return ExpenseResponse.model_validate(expense)


@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an expense",
)
async def delete_expense(
    expense_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Permanently remove an expense record."""
    await _service(db).delete(current_user.id, expense_id)
