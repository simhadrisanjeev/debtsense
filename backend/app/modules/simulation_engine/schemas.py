"""
Pydantic v2 schemas for the Simulation Engine module.

Defines request/response models for what-if scenario evaluation,
including scenario types, parameters, and comparison results.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.financial_engine.schemas import DebtInput


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ScenarioType(str, Enum):
    """Supported what-if scenario categories."""

    EXTRA_PAYMENT = "extra_payment"
    RATE_CHANGE = "rate_change"
    NEW_DEBT = "new_debt"
    INCOME_CHANGE = "income_change"
    LUMP_SUM = "lump_sum"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ScenarioInput(BaseModel):
    """A single what-if scenario to evaluate.

    The ``parameters`` dict carries scenario-specific fields:

    * **extra_payment** -- ``{"additional_payment": Decimal}``
    * **rate_change** -- ``{"debt_name": str, "new_rate": Decimal}``
    * **new_debt** -- ``{"name": str, "balance": Decimal,
      "interest_rate": Decimal, "minimum_payment": Decimal}``
    * **income_change** -- ``{"monthly_delta": Decimal}``
    * **lump_sum** -- ``{"debt_name": str, "amount": Decimal}``
    """

    scenario_type: ScenarioType
    parameters: dict[str, Any] = Field(
        ...,
        description=(
            "Scenario-specific key/value pairs.  See class docstring "
            "for the expected shape per scenario type."
        ),
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "scenario_type": "extra_payment",
                    "parameters": {"additional_payment": "200.00"},
                },
                {
                    "scenario_type": "rate_change",
                    "parameters": {
                        "debt_name": "Chase Visa",
                        "new_rate": "0.1499",
                    },
                },
                {
                    "scenario_type": "lump_sum",
                    "parameters": {
                        "debt_name": "Chase Visa",
                        "amount": "1000.00",
                    },
                },
            ]
        }
    )


class SimulationRequest(BaseModel):
    """Full payload for running one or more what-if simulations."""

    base_debts: list[DebtInput] = Field(
        ...,
        min_length=1,
        description="Current debt portfolio snapshot used as the baseline",
    )
    base_extra_payment: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Monthly extra payment already being applied in the baseline",
    )
    scenarios: list[ScenarioInput] = Field(
        ...,
        min_length=1,
        description="One or more what-if scenarios to evaluate",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "base_debts": [
                    {
                        "name": "Chase Visa",
                        "balance": "4200.50",
                        "interest_rate": "0.1999",
                        "minimum_payment": "105.00",
                    }
                ],
                "base_extra_payment": "100.00",
                "scenarios": [
                    {
                        "scenario_type": "extra_payment",
                        "parameters": {"additional_payment": "200.00"},
                    }
                ],
            }
        }
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class SimulationResult(BaseModel):
    """Outcome of a single what-if scenario compared to the baseline."""

    scenario_type: ScenarioType
    description: str = Field(
        ..., description="Human-readable explanation of the scenario",
    )
    original_payoff_months: int = Field(
        ..., ge=0, description="Months to payoff under the baseline",
    )
    new_payoff_months: int = Field(
        ..., ge=0, description="Months to payoff under the scenario",
    )
    original_total_interest: Decimal = Field(
        ..., ge=0, description="Cumulative interest under the baseline",
    )
    new_total_interest: Decimal = Field(
        ..., ge=0, description="Cumulative interest under the scenario",
    )
    monthly_savings: Decimal = Field(
        ...,
        description=(
            "Estimated monthly interest savings (positive means cheaper, "
            "negative means costlier)"
        ),
    )
    total_savings: Decimal = Field(
        ...,
        description=(
            "Total interest saved (positive) or added (negative) "
            "compared to the baseline"
        ),
    )

    model_config = ConfigDict(from_attributes=True)


class SimulationResponse(BaseModel):
    """Envelope for one or more simulation results."""

    results: list[SimulationResult]
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    model_config = ConfigDict(from_attributes=True)
