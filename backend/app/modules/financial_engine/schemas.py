"""
Pydantic v2 request / response schemas for the financial engine module.

Defines the data contracts for debt payoff strategy calculations,
amortization schedules, and multi-strategy comparison results.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Shared field constraints (consistent with debts module conventions)
# ---------------------------------------------------------------------------

PositiveBalance = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
PositivePayment = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]
InterestRate = Annotated[Decimal, Field(ge=0, le=1, max_digits=5, decimal_places=4)]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PayoffStrategy(str, Enum):
    """Supported debt payoff strategies."""

    SNOWBALL = "snowball"
    AVALANCHE = "avalanche"
    HYBRID = "hybrid"
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class DebtInput(BaseModel):
    """A single debt to include in the payoff calculation.

    ``interest_rate`` is the annual percentage rate expressed as a decimal
    (e.g. ``0.1999`` for 19.99 %).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Chase Visa",
                "balance": "4200.50",
                "interest_rate": "0.1999",
                "minimum_payment": "105.00",
            }
        },
    )

    name: str = Field(..., min_length=1, max_length=255, examples=["Chase Visa"])
    balance: PositiveBalance = Field(
        ...,
        description="Current outstanding balance",
    )
    interest_rate: InterestRate = Field(
        ...,
        description="APR as a decimal, e.g. 0.1999 for 19.99%",
    )
    minimum_payment: PositivePayment = Field(
        ...,
        description="Required monthly minimum payment",
    )


class PayoffRequest(BaseModel):
    """Request body for a single-strategy payoff calculation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "debts": [
                    {
                        "name": "Chase Visa",
                        "balance": "4200.50",
                        "interest_rate": "0.1999",
                        "minimum_payment": "105.00",
                    },
                    {
                        "name": "Student Loan",
                        "balance": "15000.00",
                        "interest_rate": "0.0550",
                        "minimum_payment": "180.00",
                    },
                ],
                "strategy": "avalanche",
                "extra_payment": "200.00",
            }
        },
    )

    debts: list[DebtInput] = Field(..., min_length=1, description="Debts to analyze")
    strategy: PayoffStrategy
    extra_payment: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Additional monthly amount beyond all minimum payments",
    )


class CompareRequest(BaseModel):
    """Request body for comparing all payoff strategies."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "debts": [
                    {
                        "name": "Chase Visa",
                        "balance": "4200.50",
                        "interest_rate": "0.1999",
                        "minimum_payment": "105.00",
                    },
                    {
                        "name": "Student Loan",
                        "balance": "15000.00",
                        "interest_rate": "0.0550",
                        "minimum_payment": "180.00",
                    },
                ],
                "extra_payment": "200.00",
            }
        },
    )

    debts: list[DebtInput] = Field(..., min_length=1, description="Debts to analyze")
    extra_payment: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Additional monthly amount beyond all minimum payments",
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class PayoffScheduleEntry(BaseModel):
    """A single row in the month-by-month amortization schedule."""

    model_config = ConfigDict(from_attributes=True)

    month: int = Field(..., ge=1, description="Month number (1-based)")
    debt_name: str = Field(..., description="Name of the debt this entry applies to")
    payment: Decimal = Field(..., description="Total payment applied this month")
    principal: Decimal = Field(..., description="Portion of payment applied to principal")
    interest: Decimal = Field(..., description="Portion of payment consumed by interest")
    remaining_balance: Decimal = Field(
        ...,
        description="Outstanding balance after this month's payment",
    )


class PayoffResult(BaseModel):
    """Complete result of a payoff strategy simulation."""

    model_config = ConfigDict(from_attributes=True)

    strategy: str = Field(..., description="Strategy name used for this simulation")
    total_months: int = Field(..., ge=0, description="Months until all debts are paid off")
    total_interest_paid: Decimal = Field(
        ...,
        description="Cumulative interest paid across all debts",
    )
    total_paid: Decimal = Field(
        ...,
        description="Total of all payments (principal + interest)",
    )
    payoff_order: list[str] = Field(
        ...,
        description="Order in which debts are fully paid off",
    )
    schedule: list[PayoffScheduleEntry] = Field(
        ...,
        description="Month-by-month amortization schedule for every debt",
    )
    debt_free_date: str = Field(
        ...,
        description="Projected debt-free date (YYYY-MM format)",
    )


class StrategyComparison(BaseModel):
    """Side-by-side comparison of all payoff strategies."""

    model_config = ConfigDict(from_attributes=True)

    strategies: list[PayoffResult] = Field(
        ...,
        description="Results for each strategy evaluated",
    )
    recommended: str = Field(
        ...,
        description="Strategy name that minimises total interest paid",
    )
    interest_savings_vs_minimum: Decimal = Field(
        ...,
        description="Interest saved by the recommended strategy vs. minimum-only payments",
    )
