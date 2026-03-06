"""
Async Redis client wrapper for caching operations.

Provides a connection pool, typed helpers for get/set/delete, and
JSON-aware convenience functions.  All functions are coroutine-safe and
designed to be called from any async context (FastAPI routes, background
tasks, etc.).
"""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Connection pool & client (module-level singletons)
# ---------------------------------------------------------------------------

redis_pool: aioredis.ConnectionPool = aioredis.ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=20,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_keepalive=True,
    retry_on_timeout=True,
)

redis_client: aioredis.Redis = aioredis.Redis(connection_pool=redis_pool)


# ---------------------------------------------------------------------------
# Lifecycle helpers (call from FastAPI lifespan)
# ---------------------------------------------------------------------------

async def redis_ping() -> bool:
    """Return *True* if the Redis server is reachable."""
    try:
        return await redis_client.ping()
    except (aioredis.ConnectionError, aioredis.TimeoutError) as exc:
        logger.error("redis.ping_failed", error=str(exc))
        return False


async def redis_close() -> None:
    """Gracefully shut down the Redis connection pool."""
    await redis_client.aclose()
    await redis_pool.disconnect()
    logger.info("redis.connection_closed")


# ---------------------------------------------------------------------------
# Primitive helpers
# ---------------------------------------------------------------------------

async def cache_get(key: str) -> str | None:
    """Fetch a cached string value by *key*.

    Returns ``None`` when the key does not exist or on connection errors.
    """
    try:
        return await redis_client.get(key)
    except (aioredis.ConnectionError, aioredis.TimeoutError) as exc:
        logger.warning("redis.get_failed", key=key, error=str(exc))
        return None


async def cache_set(key: str, value: str, ttl: int = 300) -> bool:
    """Store a string *value* under *key* with an expiry of *ttl* seconds.

    Returns ``True`` on success, ``False`` on connection errors.
    """
    try:
        await redis_client.set(key, value, ex=ttl)
        return True
    except (aioredis.ConnectionError, aioredis.TimeoutError) as exc:
        logger.warning("redis.set_failed", key=key, error=str(exc))
        return False


async def cache_delete(key: str) -> bool:
    """Remove a single *key* from the cache.

    Returns ``True`` if the key was deleted, ``False`` otherwise.
    """
    try:
        removed = await redis_client.delete(key)
        return removed > 0
    except (aioredis.ConnectionError, aioredis.TimeoutError) as exc:
        logger.warning("redis.delete_failed", key=key, error=str(exc))
        return False


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

async def cache_get_json(key: str) -> Any | None:
    """Fetch and JSON-decode the value stored under *key*.

    Returns the decoded Python object, or ``None`` when the key is missing
    or deserialization fails.
    """
    raw = await cache_get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("redis.json_decode_failed", key=key, error=str(exc))
        return None


async def cache_set_json(
    key: str,
    value: Any,
    ttl: int = 300,
) -> bool:
    """JSON-encode *value* and store it under *key* with *ttl* seconds expiry."""
    try:
        serialized = json.dumps(value, default=str)
    except (TypeError, ValueError) as exc:
        logger.warning("redis.json_encode_failed", key=key, error=str(exc))
        return False
    return await cache_set(key, serialized, ttl=ttl)
