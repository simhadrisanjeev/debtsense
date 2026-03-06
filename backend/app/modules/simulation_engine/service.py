"""
Service layer for simulation operations.

Provides an async-friendly interface over the synchronous
``SimulationEngine``, adding structured logging and a
timestamped response envelope.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import structlog

from app.modules.financial_engine.schemas import DebtInput
from app.modules.simulation_engine.engine import SimulationEngine
from app.modules.simulation_engine.schemas import (
    ScenarioInput,
    SimulationResponse,
    SimulationResult,
)

logger = structlog.get_logger(__name__)


class SimulationService:
    """Thin orchestration wrapper around ``SimulationEngine``.

    The engine itself is CPU-bound and synchronous.  This service
    exposes ``async`` methods so that FastAPI route handlers stay
    consistently awaitable, and adds logging around each call.
    """

    def __init__(self) -> None:
        self._engine = SimulationEngine()

    async def run_scenario(
        self,
        base_debts: list[DebtInput],
        base_extra_payment: Decimal,
        scenario: ScenarioInput,
    ) -> SimulationResult:
        """Run a single what-if scenario and return the comparison result."""
        logger.info(
            "simulation.run_scenario",
            scenario_type=scenario.scenario_type.value,
            debt_count=len(base_debts),
            base_extra_payment=str(base_extra_payment),
        )
        result = self._engine.run_scenario(
            base_debts, base_extra_payment, scenario,
        )
        logger.info(
            "simulation.scenario_complete",
            scenario_type=scenario.scenario_type.value,
            months_saved=result.original_payoff_months - result.new_payoff_months,
            total_savings=str(result.total_savings),
        )
        return result

    async def run_batch(
        self,
        base_debts: list[DebtInput],
        base_extra_payment: Decimal,
        scenarios: list[ScenarioInput],
    ) -> SimulationResponse:
        """Run multiple scenarios and return a timestamped response envelope."""
        logger.info(
            "simulation.run_batch",
            scenario_count=len(scenarios),
            debt_count=len(base_debts),
            base_extra_payment=str(base_extra_payment),
        )
        results = self._engine.run_batch(
            base_debts, base_extra_payment, scenarios,
        )
        response = SimulationResponse(
            results=results,
            generated_at=datetime.now(timezone.utc),
        )
        logger.info(
            "simulation.batch_complete",
            scenario_count=len(results),
        )
        return response
