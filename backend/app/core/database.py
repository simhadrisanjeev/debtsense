"""
Async SQLAlchemy engine and session factory.

Uses connection pooling tuned for high-throughput workloads.
Supports both PostgreSQL (production) and SQLite (local dev).
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

_engine_kwargs: dict = {
    "echo": settings.APP_DEBUG,
}

if settings.USE_SQLITE:
    # SQLite doesn't support pool_size/max_overflow; use StaticPool for dev
    from sqlalchemy.pool import StaticPool

    _engine_kwargs.update(
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    _engine_kwargs.update(
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
    )

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
