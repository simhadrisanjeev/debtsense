"""
Business-logic layer for income CRUD and aggregation.
"""

import uuid
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.income.models import Income
from app.modules.income.schemas import IncomeCreate, IncomeUpdate

# Multipliers to normalise any frequency to a monthly equivalent.
_MONTHLY_MULTIPLIER: dict[str, Decimal] = {
    "weekly": Decimal("4.333"),       # 52 / 12
    "biweekly": Decimal("2.167"),     # 26 / 12
    "monthly": Decimal("1"),
    "annually": Decimal("0.08333"),   # 1 / 12
}


class IncomeService:
    """Encapsulates all income-related database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def list_by_user(self, user_id: uuid.UUID) -> list[Income]:
        """Return all income records for a given user."""
        stmt = (
            select(Income)
            .where(Income.user_id == user_id)
            .order_by(Income.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, income_id: uuid.UUID, user_id: uuid.UUID) -> Income:
        """Fetch a single income record, scoped to the owning user."""
        stmt = select(Income).where(
            Income.id == income_id,
            Income.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        income = result.scalar_one_or_none()
        if income is None:
            raise NotFoundError("Income", str(income_id))
        return income

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def create(self, user_id: uuid.UUID, payload: IncomeCreate) -> Income:
        """Persist a new income record."""
        income = Income(
            user_id=user_id,
            source=payload.source.value,
            amount=payload.amount,
            frequency=payload.frequency.value,
            is_active=payload.is_active,
        )
        self._session.add(income)
        await self._session.flush()
        await self._session.refresh(income)
        return income

    async def update(
        self,
        income_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: IncomeUpdate,
    ) -> Income:
        """Apply a partial update to an existing income record."""
        income = await self.get_by_id(income_id, user_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            # Enum values need to be stored as their raw string.
            if hasattr(value, "value"):
                value = value.value
            setattr(income, field, value)

        await self._session.flush()
        await self._session.refresh(income)
        return income

    async def delete(self, income_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Hard-delete an income record."""
        income = await self.get_by_id(income_id, user_id)
        await self._session.delete(income)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    async def calculate_monthly_total(self, user_id: uuid.UUID) -> tuple[Decimal, int]:
        """
        Compute the normalised monthly income total across all *active*
        sources for a user.

        Returns:
            A tuple of (monthly_total, active_source_count).
        """
        stmt = select(Income).where(
            Income.user_id == user_id,
            Income.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        active_incomes = list(result.scalars().all())

        monthly_total = Decimal("0.00")
        for income in active_incomes:
            multiplier = _MONTHLY_MULTIPLIER.get(income.frequency, Decimal("1"))
            monthly_total += income.amount * multiplier

        # Round to two decimal places for currency precision.
        monthly_total = monthly_total.quantize(Decimal("0.01"))

        return monthly_total, len(active_incomes)
