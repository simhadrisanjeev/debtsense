"""
Business-logic service layer for debt CRUD, payment overrides,
and monthly payment schedule generation.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.modules.debts.models import Debt, DebtPaymentOverride
from app.modules.debts.schemas import (
    DebtCreate,
    DebtSummary,
    DebtUpdate,
    PaymentOverrideCreate,
    PaymentOverrideUpdate,
    MonthlyPaymentDetail,
    PaymentScheduleResponse,
)
from services.interest_calculator import calculate_monthly_interest


class DebtService:
    """Encapsulates all debt-related data operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Debt Queries
    # ------------------------------------------------------------------

    async def list_debts(
        self,
        user_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
        active_only: bool = True,
    ) -> list[Debt]:
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
        stmt = select(Debt).where(Debt.id == debt_id, Debt.user_id == user_id)
        result = await self._session.execute(stmt)
        debt = result.scalar_one_or_none()
        if debt is None:
            raise NotFoundError("Debt", str(debt_id))
        return debt

    async def get_summary(self, user_id: uuid.UUID) -> DebtSummary:
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
    # Debt Mutations
    # ------------------------------------------------------------------

    async def create(self, user_id: uuid.UUID, payload: DebtCreate) -> Debt:
        debt = Debt(user_id=user_id, **payload.model_dump())
        self._session.add(debt)
        await self._session.flush()
        return debt

    async def update(
        self, debt_id: uuid.UUID, user_id: uuid.UUID, payload: DebtUpdate,
    ) -> Debt:
        debt = await self.get_by_id(debt_id, user_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(debt, field, value)
        await self._session.flush()
        return debt

    async def delete(self, debt_id: uuid.UUID, user_id: uuid.UUID) -> Debt:
        debt = await self.get_by_id(debt_id, user_id)
        debt.is_active = False
        await self._session.flush()
        return debt

    # ------------------------------------------------------------------
    # Payment Overrides
    # ------------------------------------------------------------------

    async def list_overrides(
        self, debt_id: uuid.UUID, user_id: uuid.UUID,
    ) -> list[DebtPaymentOverride]:
        await self.get_by_id(debt_id, user_id)
        stmt = (
            select(DebtPaymentOverride)
            .where(
                DebtPaymentOverride.debt_id == debt_id,
                DebtPaymentOverride.user_id == user_id,
            )
            .order_by(DebtPaymentOverride.month_year.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_override(
        self,
        debt_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: PaymentOverrideCreate,
    ) -> DebtPaymentOverride:
        await self.get_by_id(debt_id, user_id)

        existing = await self._session.execute(
            select(DebtPaymentOverride).where(
                DebtPaymentOverride.debt_id == debt_id,
                DebtPaymentOverride.month_year == payload.month_year,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError(
                f"Override for {payload.month_year} already exists for this debt"
            )

        override = DebtPaymentOverride(
            debt_id=debt_id,
            user_id=user_id,
            **payload.model_dump(),
        )
        self._session.add(override)
        await self._session.flush()
        return override

    async def update_override(
        self,
        override_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: PaymentOverrideUpdate,
    ) -> DebtPaymentOverride:
        stmt = select(DebtPaymentOverride).where(
            DebtPaymentOverride.id == override_id,
            DebtPaymentOverride.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        override = result.scalar_one_or_none()
        if override is None:
            raise NotFoundError("PaymentOverride", str(override_id))

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(override, field, value)
        await self._session.flush()
        return override

    async def delete_override(
        self, override_id: uuid.UUID, user_id: uuid.UUID,
    ) -> None:
        stmt = select(DebtPaymentOverride).where(
            DebtPaymentOverride.id == override_id,
            DebtPaymentOverride.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        override = result.scalar_one_or_none()
        if override is None:
            raise NotFoundError("PaymentOverride", str(override_id))

        await self._session.delete(override)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Monthly Payment Resolution
    # ------------------------------------------------------------------

    async def get_monthly_payment_for_debt(
        self, debt_id: uuid.UUID, user_id: uuid.UUID, month_year: str,
    ) -> Decimal:
        """Return the effective payment for a debt in a given month.

        1. Check debt_payment_overrides for a custom value.
        2. Fall back to the debt's minimum_payment.
        """
        debt = await self.get_by_id(debt_id, user_id)

        stmt = select(DebtPaymentOverride.custom_payment_amount).where(
            DebtPaymentOverride.debt_id == debt_id,
            DebtPaymentOverride.month_year == month_year,
        )
        result = await self._session.execute(stmt)
        custom = result.scalar_one_or_none()

        if custom is not None:
            return Decimal(str(custom))
        return Decimal(str(debt.minimum_payment))

    # ------------------------------------------------------------------
    # Payment Schedule Generation
    # ------------------------------------------------------------------

    async def generate_payment_schedule(
        self, debt_id: uuid.UUID, user_id: uuid.UUID, months: int = 60,
    ) -> PaymentScheduleResponse:
        """Project a month-by-month payment schedule for a debt.

        Uses overrides where available, else minimum_payment.
        Cap at *months* iterations or until balance reaches zero.
        """
        debt = await self.get_by_id(debt_id, user_id)
        overrides = await self.list_overrides(debt_id, user_id)
        override_map: dict[str, Decimal] = {
            o.month_year: Decimal(str(o.custom_payment_amount))
            for o in overrides
        }

        balance = Decimal(str(debt.current_balance))
        min_payment = Decimal(str(debt.minimum_payment))
        rate = Decimal(str(debt.interest_rate))
        interest_type = debt.interest_type
        principal_for_flat = Decimal(str(debt.principal_amount))

        schedule: list[MonthlyPaymentDetail] = []
        total_interest = Decimal("0")
        total_paid = Decimal("0")

        today = date.today()
        year, month_num = today.year, today.month

        for _ in range(months):
            if balance <= 0:
                break

            month_key = f"{year:04d}-{month_num:02d}"
            interest = calculate_monthly_interest(
                balance, rate, interest_type, principal_for_flat,
            )

            payment = override_map.get(month_key, min_payment)
            effective_payment = min(payment, balance + interest)
            principal_paid = effective_payment - interest
            if principal_paid < 0:
                principal_paid = Decimal("0")

            balance = balance - principal_paid
            if balance < 0:
                balance = Decimal("0")

            schedule.append(MonthlyPaymentDetail(
                month=month_key,
                interest=interest,
                payment=effective_payment,
                principal_paid=principal_paid,
                remaining_balance=balance,
            ))

            total_interest += interest
            total_paid += effective_payment

            month_num += 1
            if month_num > 12:
                month_num = 1
                year += 1

        return PaymentScheduleResponse(
            debt_id=debt.id,
            schedule=schedule,
            total_interest=total_interest,
            total_paid=total_paid,
            payoff_months=len(schedule),
        )
