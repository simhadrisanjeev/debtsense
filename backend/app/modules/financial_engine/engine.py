"""
Core debt payoff computation engine.

Implements month-by-month amortization simulations for multiple payoff
strategies (snowball, avalanche, hybrid, custom).  All arithmetic uses
``decimal.Decimal`` to guarantee the precision required for financial
calculations — no floating-point rounding surprises.

Terminology
-----------
- **APR**: Annual Percentage Rate expressed as a decimal (e.g. 0.1999).
- **Monthly rate**: ``APR / 12``.
- **Snowball**: Debts are targeted from *lowest balance* to highest.
- **Avalanche**: Debts are targeted from *highest interest rate* to lowest.
- **Hybrid**: Within bands of similar interest rates (< 2 pp difference),
  debts are sorted by balance ascending (snowball within rate tiers) so the
  user gets quick psychological wins without significant interest cost.
- **Custom**: Falls back to the input order supplied by the caller.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Sequence

from app.modules.financial_engine.schemas import (
    DebtInput,
    PayoffResult,
    PayoffScheduleEntry,
    PayoffStrategy,
    StrategyComparison,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_MONTHS_IN_YEAR = Decimal("12")
_TWO_PLACES = Decimal("0.01")
_ZERO = Decimal("0")
_MAX_MONTHS = 1200  # 100-year safety cap to prevent infinite loops

# Hybrid strategy: debts whose APR difference is within this band are
# treated as equivalent and sub-sorted by balance (snowball behaviour).
_HYBRID_RATE_BAND = Decimal("0.02")  # 2 percentage points


# ---------------------------------------------------------------------------
# Internal working data structure
# ---------------------------------------------------------------------------

@dataclass
class _DebtState:
    """Mutable snapshot of a single debt during the simulation."""

    name: str
    balance: Decimal
    interest_rate: Decimal
    minimum_payment: Decimal
    monthly_rate: Decimal = field(init=False)
    paid_off: bool = False

    def __post_init__(self) -> None:
        self.monthly_rate = (self.interest_rate / _MONTHS_IN_YEAR).quantize(
            Decimal("0.0000000001"),
            rounding=ROUND_HALF_UP,
        )

    @classmethod
    def from_input(cls, debt: DebtInput) -> _DebtState:
        return cls(
            name=debt.name,
            balance=debt.balance.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP),
            interest_rate=debt.interest_rate,
            minimum_payment=debt.minimum_payment.quantize(
                _TWO_PLACES, rounding=ROUND_HALF_UP,
            ),
        )


# ---------------------------------------------------------------------------
# Sorting helpers
# ---------------------------------------------------------------------------

def _snowball_key(d: _DebtState) -> tuple[Decimal, Decimal]:
    """Lowest balance first; break ties by highest rate."""
    return (d.balance, -d.interest_rate)


def _avalanche_key(d: _DebtState) -> tuple[Decimal, Decimal]:
    """Highest interest rate first; break ties by lowest balance."""
    return (-d.interest_rate, d.balance)


def _hybrid_key(d: _DebtState) -> tuple[Decimal, Decimal]:
    """Group by rate band (descending), then by balance (ascending).

    Debts whose APR rounds to the same band (floor at 2 pp increments)
    are sub-sorted by balance so small debts get knocked out first
    within each rate tier.
    """
    rate_tier = (d.interest_rate / _HYBRID_RATE_BAND).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP,
    ) * _HYBRID_RATE_BAND
    return (-rate_tier, d.balance)


_STRATEGY_SORT_KEYS = {
    PayoffStrategy.SNOWBALL: _snowball_key,
    PayoffStrategy.AVALANCHE: _avalanche_key,
    PayoffStrategy.HYBRID: _hybrid_key,
    # Custom: preserve caller-supplied order — no sorting.
}


# ---------------------------------------------------------------------------
# Date helper
# ---------------------------------------------------------------------------

def _add_months(start: date, months: int) -> date:
    """Return the date that is *months* calendar months after *start*.

    Clamps the day to the last valid day of the target month (e.g. Jan 31
    + 1 month -> Feb 28).
    """
    total_months = start.month - 1 + months
    target_year = start.year + total_months // 12
    target_month = total_months % 12 + 1
    max_day = calendar.monthrange(target_year, target_month)[1]
    target_day = min(start.day, max_day)
    return date(target_year, target_month, target_day)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class FinancialEngine:
    """Stateless engine that runs debt payoff simulations.

    Every public method accepts plain data and returns schema objects.
    The engine never touches a database or performs I/O — it is a pure
    computation layer.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate_payoff(
        self,
        debts: Sequence[DebtInput],
        strategy: PayoffStrategy,
        extra_payment: Decimal = _ZERO,
    ) -> PayoffResult:
        """Run a month-by-month amortization simulation for *strategy*.

        Parameters
        ----------
        debts:
            The debts to pay off.
        strategy:
            Which ordering strategy to apply.
        extra_payment:
            Additional money available each month on top of every
            debt's minimum payment, directed to the target debt.

        Returns
        -------
        PayoffResult
            Full schedule, totals, and projected debt-free date.
        """
        if not debts:
            return self._empty_result(strategy)

        # Build mutable working copies
        states = [_DebtState.from_input(d) for d in debts]

        # Sort according to strategy (custom = input order)
        sort_key = _STRATEGY_SORT_KEYS.get(strategy)
        if sort_key is not None:
            states.sort(key=sort_key)

        schedule: list[PayoffScheduleEntry] = []
        payoff_order: list[str] = []
        total_interest = _ZERO
        total_paid = _ZERO
        month = 0

        # Pool of freed-up minimum payments from debts already paid off.
        freed_payment = _ZERO

        while any(not d.paid_off for d in states) and month < _MAX_MONTHS:
            month += 1

            # The amount available to throw at the target debt this month.
            # It starts as the explicit extra_payment plus any freed mins.
            available_extra = extra_payment + freed_payment

            for debt in states:
                if debt.paid_off:
                    continue

                # 1. Accrue interest  --  interest = balance * monthly_rate
                month_interest = (
                    debt.balance * debt.monthly_rate
                ).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

                debt.balance += month_interest
                total_interest += month_interest

                # 2. Determine payment
                #    - Every debt gets at least its minimum payment.
                #    - The *first* non-paid-off debt in strategy order
                #      also receives the available extra.
                is_target = debt is self._current_target(states)
                base_payment = min(debt.minimum_payment, debt.balance)

                if is_target:
                    payment = min(
                        base_payment + available_extra,
                        debt.balance,
                    )
                    # Whatever extra we used is consumed.
                    used_extra = payment - base_payment
                    available_extra -= used_extra
                else:
                    payment = min(base_payment, debt.balance)

                payment = payment.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

                # 3. Apply payment
                principal_portion = payment - month_interest
                # Guard against negative principal when interest > payment
                if principal_portion < _ZERO:
                    principal_portion = _ZERO

                debt.balance -= payment
                # Clamp tiny negative remainders from rounding
                if debt.balance < _ZERO:
                    debt.balance = _ZERO

                debt.balance = debt.balance.quantize(
                    _TWO_PLACES, rounding=ROUND_HALF_UP,
                )
                total_paid += payment

                schedule.append(
                    PayoffScheduleEntry(
                        month=month,
                        debt_name=debt.name,
                        payment=payment,
                        principal=principal_portion.quantize(
                            _TWO_PLACES, rounding=ROUND_HALF_UP,
                        ),
                        interest=month_interest,
                        remaining_balance=debt.balance,
                    ),
                )

                # 4. Check if this debt is now paid off
                if debt.balance <= _ZERO:
                    debt.paid_off = True
                    payoff_order.append(debt.name)
                    # Free up this debt's minimum payment for future months
                    freed_payment += debt.minimum_payment

        # Compute the projected debt-free date
        today = date.today()
        debt_free = _add_months(today, month)
        debt_free_str = debt_free.strftime("%Y-%m")

        return PayoffResult(
            strategy=strategy.value,
            total_months=month,
            total_interest_paid=total_interest.quantize(
                _TWO_PLACES, rounding=ROUND_HALF_UP,
            ),
            total_paid=total_paid.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP),
            payoff_order=payoff_order,
            schedule=schedule,
            debt_free_date=debt_free_str,
        )

    def compare_strategies(
        self,
        debts: Sequence[DebtInput],
        extra_payment: Decimal = _ZERO,
    ) -> StrategyComparison:
        """Run every strategy and return a side-by-side comparison.

        The *recommended* strategy is the one that minimises total
        interest paid.  ``interest_savings_vs_minimum`` shows how much
        interest the recommended strategy saves compared to paying only
        minimum payments (no extra payment, avalanche order as baseline).
        """
        strategies_to_run = [
            PayoffStrategy.SNOWBALL,
            PayoffStrategy.AVALANCHE,
            PayoffStrategy.HYBRID,
        ]

        results: list[PayoffResult] = [
            self.calculate_payoff(debts, s, extra_payment)
            for s in strategies_to_run
        ]

        # Minimum-payments-only baseline for savings calculation
        baseline = self.calculate_payoff(debts, PayoffStrategy.AVALANCHE, _ZERO)

        # Find the strategy with the lowest total interest
        best = min(results, key=lambda r: r.total_interest_paid)

        savings = (
            baseline.total_interest_paid - best.total_interest_paid
        ).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

        return StrategyComparison(
            strategies=results,
            recommended=best.strategy,
            interest_savings_vs_minimum=savings,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _current_target(states: list[_DebtState]) -> _DebtState | None:
        """Return the first debt that has not been paid off yet."""
        for debt in states:
            if not debt.paid_off:
                return debt
        return None

    @staticmethod
    def _empty_result(strategy: PayoffStrategy) -> PayoffResult:
        """Shortcut result when there are no debts to process."""
        return PayoffResult(
            strategy=strategy.value,
            total_months=0,
            total_interest_paid=_ZERO,
            total_paid=_ZERO,
            payoff_order=[],
            schedule=[],
            debt_free_date=date.today().strftime("%Y-%m"),
        )
