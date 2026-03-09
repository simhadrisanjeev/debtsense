"""
Interest calculation utilities for different Indian and international
debt structures.

Supports:
- Reducing balance (standard EMI-style)
- Flat interest (interest on original principal)
- Monthly interest (simple monthly rate on current balance)
- No interest
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


def calculate_monthly_interest(
    balance: Decimal | float,
    annual_rate: Decimal | float,
    interest_type: str,
    principal_amount: Decimal | float | None = None,
) -> Decimal:
    """Calculate the interest component for one month.

    Args:
        balance: Current outstanding balance.
        annual_rate: Annual interest rate as a decimal (e.g. 0.18 for 18%).
        interest_type: One of 'reducing_balance', 'flat_interest',
                       'monthly_interest', 'no_interest'.
        principal_amount: Original principal (used for flat_interest).

    Returns:
        Monthly interest amount rounded to 2 decimal places.
    """
    balance = Decimal(str(balance))
    annual_rate = Decimal(str(annual_rate))

    if interest_type == "no_interest" or annual_rate <= 0 or balance <= 0:
        return Decimal("0.00")

    if interest_type == "flat_interest":
        # Flat interest: calculated on original principal regardless of balance
        principal = Decimal(str(principal_amount)) if principal_amount else balance
        monthly = (principal * annual_rate) / Decimal("12")
    elif interest_type == "monthly_interest":
        # Monthly interest: simple monthly rate on current balance
        # Here annual_rate is treated as annual; divide by 12
        monthly = (balance * annual_rate) / Decimal("12")
    else:
        # reducing_balance (default): interest on current balance
        monthly = (balance * annual_rate) / Decimal("12")

    return monthly.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_emi(
    principal: Decimal | float,
    annual_rate: Decimal | float,
    tenure_months: int,
) -> Decimal:
    """Calculate the fixed EMI for a reducing-balance loan.

    Uses the standard formula:
        EMI = P * r * (1+r)^n / ((1+r)^n - 1)

    where r = monthly rate, n = number of months.

    Returns 0 if tenure is 0 or rate is 0 (simple division fallback).
    """
    P = Decimal(str(principal))
    annual = Decimal(str(annual_rate))

    if tenure_months <= 0 or P <= 0:
        return Decimal("0.00")

    if annual <= 0:
        # No interest — equal principal installments
        return (P / Decimal(str(tenure_months))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    r = annual / Decimal("12")
    n = Decimal(str(tenure_months))

    # (1+r)^n
    compound = (1 + r) ** n
    emi = P * r * compound / (compound - 1)

    return emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
