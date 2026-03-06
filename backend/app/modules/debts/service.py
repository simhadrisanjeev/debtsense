"""
Business-logic service layer for debt CRUD and aggregation.

All database access is performed through async SQLAlchemy sessions.
The service never commits or rolls back -- the caller (or the
``get_db`` dependency) owns the session lifecycle.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.debts.models import Debt
from app.modules.debts.schemas import DebtCreate, DebtSummary, DebtUpdate


class DebtService:
    """Encapsulates all debt-related data operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def list_debts(
        self,
        user_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
        active_only: bool = True,
    ) -> list[Debt]:
        """Return a paginated list of debts for a given user."""
        stmt = (
            select(Debt)
            .where(Debt.user_id == user_id)
            .order_by(Debt.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if active_only:
            stmt = stmt.where(Debt.is_active.is_(True))

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        debt_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Debt:
        """Fetch a single debt, scoped to the owning user.

        Raises ``NotFoundError`` when the record does not exist or
        belongs to a different user.
        """
        stmt = select(Debt).where(Debt.id == debt_id, Debt.user_id == user_id)
        result = await self._session.execute(stmt)
        debt = result.scalar_one_or_none()
        if debt is None:
            raise NotFoundError("Debt", str(debt_id))
        return debt

    async def get_summary(self, user_id: uuid.UUID) -> DebtSummary:
        """Compute aggregated statistics for all active debts.

        The weighted average rate is calculated as:
            sum(current_balance * interest_rate) / sum(current_balance)
        When there are no debts (or zero total balance) the rate is 0.
        """
        stmt = (
            select(
                func.coalesce(func.sum(Debt.current_balance), 0).label("total_balance"),
                func.coalesce(func.sum(Debt.minimum_payment), 0).label("total_minimum_payment"),
                func.count(Debt.id).label("debt_count"),
                func.coalesce(
                    func.sum(Debt.current_balance * Debt.interest_rate), 0
                ).label("weighted_numerator"),
            )
            .where(Debt.user_id == user_id, Debt.is_active.is_(True))
        )
        row = (await self._session.execute(stmt)).one()

        total_balance: Decimal = row.total_balance  # type: ignore[assignment]
        weighted_numerator: Decimal = row.weighted_numerator  # type: ignore[assignment]

        weighted_avg_rate = (
            (weighted_numerator / total_balance) if total_balance else Decimal("0")
        )

        return DebtSummary(
            total_balance=total_balance,
            total_minimum_payment=row.total_minimum_payment,  # type: ignore[arg-type]
            debt_count=row.debt_count,  # type: ignore[arg-type]
            weighted_avg_rate=weighted_avg_rate,
        )

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def create(
        self,
        user_id: uuid.UUID,
        payload: DebtCreate,
    ) -> Debt:
        """Persist a new debt record."""
        debt = Debt(
            user_id=user_id,
            **payload.model_dump(),
        )
        self._session.add(debt)
        await self._session.flush()  # populate server-side defaults (id, timestamps)
        return debt

    async def update(
        self,
        debt_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: DebtUpdate,
    ) -> Debt:
        """Apply a partial update to an existing debt.

        Only fields that are explicitly set by the client are written.
        """
        debt = await self.get_by_id(debt_id, user_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(debt, field, value)
        await self._session.flush()
        return debt

    async def delete(
        self,
        debt_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Debt:
        """Soft-delete a debt by setting ``is_active = False``."""
        debt = await self.get_by_id(debt_id, user_id)
        debt.is_active = False
        await self._session.flush()
        return debt
