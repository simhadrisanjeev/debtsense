"""
Business-logic layer for income CRUD, allocation-month queries, and aggregation.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.income.models import IncomeEntry, calculate_allocation_month
from app.modules.income.schemas import IncomeCreate, IncomeUpdate


class IncomeService:
    """Encapsulates all income-related database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def list_by_user(self, user_id: uuid.UUID) -> list[IncomeEntry]:
        """Return all income entries for a given user."""
        stmt = (
            select(IncomeEntry)
            .where(IncomeEntry.user_id == user_id)
            .order_by(IncomeEntry.date_received.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(
        self, income_id: uuid.UUID, user_id: uuid.UUID,
    ) -> IncomeEntry:
        """Fetch a single income entry, scoped to the owning user."""
        stmt = select(IncomeEntry).where(
            IncomeEntry.id == income_id,
            IncomeEntry.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        entry = result.scalar_one_or_none()
        if entry is None:
            raise NotFoundError("IncomeEntry", str(income_id))
        return entry

    async def list_by_allocation_month(
        self, user_id: uuid.UUID, month: date,
    ) -> list[IncomeEntry]:
        """Return income entries allocated to a specific month.

        Includes:
        1. One-time entries whose ``allocation_month`` matches exactly.
        2. Active recurring entries (they apply to every month).
        """
        target = date(month.year, month.month, 1)

        stmt = (
            select(IncomeEntry)
            .where(
                IncomeEntry.user_id == user_id,
                IncomeEntry.is_active.is_(True),
                or_(
                    IncomeEntry.allocation_month == target,
                    IncomeEntry.is_recurring.is_(True),
                ),
            )
            .order_by(IncomeEntry.date_received.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def create(
        self, user_id: uuid.UUID, payload: IncomeCreate,
    ) -> IncomeEntry:
        """Persist a new income entry with computed allocation month."""
        alloc_month = calculate_allocation_month(
            payload.date_received,
            payload.income_allocation_type.value,
        )

        entry = IncomeEntry(
            user_id=user_id,
            income_type=payload.income_type.value,
            amount=payload.amount,
            date_received=payload.date_received,
            allocation_month=alloc_month,
            income_allocation_type=payload.income_allocation_type.value,
            is_recurring=payload.is_recurring,
            recurring_day=payload.recurring_day,
            note=payload.note,
            is_active=payload.is_active,
        )
        self._session.add(entry)
        await self._session.flush()
        await self._session.refresh(entry)
        return entry

    async def update(
        self,
        income_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: IncomeUpdate,
    ) -> IncomeEntry:
        """Apply a partial update to an existing income entry."""
        entry = await self.get_by_id(income_id, user_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(value, "value"):
                value = value.value
            setattr(entry, field, value)

        # Recompute allocation_month if either date or allocation type changed
        if "date_received" in update_data or "income_allocation_type" in update_data:
            entry.allocation_month = calculate_allocation_month(
                entry.date_received,
                entry.income_allocation_type,
            )

        await self._session.flush()
        await self._session.refresh(entry)
        return entry

    async def delete(self, income_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Hard-delete an income entry."""
        entry = await self.get_by_id(income_id, user_id)
        await self._session.delete(entry)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    async def calculate_monthly_total(
        self, user_id: uuid.UUID, month: date | None = None,
    ) -> tuple[Decimal, int]:
        """Compute total income allocated to a specific month.

        If *month* is ``None``, defaults to the current month.

        Returns:
            A tuple of ``(monthly_total, entry_count)``.
        """
        if month is None:
            today = date.today()
            month = date(today.year, today.month, 1)
        else:
            month = date(month.year, month.month, 1)

        entries = await self.list_by_allocation_month(user_id, month)

        total = sum((e.amount for e in entries), Decimal("0.00"))
        total = total.quantize(Decimal("0.01"))

        return total, len(entries)

    async def get_income_summary(
        self, user_id: uuid.UUID, month: date | None = None,
    ) -> dict:
        """Build a typed breakdown of income for a month."""
        if month is None:
            today = date.today()
            month = date(today.year, today.month, 1)
        else:
            month = date(month.year, month.month, 1)

        entries = await self.list_by_allocation_month(user_id, month)

        breakdown: dict[str, dict] = {}
        for entry in entries:
            key = entry.income_type
            if key not in breakdown:
                breakdown[key] = {"total": Decimal("0"), "count": 0}
            breakdown[key]["total"] += entry.amount
            breakdown[key]["count"] += 1

        total = sum((e.amount for e in entries), Decimal("0.00"))

        return {
            "user_id": user_id,
            "month": month,
            "monthly_total": total.quantize(Decimal("0.01")),
            "entry_count": len(entries),
            "breakdown": [
                {
                    "income_type": k,
                    "total": v["total"].quantize(Decimal("0.01")),
                    "count": v["count"],
                }
                for k, v in breakdown.items()
            ],
        }
