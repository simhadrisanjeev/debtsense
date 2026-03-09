"""
DebtSense — FastAPI Application Factory

Production-ready setup with:
- CORS middleware
- Rate limiting
- Structured logging
- Health checks
- API versioning
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import sys
from pathlib import Path

# Ensure the monorepo root is on sys.path so ``services.*`` imports resolve.
_monorepo_root = str(Path(__file__).resolve().parents[2])
if _monorepo_root not in sys.path:
    sys.path.insert(0, _monorepo_root)

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.core.router import api_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown."""
    # ----- Startup -----
    setup_logging()
    logger.info("debtsense.startup", version=settings.APP_VERSION, env=settings.APP_ENV)

    # Initialize database connection pool
    try:
        from app.core.database import engine  # noqa: F401

        # Auto-create tables for SQLite (local dev without migrations)
        if settings.USE_SQLITE:
            from app.core.base_model import Base
            # Import all models so Base.metadata knows about them
            import app.modules.users.models  # noqa: F401
            import app.modules.auth.models  # noqa: F401
            import app.modules.debts.models  # noqa: F401
            import app.modules.income.models  # noqa: F401
            import app.modules.expenses.models  # noqa: F401
            import app.modules.analytics.models  # noqa: F401
            import app.modules.notifications.models  # noqa: F401

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("debtsense.sqlite_tables_created")
    except Exception as exc:
        logger.warning("debtsense.db_init_skipped", error=str(exc))

    # Initialize Redis connection pool
    try:
        from services.cache.redis_client import redis_pool  # noqa: F401
    except Exception as exc:
        logger.warning("debtsense.redis_init_skipped", error=str(exc))

    yield

    # ----- Shutdown -----
    try:
        from app.core.database import engine as db_engine
        await db_engine.dispose()
    except Exception:
        pass
    logger.info("debtsense.shutdown")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/api/docs" if settings.APP_DEBUG else None,
        redoc_url="/api/redoc" if settings.APP_DEBUG else None,
        openapi_url="/api/openapi.json" if settings.APP_DEBUG else None,
        lifespan=lifespan,
    )

    # --- Middleware (order matters: outermost first) ---
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(RateLimiterMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS_LIST,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routes ---
    app.include_router(api_router, prefix=settings.API_PREFIX)

    # --- Exception Handlers ---
    register_exception_handlers(app)

    # --- Health Check ---
    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "healthy", "version": settings.APP_VERSION}

    return app


app = create_app()
