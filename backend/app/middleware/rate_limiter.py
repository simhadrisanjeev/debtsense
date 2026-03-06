"""
Redis-backed sliding-window rate limiter middleware.

Falls back to an in-memory counter if Redis is unavailable.
"""

from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# In-memory fallback (per-process; use Redis in production)
_buckets: dict[str, list[float]] = defaultdict(list)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/api/docs", "/api/openapi.json"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate:{client_ip}"
        now = time.time()
        window = 60.0  # 1-minute window

        try:
            from services.cache.redis_client import redis_client

            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, int(window))
            results = await pipe.execute()
            request_count = results[2]
        except Exception:
            # Fallback to in-memory
            _buckets[key] = [t for t in _buckets[key] if t > now - window]
            _buckets[key].append(now)
            request_count = len(_buckets[key])

        if request_count > settings.RATE_LIMIT_PER_MINUTE:
            logger.warning("rate_limit_exceeded", client_ip=client_ip, count=request_count)
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests"}},
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, settings.RATE_LIMIT_PER_MINUTE - request_count)
        )
        return response
