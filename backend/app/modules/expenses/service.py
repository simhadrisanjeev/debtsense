"""
Business-logic layer for expense operations.

All database interaction is isolated here so routers stay thin.
"""

import uuid
from decimal import Decimal

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.expenses.models import Expense, ExpenseFrequency
from app.modules.expenses.schemas import (
    CategoryBreakdown,
    ExpenseCreate,
    ExpenseSummary,
    ExpenseUpdate,
)

# Multipliers to normalise any frequency to a monthly amount.
_MONTHLY_MULTIPLIERS: dict[str, Decimal] = {
    ExpenseFrequency.ONE_TIME.value: Decimal("0"),       # one-time costs are excluded from recurring monthly
    ExpenseFrequency.WEEKLY.value: Decimal("4.333"),     # 52 weeks / 12 months
    ExpenseFrequency.BIWEEKLY.value: Decimal("2.167"),   # 26 periods / 12 months
    ExpenseFrequency.MONTHLY.value: Decimal("1"),
    ExpenseFrequency.ANNUALLY.value: Decimal("0.0833"),  # 1 / 12
}


class ExpenseService:
    """Encapsulates CRUD operations and analytics for expenses."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create(self, user_id: uuid.UUID, payload: ExpenseCreate) -> Expense:
        """Persist a new expense and return the created row."""
        expense = Expense(
            user_id=user_id,
            category=payload.category.value,
            description=payload.description,
            amount=payload.amount,
            frequency=payload.frequency.value,
            is_recurring=payload.is_recurring,
        )
        self._session.add(expense)
        await self._session.flush()
        await self._session.refresh(expense)
        return expense

    async def get_by_id(self, user_id: uuid.UUID, expense_id: uuid.UUID) -> Expense:
        """Fetch a single expense, scoped to the requesting user."""
        stmt = select(Expense).where(
            Expense.id == expense_id,
            Expense.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        expense = result.scalar_one_or_none()
        if expense is None:
            raise NotFoundError("Expense", str(expense_id))
        return expense

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> list[Expense]:
        """Return all expenses for a user, optionally filtering by active status."""
        stmt = select(Expense).where(Expense.user_id == user_id)
        if active_only:
            stmt = stmt.where(Expense.is_active.is_(True))
        stmt = stmt.order_by(Expense.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        user_id: uuid.UUID,
        expense_id: uuid.UUID,
        payload: ExpenseUpdate,
    ) -> Expense:
        """Apply a partial update to an existing expense."""
        expense = await self.get_by_id(user_id, expense_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            # Convert enums to their string values for the ORM column.
            if hasattr(value, "value"):
                value = value.value
            setattr(expense, field, value)
        await self._session.flush()
        await self._session.refresh(expense)
        return expense

    async def delete(self, user_id: uuid.UUID, expense_id: uuid.UUID) -> None:
        """Hard-delete an expense row."""
        expense = await self.get_by_id(user_id, expense_id)
        await self._session.delete(expense)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Analytics helpers
    # ------------------------------------------------------------------

    async def calculate_monthly_total(self, user_id: uuid.UUID) -> Decimal:
        """
        Return the estimated total monthly spend for the user.

        Each expense amount is normalised to a monthly equivalent using its
        frequency multiplier.  Only active, recurring expenses are counted.
        """
        expenses = await self.list_by_user(user_id, active_only=True)
        total = Decimal("0")
        for exp in expenses:
            if not exp.is_recurring:
                continue
            multiplier = _MONTHLY_MULTIPLIERS.get(exp.frequency, Decimal("1"))
            total += Decimal(str(exp.amount)) * multiplier
        return total.quantize(Decimal("0.01"))

    async def get_breakdown_by_category(self, user_id: uuid.UUID) -> ExpenseSummary:
        """
        Build a per-category spending summary for the user.

        Returns an ``ExpenseSummary`` containing the total monthly estimate
        and a list of ``CategoryBreakdown`` items.
        """
        stmt = (
            select(
                Expense.category,
                func.sum(Expense.amount).label("total"),
                func.count(Expense.id).label("count"),
            )
            .where(
                Expense.user_id == user_id,
                Expense.is_active.is_(True),
            )
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount).desc())
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        breakdown = [
            CategoryBreakdown(
                category=row.category,
                total=Decimal(str(row.total)),
                count=row.count,
            )
            for row in rows
        ]

        monthly_total = await self.calculate_monthly_total(user_id)

        return ExpenseSummary(
            user_id=user_id,
            total_monthly=monthly_total,
            breakdown=breakdown,
        )
