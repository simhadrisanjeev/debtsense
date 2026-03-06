"""
FastAPI router for simulation endpoints.

Exposes POST endpoints for running single and batch what-if
scenarios against a debt portfolio baseline.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.modules.simulation_engine.schemas import (
    SimulationRequest,
    SimulationResponse,
    SimulationResult,
)
from app.modules.simulation_engine.service import SimulationService

router = APIRouter()


def _service() -> SimulationService:
    """Factory for the simulation service (stateless, no DB required)."""
    return SimulationService()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/run",
    response_model=SimulationResult,
    status_code=status.HTTP_200_OK,
    summary="Run a single what-if scenario",
)
async def run_single_scenario(
    payload: SimulationRequest,
) -> SimulationResult:
    """Evaluate a single what-if scenario against the provided debt baseline.

    Only the **first** entry in ``scenarios`` is evaluated.  For
    multiple scenarios in one request, use ``POST /batch`` instead.
    """
    service = _service()
    return await service.run_scenario(
        base_debts=payload.base_debts,
        base_extra_payment=payload.base_extra_payment,
        scenario=payload.scenarios[0],
    )


@router.post(
    "/batch",
    response_model=SimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Run multiple what-if scenarios",
)
async def run_batch_scenarios(
    payload: SimulationRequest,
) -> SimulationResponse:
    """Evaluate every scenario in ``scenarios`` against the same baseline.

    Each scenario is evaluated independently -- mutations from one
    scenario do **not** carry over to the next.  The response is
    wrapped in a ``SimulationResponse`` envelope with a ``generated_at``
    timestamp.
    """
    service = _service()
    return await service.run_batch(
        base_debts=payload.base_debts,
        base_extra_payment=payload.base_extra_payment,
        scenarios=payload.scenarios,
    )
