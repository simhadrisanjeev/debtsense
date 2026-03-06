"""
Background tasks executed by Celery workers.

Each task is idempotent and designed to be safely retried.  Heavy I/O
(database queries, LLM calls) is performed inside the task body so the
API layer can return immediately.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from services.queue.celery_app import celery_app

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_sync_session() -> Session:
    """Build a *synchronous* SQLAlchemy session for use inside Celery workers.

    Celery tasks run in a sync context, so we cannot reuse the async
    session factory from ``app.core.database``.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings

    engine = create_engine(
        settings.DATABASE_URL_SYNC,
        pool_size=5,
        max_overflow=2,
        pool_pre_ping=True,
    )
    factory = sessionmaker(bind=engine)
    return factory()


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="tasks.send_notification_email",
)
def send_notification_email(
    self,
    user_id: str,
    subject: str,
    body: str,
) -> dict:
    """Send a transactional notification email to a user.

    The task looks up the user's email address from the database, then
    delegates to the configured SMTP transport.  On transient failures
    the task is retried up to three times with a 60-second back-off.

    Parameters
    ----------
    user_id : str
        UUID of the target user (string-serialized for JSON transport).
    subject : str
        Email subject line.
    body : str
        Plain-text email body.

    Returns
    -------
    dict
        ``{"status": "sent", "user_id": ..., "subject": ...}``
    """
    log = logger.bind(task="send_notification_email", user_id=user_id)
    log.info("task.started")

    session = _get_sync_session()
    try:
        from app.modules.users.models import User

        user = session.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        ).scalar_one_or_none()

        if user is None:
            log.warning("task.user_not_found")
            return {"status": "skipped", "reason": "user_not_found"}

        # ------------------------------------------------------------------
        # TODO: Replace with real SMTP / SES / SendGrid integration.
        # For now we log the email that *would* be sent.
        # ------------------------------------------------------------------
        log.info(
            "task.email_sent",
            to=user.email,
            subject=subject,
            body_length=len(body),
        )

        return {
            "status": "sent",
            "user_id": user_id,
            "subject": subject,
        }
    except Exception as exc:
        log.error("task.failed", error=str(exc))
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    name="tasks.generate_monthly_snapshot",
)
def generate_monthly_snapshot(self, user_id: str) -> dict:
    """Generate a point-in-time financial snapshot for a user.

    Aggregates the user's debts, income, and expenses into a single
    ``monthly_snapshots`` row that powers trend charts on the frontend.

    Parameters
    ----------
    user_id : str
        UUID of the target user (string-serialized).

    Returns
    -------
    dict
        ``{"status": "created", "user_id": ..., "snapshot_date": ...}``
    """
    log = logger.bind(task="generate_monthly_snapshot", user_id=user_id)
    log.info("task.started")

    session = _get_sync_session()
    try:
        from app.modules.debts.models import Debt
        from app.modules.income.models import Income
        from app.modules.expenses.models import Expense

        uid = uuid.UUID(user_id)
        now = datetime.now(timezone.utc)

        # Aggregate debts
        debts = session.execute(
            select(Debt).where(Debt.user_id == uid, Debt.is_active.is_(True))
        ).scalars().all()
        total_debt = sum(float(d.current_balance) for d in debts)
        total_minimum = sum(float(d.minimum_payment) for d in debts)

        # Aggregate income
        incomes = session.execute(
            select(Income).where(Income.user_id == uid, Income.is_active.is_(True))
        ).scalars().all()
        total_income = sum(float(i.amount) for i in incomes)

        # Aggregate expenses
        expenses = session.execute(
            select(Expense).where(Expense.user_id == uid, Expense.is_active.is_(True))
        ).scalars().all()
        total_expenses = sum(float(e.amount) for e in expenses)

        snapshot_data = {
            "user_id": user_id,
            "snapshot_date": now.date().isoformat(),
            "total_debt": total_debt,
            "total_minimum_payments": total_minimum,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "disposable_income": total_income - total_expenses - total_minimum,
            "debt_count": len(debts),
        }

        # ------------------------------------------------------------------
        # TODO: Persist snapshot_data to monthly_snapshots table once the
        # ORM model is created.  For now we return the computed dict.
        # ------------------------------------------------------------------
        log.info("task.snapshot_computed", **snapshot_data)

        return {"status": "created", **snapshot_data}
    except Exception as exc:
        log.error("task.failed", error=str(exc))
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    name="tasks.process_ai_advice",
)
def process_ai_advice(
    self,
    request_id: str,
    question: str,
    context: dict,
) -> dict:
    """Run an AI advisor query as a background job.

    This is used when the caller prefers an async (polling) workflow
    rather than waiting for the LLM response inline.  The result is
    stored in the Celery result backend and can be retrieved via the
    ``request_id``.

    Parameters
    ----------
    request_id : str
        Unique identifier the caller can use to poll for results.
    question : str
        The user's natural-language question.
    context : dict
        Serialized financial context (debts, income, expenses, etc.).

    Returns
    -------
    dict
        ``{"status": "completed", "request_id": ..., "answer": ...}``
    """
    import asyncio

    log = logger.bind(task="process_ai_advice", request_id=request_id)
    log.info("task.started", question_length=len(question))

    try:
        from app.modules.ai_advisor.llm_client import get_llm_client
        from app.modules.ai_advisor.prompts import build_advice_messages  # type: ignore[import-untyped]

        llm = get_llm_client()

        messages = [
            {"role": "system", "content": (
                "You are DebtSense AI, a financial advisor specializing in "
                "debt repayment strategies.  Answer concisely and actionably."
            )},
            {"role": "user", "content": (
                f"Financial context:\n{context}\n\nQuestion: {question}"
            )},
        ]

        # Run the async LLM call inside the sync Celery worker.
        loop = asyncio.new_event_loop()
        try:
            answer = loop.run_until_complete(llm.complete(messages))
        finally:
            loop.close()

        log.info("task.completed", answer_length=len(answer))

        return {
            "status": "completed",
            "request_id": request_id,
            "answer": answer,
        }
    except Exception as exc:
        log.error("task.failed", error=str(exc))
        raise self.retry(exc=exc)
