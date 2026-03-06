"""
Core simulation engine -- evaluates what-if scenarios against a debt baseline.

Each scenario type mutates a copy of the baseline inputs (debts and/or extra
payment), then runs ``FinancialEngine.calculate_payoff`` for both the original
and modified inputs to produce a before/after comparison.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from app.modules.financial_engine.engine import FinancialEngine
from app.modules.financial_engine.schemas import DebtInput, PayoffStrategy
from app.modules.simulation_engine.schemas import (
    ScenarioInput,
    ScenarioType,
    SimulationResult,
)

# Default strategy used for all simulation comparisons.
_DEFAULT_STRATEGY = PayoffStrategy.AVALANCHE

_ZERO = Decimal("0")
_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


class SimulationEngine:
    """Evaluates what-if scenarios by comparing modified inputs to a baseline."""

    def __init__(self) -> None:
        self._financial = FinancialEngine()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _baseline(
        self,
        debts: list[DebtInput],
        extra_payment: Decimal,
    ) -> tuple[int, Decimal]:
        """Return (months, total_interest) for the unmodified baseline."""
        result = self._financial.calculate_payoff(
            debts, _DEFAULT_STRATEGY, extra_payment,
        )
        return result.total_months, result.total_interest_paid

    def _build_result(
        self,
        scenario_type: ScenarioType,
        description: str,
        orig_months: int,
        orig_interest: Decimal,
        new_months: int,
        new_interest: Decimal,
    ) -> SimulationResult:
        """Assemble a SimulationResult from before/after figures."""
        total_savings = (orig_interest - new_interest).quantize(
            _CENT, rounding=ROUND_HALF_UP,
        )
        monthly_savings = (
            (total_savings / Decimal(str(orig_months)))
            if orig_months > 0
            else _ZERO
        ).quantize(_CENT, rounding=ROUND_HALF_UP)

        return SimulationResult(
            scenario_type=scenario_type,
            description=description,
            original_payoff_months=orig_months,
            new_payoff_months=new_months,
            original_total_interest=orig_interest,
            new_total_interest=new_interest,
            monthly_savings=monthly_savings,
            total_savings=total_savings,
        )

    # ------------------------------------------------------------------
    # Scenario-specific mutation handlers
    #
    # Each returns (modified_debts, modified_extra, description).
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_extra_payment(
        debts: list[DebtInput],
        base_extra: Decimal,
        params: dict,
    ) -> tuple[list[DebtInput], Decimal, str]:
        additional = Decimal(str(params["additional_payment"]))
        new_extra = base_extra + additional
        description = (
            f"Increase monthly extra payment by ${additional:,.2f} "
            f"(total extra: ${new_extra:,.2f})"
        )
        return debts, new_extra, description

    @staticmethod
    def _apply_rate_change(
        debts: list[DebtInput],
        base_extra: Decimal,
        params: dict,
    ) -> tuple[list[DebtInput], Decimal, str]:
        debt_name: str = params["debt_name"]
        new_rate = Decimal(str(params["new_rate"]))
        modified: list[DebtInput] = []
        found = False
        for d in debts:
            if d.name == debt_name:
                modified.append(d.model_copy(update={"interest_rate": new_rate}))
                found = True
            else:
                modified.append(d)
        if not found:
            raise ValueError(f"Debt '{debt_name}' not found in base debts")
        pct = (new_rate * _HUNDRED).quantize(_CENT, rounding=ROUND_HALF_UP)
        description = f"Change interest rate on '{debt_name}' to {pct}%"
        return modified, base_extra, description

    @staticmethod
    def _apply_new_debt(
        debts: list[DebtInput],
        base_extra: Decimal,
        params: dict,
    ) -> tuple[list[DebtInput], Decimal, str]:
        new_debt = DebtInput(
            name=params["name"],
            balance=Decimal(str(params["balance"])),
            interest_rate=Decimal(str(params["interest_rate"])),
            minimum_payment=Decimal(str(params["minimum_payment"])),
        )
        modified = list(debts) + [new_debt]
        pct = (new_debt.interest_rate * _HUNDRED).quantize(
            _CENT, rounding=ROUND_HALF_UP,
        )
        description = (
            f"Add new debt '{new_debt.name}' -- "
            f"${new_debt.balance:,.2f} at {pct}%"
        )
        return modified, base_extra, description

    @staticmethod
    def _apply_income_change(
        debts: list[DebtInput],
        base_extra: Decimal,
        params: dict,
    ) -> tuple[list[DebtInput], Decimal, str]:
        delta = Decimal(str(params["monthly_delta"]))
        new_extra = max(base_extra + delta, _ZERO)
        direction = "increase" if delta >= _ZERO else "decrease"
        description = (
            f"Monthly income {direction} of ${abs(delta):,.2f} "
            f"(extra payment now ${new_extra:,.2f})"
        )
        return debts, new_extra, description

    @staticmethod
    def _apply_lump_sum(
        debts: list[DebtInput],
        base_extra: Decimal,
        params: dict,
    ) -> tuple[list[DebtInput], Decimal, str]:
        debt_name: str = params["debt_name"]
        amount = Decimal(str(params["amount"]))
        modified: list[DebtInput] = []
        found = False
        for d in debts:
            if d.name == debt_name:
                new_balance = max(d.balance - amount, _ZERO)
                modified.append(d.model_copy(update={"balance": new_balance}))
                found = True
            else:
                modified.append(d)
        if not found:
            raise ValueError(f"Debt '{debt_name}' not found in base debts")
        description = f"Apply ${amount:,.2f} lump-sum payment to '{debt_name}'"
        return modified, base_extra, description

    # Dispatch table -------------------------------------------------------

    _SCENARIO_HANDLERS = {
        ScenarioType.EXTRA_PAYMENT: _apply_extra_payment,
        ScenarioType.RATE_CHANGE: _apply_rate_change,
        ScenarioType.NEW_DEBT: _apply_new_debt,
        ScenarioType.INCOME_CHANGE: _apply_income_change,
        ScenarioType.LUMP_SUM: _apply_lump_sum,
    }

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run_scenario(
        self,
        base_debts: list[DebtInput],
        base_extra_payment: Decimal,
        scenario: ScenarioInput,
    ) -> SimulationResult:
        """Evaluate a single what-if scenario against the baseline.

        Parameters
        ----------
        base_debts:
            Current debt portfolio snapshot.
        base_extra_payment:
            Monthly extra payment already being made.
        scenario:
            The what-if scenario to evaluate.

        Returns
        -------
        SimulationResult
            Before/after comparison with savings figures.

        Raises
        ------
        ValueError
            If a referenced debt name is not found in *base_debts*.
        KeyError
            If a required parameter is missing from ``scenario.parameters``.
        """
        orig_months, orig_interest = self._baseline(
            base_debts, base_extra_payment,
        )

        handler = self._SCENARIO_HANDLERS[scenario.scenario_type]
        modified_debts, modified_extra, description = handler(
            base_debts, base_extra_payment, scenario.parameters,
        )

        scenario_result = self._financial.calculate_payoff(
            modified_debts, _DEFAULT_STRATEGY, modified_extra,
        )

        return self._build_result(
            scenario_type=scenario.scenario_type,
            description=description,
            orig_months=orig_months,
            orig_interest=orig_interest,
            new_months=scenario_result.total_months,
            new_interest=scenario_result.total_interest_paid,
        )

    def run_batch(
        self,
        base_debts: list[DebtInput],
        base_extra_payment: Decimal,
        scenarios: list[ScenarioInput],
    ) -> list[SimulationResult]:
        """Evaluate multiple scenarios against the same baseline.

        Each scenario is evaluated independently; mutations from one
        scenario do **not** carry over to the next.
        """
        return [
            self.run_scenario(base_debts, base_extra_payment, s)
            for s in scenarios
        ]
