"""
Pydantic v2 schemas for income validation and serialisation.

Supports allocation-month logic where income received on one date
can be allocated to a different month's budget.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class IncomeType(str, Enum):
    """Allowed income type categories."""

    SALARY = "salary"
    FREELANCE = "freelance"
    BUSINESS = "business"
    BONUS = "bonus"
    GIFT = "gift"
    INVESTMENT = "investment"
    OTHER = "other"


class IncomeAllocationType(str, Enum):
    """Determines which month income is allocated to."""

    SAME_MONTH = "same_month"
    NEXT_MONTH = "next_month"


# ---------------------------------------------------------------------------
# Shared field constraints
# ---------------------------------------------------------------------------

Amount = Annotated[
    Decimal,
    Field(gt=0, max_digits=12, decimal_places=2, description="Positive income amount"),
]

RecurringDay = Annotated[
    int,
    Field(ge=1, le=31, description="Day of month for recurring income (1-31)"),
]


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class IncomeCreate(BaseModel):
    """Payload for creating a new income entry."""

    income_type: IncomeType
    amount: Amount
    date_received: date
    income_allocation_type: IncomeAllocationType = IncomeAllocationType.SAME_MONTH
    is_recurring: bool = False
    recurring_day: RecurringDay | None = None
    note: str | None = Field(None, max_length=500)
    is_active: bool = True

    @field_validator("date_received")
    @classmethod
    def date_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("date_received cannot be in the future")
        return v

    @model_validator(mode="after")
    def recurring_day_required_when_recurring(self) -> "IncomeCreate":
        if self.is_recurring and self.recurring_day is None:
            raise ValueError("recurring_day is required when is_recurring is true")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "income_type": "salary",
                    "amount": "80000.00",
                    "date_received": "2026-03-31",
                    "income_allocation_type": "next_month",
                    "is_recurring": True,
                    "recurring_day": 31,
                    "note": "March salary",
                }
            ]
        }
    )


class IncomeUpdate(BaseModel):
    """Payload for partially updating an income entry. All fields optional."""

    income_type: IncomeType | None = None
    amount: Amount | None = None
    date_received: date | None = None
    income_allocation_type: IncomeAllocationType | None = None
    is_recurring: bool | None = None
    recurring_day: RecurringDay | None = None
    note: str | None = None
    is_active: bool | None = None

    @field_validator("date_received")
    @classmethod
    def date_not_future(cls, v: date | None) -> date | None:
        if v is not None and v > date.today():
            raise ValueError("date_received cannot be in the future")
        return v


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class IncomeResponse(BaseModel):
    """Serialised income entry returned to the client."""

    id: uuid.UUID
    user_id: uuid.UUID
    income_type: IncomeType
    amount: Decimal
    date_received: date
    allocation_month: date
    income_allocation_type: IncomeAllocationType
    is_recurring: bool
    recurring_day: int | None
    is_active: bool
    note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncomeByTypeBreakdown(BaseModel):
    """Breakdown of income by type within a month."""

    income_type: str
    total: Decimal
    count: int


class MonthlyIncomeSummaryResponse(BaseModel):
    """Aggregated monthly income summary for a user."""

    user_id: uuid.UUID
    month: date
    monthly_total: Decimal
    entry_count: int
    breakdown: list[IncomeByTypeBreakdown]
