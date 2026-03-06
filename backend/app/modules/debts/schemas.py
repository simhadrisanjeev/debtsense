"""
Pydantic v2 schemas for the Debts module.

Provides request/response validation for CRUD operations
and an aggregated summary schema.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class DebtType(str, Enum):
    """Allowed debt categories."""

    CREDIT_CARD = "credit_card"
    STUDENT_LOAN = "student_loan"
    MORTGAGE = "mortgage"
    AUTO_LOAN = "auto_loan"
    PERSONAL_LOAN = "personal_loan"
    MEDICAL = "medical"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Shared field constraints
# ---------------------------------------------------------------------------
PositiveBalance = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
PositivePayment = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]
InterestRate = Annotated[Decimal, Field(ge=0, le=1, max_digits=5, decimal_places=4)]
DayOfMonth = Annotated[int, Field(ge=1, le=31)]


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------
class DebtCreate(BaseModel):
    """Payload for creating a new debt."""

    name: str = Field(..., min_length=1, max_length=255, examples=["Chase Visa"])
    debt_type: DebtType
    principal_balance: PositiveBalance
    current_balance: PositiveBalance
    interest_rate: InterestRate = Field(
        ...,
        description="APR expressed as a decimal, e.g. 0.1999 for 19.99%",
        examples=[Decimal("0.1999")],
    )
    minimum_payment: PositivePayment
    due_date: DayOfMonth
    start_date: date
    is_active: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Chase Visa",
                "debt_type": "credit_card",
                "principal_balance": "5000.00",
                "current_balance": "4200.50",
                "interest_rate": "0.1999",
                "minimum_payment": "105.00",
                "due_date": 15,
                "start_date": "2024-01-10",
            }
        }
    )


class DebtUpdate(BaseModel):
    """Payload for partially updating an existing debt.

    Every field is optional so the client can send only changed values.
    """

    name: str | None = Field(None, min_length=1, max_length=255)
    debt_type: DebtType | None = None
    principal_balance: PositiveBalance | None = None
    current_balance: PositiveBalance | None = None
    interest_rate: InterestRate | None = None
    minimum_payment: PositivePayment | None = None
    due_date: DayOfMonth | None = None
    start_date: date | None = None
    is_active: bool | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_balance": "3800.00",
                "minimum_payment": "95.00",
            }
        }
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------
class DebtResponse(BaseModel):
    """Full debt record returned to the client."""

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    debt_type: DebtType
    principal_balance: Decimal
    current_balance: Decimal
    interest_rate: Decimal
    minimum_payment: Decimal
    due_date: int
    start_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DebtSummary(BaseModel):
    """Aggregated statistics across all active debts for a user."""

    total_balance: Decimal = Field(
        ...,
        description="Sum of current_balance for all active debts",
    )
    total_minimum_payment: Decimal = Field(
        ...,
        description="Sum of minimum_payment for all active debts",
    )
    debt_count: int = Field(
        ...,
        description="Number of active debts",
    )
    weighted_avg_rate: Decimal = Field(
        ...,
        description="Balance-weighted average interest rate across active debts",
    )

    model_config = ConfigDict(from_attributes=True)
