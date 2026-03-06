"""
Pydantic v2 schemas for expense validation and serialisation.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ExpenseCategoryEnum(str, Enum):
    """Allowed expense categories."""

    HOUSING = "housing"
    TRANSPORTATION = "transportation"
    FOOD = "food"
    UTILITIES = "utilities"
    INSURANCE = "insurance"
    HEALTHCARE = "healthcare"
    ENTERTAINMENT = "entertainment"
    SUBSCRIPTIONS = "subscriptions"
    OTHER = "other"


class ExpenseFrequencyEnum(str, Enum):
    """Allowed recurrence frequencies."""

    ONE_TIME = "one_time"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    ANNUALLY = "annually"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ExpenseCreate(BaseModel):
    """Payload for creating a new expense."""

    model_config = ConfigDict(from_attributes=True)

    category: ExpenseCategoryEnum
    description: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    frequency: ExpenseFrequencyEnum = ExpenseFrequencyEnum.MONTHLY
    is_recurring: bool = True


class ExpenseUpdate(BaseModel):
    """Payload for partially updating an expense.  All fields are optional."""

    model_config = ConfigDict(from_attributes=True)

    category: ExpenseCategoryEnum | None = None
    description: str | None = Field(default=None, min_length=1, max_length=255)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    frequency: ExpenseFrequencyEnum | None = None
    is_recurring: bool | None = None
    is_active: bool | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ExpenseResponse(BaseModel):
    """Serialised representation of a single expense."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    category: ExpenseCategoryEnum
    description: str
    amount: Decimal
    frequency: ExpenseFrequencyEnum
    is_recurring: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CategoryBreakdown(BaseModel):
    """Spending total for a single category."""

    category: ExpenseCategoryEnum
    total: Decimal
    count: int


class ExpenseSummary(BaseModel):
    """Aggregated spending breakdown across all categories."""

    user_id: uuid.UUID
    total_monthly: Decimal
    breakdown: list[CategoryBreakdown]
