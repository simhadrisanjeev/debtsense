"""
Business-logic service layer for analytics events, snapshots, and dashboard.

All database access is performed through async SQLAlchemy sessions.
The service never commits or rolls back -- the caller (or the
``get_db`` dependency) owns the session lifecycle.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import AnalyticsEvent, MonthlySnapshot
from app.modules.analytics.schemas import DashboardStats, EventCreate


class AnalyticsService:
    """Encapsulates all analytics-related data operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    async def track_event(
        self,
        user_id: uuid.UUID,
        payload: EventCreate,
    ) -> AnalyticsEvent:
        """Persist a new analytics event for the user."""
        event = AnalyticsEvent(
            user_id=user_id,
            event_type=payload.event_type.value,
            payload=payload.payload,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def list_events(
        self,
        user_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AnalyticsEvent]:
        """Return a paginated list of analytics events for the user."""
        stmt = (
            select(AnalyticsEvent)
            .where(AnalyticsEvent.user_id == user_id)
            .order_by(AnalyticsEvent.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    async def get_dashboard_stats(self, user_id: uuid.UUID) -> DashboardStats:
        """Compute aggregated dashboard statistics for the user.

        Pulls live data from the debts, income, and expenses tables to
        build a real-time snapshot of the user's financial position.
        """
        # Late imports to avoid circular dependencies with sibling modules
        from app.modules.debts.models import Debt
        from app.modules.expenses.models import Expense
        from app.modules.income.service import IncomeService

        # --- Debt aggregation ---
        debt_stmt = (
            select(
                func.coalesce(func.sum(Debt.current_balance), 0).label("total_debt"),
                func.coalesce(func.sum(Debt.principal_balance), 0).label("total_principal"),
                func.coalesce(func.sum(Debt.minimum_payment), 0).label("monthly_payment"),
                func.count(Debt.id).label("debt_count"),
            )
            .where(Debt.user_id == user_id, Debt.is_active.is_(True))
        )
        debt_row = (await self._session.execute(debt_stmt)).one()

        total_debt = Decimal(str(debt_row.total_debt))
        total_principal = Decimal(str(debt_row.total_principal))
        monthly_payment = Decimal(str(debt_row.monthly_payment))
        debt_count: int = debt_row.debt_count

        # --- Income aggregation (uses existing IncomeService) ---
        income_svc = IncomeService(self._session)
        total_income, _ = await income_svc.calculate_monthly_total(user_id)

        # --- Expense aggregation ---
        expense_stmt = (
            select(
                func.coalesce(func.sum(Expense.amount), 0).label("total_expenses"),
            )
            .where(Expense.user_id == user_id, Expense.is_active.is_(True))
        )
        expense_row = (await self._session.execute(expense_stmt)).one()
        total_expenses = Decimal(str(expense_row.total_expenses))

        # --- Derived metrics ---
        # Debt-free progress: how much of principal has been paid off
        if total_principal > 0:
            paid_off = total_principal - total_debt
            debt_free_progress_pct = (
                (paid_off / total_principal) * Decimal("100")
            ).quantize(Decimal("0.01"))
            debt_free_progress_pct = max(Decimal("0"), min(Decimal("100"), debt_free_progress_pct))
        else:
            debt_free_progress_pct = Decimal("100.00")

        # Estimated payoff date (simple linear projection)
        surplus = total_income - total_expenses
        effective_payment = max(monthly_payment, surplus) if surplus > 0 else monthly_payment
        if effective_payment > 0 and total_debt > 0:
            months_remaining = int(
                (total_debt / effective_payment).to_integral_value()
            ) + 1
            estimated_payoff_date = date.today() + timedelta(days=months_remaining * 30)
        else:
            estimated_payoff_date = None

        return DashboardStats(
            total_debt=total_debt,
            total_income=total_income,
            total_expenses=total_expenses,
            debt_count=debt_count,
            monthly_payment=monthly_payment,
            estimated_payoff_date=estimated_payoff_date,
            debt_free_progress_pct=debt_free_progress_pct,
        )

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------

    async def get_snapshots(
        self,
        user_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 24,
    ) -> list[MonthlySnapshot]:
        """Return a paginated list of monthly snapshots for the user."""
        stmt = (
            select(MonthlySnapshot)
            .where(MonthlySnapshot.user_id == user_id)
            .order_by(MonthlySnapshot.snapshot_month.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_monthly_snapshot(
        self,
        user_id: uuid.UUID,
        snapshot_month: date,
    ) -> MonthlySnapshot:
        """Create (or update) a monthly snapshot for the given month.

        Pulls current figures from the dashboard stats to persist a
        point-in-time record. If a snapshot already exists for the
        given month it is updated in place.
        """
        stats = await self.get_dashboard_stats(user_id)

        # Check for existing snapshot
        stmt = select(MonthlySnapshot).where(
            MonthlySnapshot.user_id == user_id,
            MonthlySnapshot.snapshot_month == snapshot_month,
        )
        result = await self._session.execute(stmt)
        snapshot = result.scalar_one_or_none()

        if snapshot is not None:
            snapshot.total_debt = float(stats.total_debt)
            snapshot.total_income = float(stats.total_income)
            snapshot.total_expenses = float(stats.total_expenses)
            snapshot.debt_count = stats.debt_count
        else:
            snapshot = MonthlySnapshot(
                user_id=user_id,
                snapshot_month=snapshot_month,
                total_debt=float(stats.total_debt),
                total_income=float(stats.total_income),
                total_expenses=float(stats.total_expenses),
                debt_count=stats.debt_count,
            )
            self._session.add(snapshot)

        await self._session.flush()
        return snapshot
