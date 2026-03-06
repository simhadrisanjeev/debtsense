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

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
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
    from app.core.database import engine  # noqa: F401

    # Initialize Redis connection pool
    from services.cache.redis_client import redis_pool  # noqa: F401

    yield

    # ----- Shutdown -----
    from app.core.database import engine as db_engine

    await db_engine.dispose()
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

    # --- Health Check ---
    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "healthy", "version": settings.APP_VERSION}

    return app


app = create_app()
