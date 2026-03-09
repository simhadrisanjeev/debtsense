"""
Pydantic v2 schemas for the Debts module.

Provides request/response validation for CRUD operations,
payment overrides, interest calculation, and payment schedules.
"""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DebtType(str, Enum):
    CREDIT_CARD = "credit_card"
    PERSONAL_LOAN = "personal_loan"
    GOLD_LOAN = "gold_loan"
    HOME_LOAN = "home_loan"
    AUTO_LOAN = "auto_loan"
    EDUCATION_LOAN = "education_loan"
    INFORMAL_LOAN = "informal_loan"
    MONEY_LENDER = "money_lender"
    BUSINESS_LOAN = "business_loan"
    CHIT_FUND = "chit_fund"
    OTHER = "other"


class InterestType(str, Enum):
    REDUCING_BALANCE = "reducing_balance"
    FLAT_INTEREST = "flat_interest"
    MONTHLY_INTEREST = "monthly_interest"
    NO_INTEREST = "no_interest"


class RepaymentStyle(str, Enum):
    EMI = "emi"
    INTEREST_ONLY = "interest_only"
    BULLET_PAYMENT = "bullet_payment"
    FLEXIBLE = "flexible"


class PaymentFrequency(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Shared field constraints
# ---------------------------------------------------------------------------

PositiveBalance = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
PositivePayment = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]
InterestRate = Annotated[Decimal, Field(ge=0, le=1, max_digits=7, decimal_places=4)]
DayOfMonth = Annotated[int, Field(ge=1, le=31)]


# ---------------------------------------------------------------------------
# Debt Request schemas
# ---------------------------------------------------------------------------

class DebtCreate(BaseModel):
    """Payload for creating a new debt."""

    name: str = Field(..., min_length=1, max_length=255, examples=["HDFC Credit Card"])
    debt_type: DebtType
    lender_name: str | None = Field(None, max_length=255)
    principal_amount: PositiveBalance
    current_balance: PositiveBalance
    interest_rate: InterestRate = Field(
        ...,
        description="Annual rate as decimal, e.g. 0.1999 for 19.99%",
        examples=[Decimal("0.1999")],
    )
    interest_type: InterestType = InterestType.REDUCING_BALANCE
    repayment_style: RepaymentStyle = RepaymentStyle.EMI
    payment_frequency: PaymentFrequency = PaymentFrequency.MONTHLY
    minimum_payment: PositivePayment
    due_day_of_month: DayOfMonth
    start_date: date
    end_date: date | None = None
    is_active: bool = True
    notes: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "HDFC Credit Card",
                "debt_type": "credit_card",
                "lender_name": "HDFC Bank",
                "principal_amount": "50000.00",
                "current_balance": "42000.00",
                "interest_rate": "0.3600",
                "interest_type": "reducing_balance",
                "repayment_style": "emi",
                "payment_frequency": "monthly",
                "minimum_payment": "2100.00",
                "due_day_of_month": 15,
                "start_date": "2025-01-10",
            }
        }
    )


class DebtUpdate(BaseModel):
    """Payload for partially updating an existing debt."""

    name: str | None = Field(None, min_length=1, max_length=255)
    debt_type: DebtType | None = None
    lender_name: str | None = Field(None, max_length=255)
    principal_amount: PositiveBalance | None = None
    current_balance: PositiveBalance | None = None
    interest_rate: InterestRate | None = None
    interest_type: InterestType | None = None
    repayment_style: RepaymentStyle | None = None
    payment_frequency: PaymentFrequency | None = None
    minimum_payment: PositivePayment | None = None
    due_day_of_month: DayOfMonth | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None
    notes: str | None = None


# ---------------------------------------------------------------------------
# Debt Response schemas
# ---------------------------------------------------------------------------

class DebtResponse(BaseModel):
    """Full debt record returned to the client."""

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    debt_type: DebtType
    lender_name: str | None
    principal_amount: Decimal
    current_balance: Decimal
    interest_rate: Decimal
    interest_type: InterestType
    repayment_style: RepaymentStyle
    payment_frequency: PaymentFrequency
    minimum_payment: Decimal
    due_day_of_month: int
    start_date: date
    end_date: date | None
    is_active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DebtSummary(BaseModel):
    """Aggregated statistics across all active debts for a user."""

    total_balance: Decimal = Field(
        ..., description="Sum of current_balance for all active debts",
    )
    total_minimum_payment: Decimal = Field(
        ..., description="Sum of minimum_payment for all active debts",
    )
    debt_count: int = Field(
        ..., description="Number of active debts",
    )
    weighted_avg_rate: Decimal = Field(
        ..., description="Balance-weighted average interest rate",
    )

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Payment Override schemas
# ---------------------------------------------------------------------------

_MONTH_YEAR_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class PaymentOverrideCreate(BaseModel):
    """Payload for creating a monthly payment override."""

    month_year: str = Field(
        ..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="YYYY-MM format",
        examples=["2026-03"],
    )
    custom_payment_amount: PositivePayment
    note: str | None = None

    @field_validator("month_year")
    @classmethod
    def validate_month_year(cls, v: str) -> str:
        if not _MONTH_YEAR_RE.match(v):
            raise ValueError("month_year must be in YYYY-MM format")
        return v


class PaymentOverrideUpdate(BaseModel):
    """Payload for updating a payment override."""

    custom_payment_amount: PositivePayment | None = None
    note: str | None = None


class PaymentOverrideResponse(BaseModel):
    """Payment override record returned to the client."""

    id: uuid.UUID
    debt_id: uuid.UUID
    user_id: uuid.UUID
    month_year: str
    custom_payment_amount: Decimal
    note: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Payment schedule schemas
# ---------------------------------------------------------------------------

class MonthlyPaymentDetail(BaseModel):
    """One month in the projected payment schedule."""

    month: str
    interest: Decimal
    payment: Decimal
    principal_paid: Decimal
    remaining_balance: Decimal


class PaymentScheduleResponse(BaseModel):
    """Full projected payment schedule for a debt."""

    debt_id: uuid.UUID
    schedule: list[MonthlyPaymentDetail]
    total_interest: Decimal
    total_paid: Decimal
    payoff_months: int
