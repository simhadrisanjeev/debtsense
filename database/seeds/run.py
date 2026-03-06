"""
Database seeder — populate the development database with sample data.

Creates realistic demo users with debts, income, and expenses so the
frontend and API can be exercised without manual data entry.

Usage::

    # From the repository root (backend/ must be on PYTHONPATH):
    python -m database.seeds.run

    # Or via Make:
    make seed-db
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from passlib.context import CryptContext
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_model import Base
from app.core.database import async_session_factory, engine
from app.modules.users.models import User
from app.modules.debts.models import Debt
from app.modules.income.models import Income
from app.modules.expenses.models import Expense

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

DEMO_USERS = [
    {
        "email": "alice@example.com",
        "password": "DemoPass123!",
        "first_name": "Alice",
        "last_name": "Johnson",
        "is_verified": True,
        "subscription_tier": "premium",
    },
    {
        "email": "bob@example.com",
        "password": "DemoPass123!",
        "first_name": "Bob",
        "last_name": "Smith",
        "is_verified": True,
        "subscription_tier": "free",
    },
    {
        "email": "carol@example.com",
        "password": "DemoPass123!",
        "first_name": "Carol",
        "last_name": "Williams",
        "is_verified": False,
        "subscription_tier": "free",
    },
]

# Debts are keyed by user email for association after user creation.
DEMO_DEBTS: dict[str, list[dict]] = {
    "alice@example.com": [
        {
            "name": "Chase Sapphire Visa",
            "debt_type": "credit_card",
            "principal_balance": Decimal("8500.00"),
            "current_balance": Decimal("6230.45"),
            "interest_rate": Decimal("0.1999"),
            "minimum_payment": Decimal("185.00"),
            "due_date": 15,
            "start_date": date(2023, 3, 1),
        },
        {
            "name": "Federal Student Loan",
            "debt_type": "student_loan",
            "principal_balance": Decimal("32000.00"),
            "current_balance": Decimal("27450.00"),
            "interest_rate": Decimal("0.0499"),
            "minimum_payment": Decimal("340.00"),
            "due_date": 1,
            "start_date": date(2019, 9, 1),
        },
        {
            "name": "Toyota Auto Loan",
            "debt_type": "auto_loan",
            "principal_balance": Decimal("22000.00"),
            "current_balance": Decimal("14800.00"),
            "interest_rate": Decimal("0.0389"),
            "minimum_payment": Decimal("420.00"),
            "due_date": 20,
            "start_date": date(2022, 6, 15),
        },
    ],
    "bob@example.com": [
        {
            "name": "Amex Blue Cash",
            "debt_type": "credit_card",
            "principal_balance": Decimal("3200.00"),
            "current_balance": Decimal("2890.00"),
            "interest_rate": Decimal("0.2149"),
            "minimum_payment": Decimal("75.00"),
            "due_date": 10,
            "start_date": date(2024, 1, 15),
        },
        {
            "name": "Medical Bill — ER Visit",
            "debt_type": "medical",
            "principal_balance": Decimal("4500.00"),
            "current_balance": Decimal("4500.00"),
            "interest_rate": Decimal("0.0000"),
            "minimum_payment": Decimal("150.00"),
            "due_date": 25,
            "start_date": date(2025, 8, 10),
        },
    ],
    "carol@example.com": [
        {
            "name": "Home Mortgage",
            "debt_type": "mortgage",
            "principal_balance": Decimal("285000.00"),
            "current_balance": Decimal("268000.00"),
            "interest_rate": Decimal("0.0675"),
            "minimum_payment": Decimal("1850.00"),
            "due_date": 1,
            "start_date": date(2021, 4, 1),
        },
        {
            "name": "Personal Loan — Renovation",
            "debt_type": "personal_loan",
            "principal_balance": Decimal("15000.00"),
            "current_balance": Decimal("11200.00"),
            "interest_rate": Decimal("0.0899"),
            "minimum_payment": Decimal("310.00"),
            "due_date": 5,
            "start_date": date(2023, 11, 1),
        },
    ],
}

DEMO_INCOME: dict[str, list[dict]] = {
    "alice@example.com": [
        {"source": "salary", "amount": Decimal("5800.00"), "frequency": "monthly"},
        {"source": "freelance", "amount": Decimal("1200.00"), "frequency": "monthly"},
    ],
    "bob@example.com": [
        {"source": "salary", "amount": Decimal("4200.00"), "frequency": "monthly"},
    ],
    "carol@example.com": [
        {"source": "salary", "amount": Decimal("7500.00"), "frequency": "monthly"},
        {"source": "rental_income", "amount": Decimal("1800.00"), "frequency": "monthly"},
    ],
}

DEMO_EXPENSES: dict[str, list[dict]] = {
    "alice@example.com": [
        {"category": "housing", "description": "Apartment rent", "amount": Decimal("1400.00"), "frequency": "monthly"},
        {"category": "utilities", "description": "Electric + Water + Internet", "amount": Decimal("220.00"), "frequency": "monthly"},
        {"category": "food", "description": "Groceries", "amount": Decimal("450.00"), "frequency": "monthly"},
        {"category": "transportation", "description": "Gas & car insurance", "amount": Decimal("280.00"), "frequency": "monthly"},
        {"category": "insurance", "description": "Health insurance premium", "amount": Decimal("180.00"), "frequency": "monthly"},
        {"category": "subscriptions", "description": "Streaming services", "amount": Decimal("45.00"), "frequency": "monthly"},
    ],
    "bob@example.com": [
        {"category": "housing", "description": "Studio apartment", "amount": Decimal("1100.00"), "frequency": "monthly"},
        {"category": "food", "description": "Groceries & dining", "amount": Decimal("500.00"), "frequency": "monthly"},
        {"category": "transportation", "description": "Public transit pass", "amount": Decimal("120.00"), "frequency": "monthly"},
        {"category": "entertainment", "description": "Gym membership", "amount": Decimal("50.00"), "frequency": "monthly"},
    ],
    "carol@example.com": [
        {"category": "housing", "description": "Property tax escrow", "amount": Decimal("520.00"), "frequency": "monthly"},
        {"category": "utilities", "description": "All utilities", "amount": Decimal("350.00"), "frequency": "monthly"},
        {"category": "food", "description": "Groceries", "amount": Decimal("600.00"), "frequency": "monthly"},
        {"category": "insurance", "description": "Home + Auto + Health", "amount": Decimal("480.00"), "frequency": "monthly"},
        {"category": "transportation", "description": "Gas & maintenance", "amount": Decimal("200.00"), "frequency": "monthly"},
        {"category": "healthcare", "description": "Prescriptions", "amount": Decimal("85.00"), "frequency": "monthly"},
    ],
}


# ---------------------------------------------------------------------------
# Seeder logic
# ---------------------------------------------------------------------------

async def seed(session: AsyncSession) -> None:
    """Insert all sample data inside a single transaction."""

    user_map: dict[str, uuid.UUID] = {}

    # -- Users ---------------------------------------------------------------
    for user_data in DEMO_USERS:
        # Skip if user already exists
        existing = await session.execute(
            select(User).where(User.email == user_data["email"])
        )
        if existing.scalar_one_or_none() is not None:
            print(f"  [skip] User {user_data['email']} already exists")
            # Still need the ID for associations
            result = await session.execute(
                select(User.id).where(User.email == user_data["email"])
            )
            user_map[user_data["email"]] = result.scalar_one()
            continue

        user = User(
            email=user_data["email"],
            hashed_password=pwd_context.hash(user_data["password"]),
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            is_verified=user_data["is_verified"],
            subscription_tier=user_data["subscription_tier"],
        )
        session.add(user)
        await session.flush()
        user_map[user_data["email"]] = user.id
        print(f"  [created] User {user.email} (id={user.id})")

    # -- Debts ---------------------------------------------------------------
    for email, debts in DEMO_DEBTS.items():
        uid = user_map[email]
        for debt_data in debts:
            debt = Debt(user_id=uid, **debt_data)
            session.add(debt)
        print(f"  [created] {len(debts)} debts for {email}")

    # -- Income --------------------------------------------------------------
    for email, incomes in DEMO_INCOME.items():
        uid = user_map[email]
        for income_data in incomes:
            income = Income(user_id=uid, **income_data)
            session.add(income)
        print(f"  [created] {len(incomes)} income sources for {email}")

    # -- Expenses ------------------------------------------------------------
    for email, expenses in DEMO_EXPENSES.items():
        uid = user_map[email]
        for expense_data in expenses:
            expense = Expense(user_id=uid, **expense_data)
            session.add(expense)
        print(f"  [created] {len(expenses)} expenses for {email}")

    await session.commit()
    print("\nSeeding complete.")


async def main() -> None:
    """Entry point for the seeder script."""
    print("DebtSense Database Seeder")
    print("=" * 40)

    # Ensure tables exist (useful for local dev without running migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        await seed(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
