"""
Pydantic v2 schemas for the Analytics module.

Provides request/response validation for analytics events,
monthly snapshots, and dashboard statistics.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    """Allowed analytics event types."""

    DEBT_PAID_OFF = "debt_paid_off"
    PAYMENT_MADE = "payment_made"
    STRATEGY_CHANGED = "strategy_changed"
    SIMULATION_RUN = "simulation_run"
    ADVICE_REQUESTED = "advice_requested"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class EventCreate(BaseModel):
    """Payload for logging a new analytics event."""

    event_type: EventType
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary JSON metadata for the event",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_type": "payment_made",
                "payload": {"debt_id": "abc-123", "amount": "250.00"},
            }
        }
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class EventResponse(BaseModel):
    """Full analytics event record returned to the client."""

    id: uuid.UUID
    user_id: uuid.UUID
    event_type: EventType
    payload: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SnapshotResponse(BaseModel):
    """Full monthly snapshot record returned to the client."""

    id: uuid.UUID
    user_id: uuid.UUID
    snapshot_month: date
    total_debt: Decimal
    total_income: Decimal
    total_expenses: Decimal
    debt_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    """Aggregated dashboard statistics for the authenticated user."""

    total_debt: Decimal = Field(
        ...,
        description="Sum of current_balance across all active debts",
    )
    total_income: Decimal = Field(
        ...,
        description="Normalised monthly income total",
    )
    total_expenses: Decimal = Field(
        ...,
        description="Monthly expenses total",
    )
    debt_count: int = Field(
        ...,
        description="Number of active debts",
    )
    monthly_payment: Decimal = Field(
        ...,
        description="Sum of minimum payments across active debts",
    )
    estimated_payoff_date: date | None = Field(
        None,
        description="Estimated date when all debts will be paid off",
    )
    debt_free_progress_pct: Decimal = Field(
        ...,
        description="Percentage of total debt already paid off (0-100)",
        ge=0,
        le=100,
    )

    model_config = ConfigDict(from_attributes=True)
