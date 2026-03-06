"""
Celery application configuration for DebtSense background tasks.

Uses Redis as both the message broker and result backend.  The app
auto-discovers task modules from the backend package so that new
task files are picked up without manual registration.
"""

from celery import Celery

from app.core.config import settings

# ---------------------------------------------------------------------------
# Celery application instance
# ---------------------------------------------------------------------------

celery_app = Celery(
    "debtsense",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,

    # Reliability — workers acknowledge *after* task completes, preventing
    # data loss when a worker is killed mid-execution.
    task_acks_late=True,

    # Each worker fetches only one task at a time so that long-running tasks
    # do not block other workers from picking up work.
    worker_prefetch_multiplier=1,

    # Result expiry — keep results for 24 hours then auto-clean.
    result_expires=86400,

    # Retry policy for broker connection on startup.
    broker_connection_retry_on_startup=True,

    # Task-level defaults
    task_soft_time_limit=300,   # 5 min soft limit (raises SoftTimeLimitExceeded)
    task_time_limit=360,        # 6 min hard limit (kills the worker process)
    task_reject_on_worker_lost=True,

    # Rate limiting per-task (can be overridden per-task with @app.task(rate_limit=...))
    task_default_rate_limit="60/m",
)

# ---------------------------------------------------------------------------
# Auto-discover task modules inside the backend app
# ---------------------------------------------------------------------------

celery_app.autodiscover_tasks(
    [
        "services.queue",
        "app.modules.ai_advisor",
        "app.modules.financial_engine",
    ],
)
