"""
Pydantic v2 schemas for income validation and serialisation.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class IncomeSource(str, Enum):
    """Allowed income source categories."""

    SALARY = "salary"
    FREELANCE = "freelance"
    INVESTMENT = "investment"
    RENTAL = "rental"
    SIDE_HUSTLE = "side_hustle"
    OTHER = "other"


class IncomeFrequency(str, Enum):
    """Allowed payment frequencies."""

    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    ANNUALLY = "annually"


# ---------------------------------------------------------------------------
# Shared field constraints
# ---------------------------------------------------------------------------

Amount = Annotated[
    Decimal,
    Field(gt=0, max_digits=12, decimal_places=2, description="Positive income amount"),
]


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class IncomeCreate(BaseModel):
    """Payload for creating a new income entry."""

    source: IncomeSource
    amount: Amount
    frequency: IncomeFrequency
    is_active: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "source": "salary",
                    "amount": "5500.00",
                    "frequency": "monthly",
                    "is_active": True,
                }
            ]
        }
    )


class IncomeUpdate(BaseModel):
    """Payload for partially updating an income entry. All fields optional."""

    source: IncomeSource | None = None
    amount: Amount | None = None
    frequency: IncomeFrequency | None = None
    is_active: bool | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "amount": "6000.00",
                    "is_active": False,
                }
            ]
        }
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class IncomeResponse(BaseModel):
    """Serialised income record returned to the client."""

    id: uuid.UUID
    user_id: uuid.UUID
    source: IncomeSource
    amount: Decimal
    frequency: IncomeFrequency
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MonthlyTotalResponse(BaseModel):
    """Aggregated monthly income total for a user."""

    user_id: uuid.UUID
    monthly_total: Decimal
    active_sources: int
