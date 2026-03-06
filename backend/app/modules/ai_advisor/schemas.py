"""
Pydantic v2 schemas for the AI Advisor module.

Covers request/response validation for the advisory endpoints
and the quick-tips feature.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Context schema — snapshot of the user's financial picture
# ---------------------------------------------------------------------------

class AdvisorContext(BaseModel):
    """Condensed financial profile sent alongside an advisory question."""

    total_debt: Decimal = Field(
        ...,
        description="Sum of all outstanding debt balances",
    )
    total_income: Decimal = Field(
        ...,
        description="Estimated monthly income",
    )
    total_expenses: Decimal = Field(
        ...,
        description="Estimated monthly expenses",
    )
    debt_count: int = Field(
        ...,
        ge=0,
        description="Number of active debts",
    )
    highest_rate_debt: str = Field(
        ...,
        max_length=255,
        description="Name of the debt with the highest interest rate",
    )
    debt_to_income_ratio: Decimal = Field(
        ...,
        description="Total debt divided by monthly income",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_debt": "24500.00",
                "total_income": "5200.00",
                "total_expenses": "3800.00",
                "debt_count": 4,
                "highest_rate_debt": "Chase Visa",
                "debt_to_income_ratio": "4.71",
            }
        }
    )


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class AdvisorRequest(BaseModel):
    """Payload for asking the AI advisor a question."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The user's question about their debt or financial situation",
    )
    context: AdvisorContext | None = Field(
        default=None,
        description="Optional financial context to personalise the advice",
    )
    conversation_history: list[dict] = Field(
        default=[],
        description="Prior messages in the conversation for multi-turn context",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "Should I pay off my credit card or student loan first?",
                "context": None,
                "conversation_history": [],
            }
        }
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class AdvisorResponse(BaseModel):
    """Structured response from the AI advisor."""

    advice: str = Field(
        ...,
        description="The main advisory text",
    )
    suggestions: list[str] = Field(
        ...,
        description="Actionable next-step suggestions",
    )
    risk_level: str = Field(
        ...,
        description="Assessed risk level: low, moderate, high, or critical",
    )
    disclaimer: str = Field(
        ...,
        description="Legal/ethical disclaimer about the advice provided",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "advice": "Focus on paying off the Chase Visa first ...",
                "suggestions": [
                    "Make minimum payments on all other debts",
                    "Allocate any extra cash to the highest-rate balance",
                ],
                "risk_level": "moderate",
                "disclaimer": (
                    "This is educational guidance, not professional financial advice. "
                    "Consult a certified financial planner for personalised recommendations."
                ),
            }
        }
    )


# ---------------------------------------------------------------------------
# Quick tips schemas
# ---------------------------------------------------------------------------

class QuickTip(BaseModel):
    """A single personalised financial tip."""

    tip: str = Field(
        ...,
        description="Short, actionable tip text",
    )
    category: str = Field(
        ...,
        description="Tip category, e.g. budgeting, debt_payoff, savings",
    )
    priority: int = Field(
        ...,
        ge=1,
        le=10,
        description="Priority ranking (1 = highest priority)",
    )


class QuickTipsResponse(BaseModel):
    """Collection of personalised quick tips."""

    tips: list[QuickTip] = Field(
        ...,
        description="Ordered list of personalised financial tips",
    )
