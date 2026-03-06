"""
FastAPI router for the financial engine module.

Exposes endpoints for single-strategy payoff calculations and
multi-strategy comparisons.  All routes require authentication.
"""

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser
from app.modules.financial_engine.schemas import (
    CompareRequest,
    PayoffRequest,
    PayoffResult,
    StrategyComparison,
)
from app.modules.financial_engine.service import FinancialEngineService

router = APIRouter()


@router.post(
    "/calculate",
    response_model=PayoffResult,
    status_code=status.HTTP_200_OK,
    summary="Calculate payoff schedule for a single strategy",
)
async def calculate_payoff(
    body: PayoffRequest,
    current_user: CurrentUser,
) -> PayoffResult:
    """Run a month-by-month amortization simulation for the chosen strategy.

    Returns the full schedule, total interest, total paid, payoff order,
    and projected debt-free date.
    """
    service = FinancialEngineService()
    return service.calculate(
        debts=body.debts,
        strategy=body.strategy,
        extra_payment=body.extra_payment,
    )


@router.post(
    "/compare",
    response_model=StrategyComparison,
    status_code=status.HTTP_200_OK,
    summary="Compare all payoff strategies",
)
async def compare_strategies(
    body: CompareRequest,
    current_user: CurrentUser,
) -> StrategyComparison:
    """Evaluate snowball, avalanche, and hybrid strategies side-by-side.

    Returns results for each strategy together with a recommendation
    (lowest total interest) and the interest savings versus minimum-only
    payments.
    """
    service = FinancialEngineService()
    return service.compare(
        debts=body.debts,
        extra_payment=body.extra_payment,
    )
