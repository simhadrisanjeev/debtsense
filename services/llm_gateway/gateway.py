"""
LLM Gateway — a thin facade over the backend's LLM client.

This module re-exports the core LLM client and wraps it with
request/response logging middleware so that every LLM interaction
is auditable without touching the inner client code.

Usage::

    from services.llm_gateway.gateway import llm_gateway

    answer = await llm_gateway.complete([
        {"role": "user", "content": "How should I pay off my debts?"}
    ])
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import structlog

from app.modules.ai_advisor.llm_client import (
    LLMClient,
    LLMClientWithFallback,
    LLMError,
    LLMProvider,
    get_llm_client,
)

logger = structlog.get_logger(__name__)


class LLMGateway:
    """Logging middleware wrapper around :class:`LLMClientWithFallback`.

    Every call to :meth:`complete` is assigned a unique ``request_id``
    and logs the request metadata (message count, token estimate) and
    response metadata (latency, response length, errors).
    """

    def __init__(self, client: LLMClientWithFallback | None = None) -> None:
        self._client = client or get_llm_client()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Send a chat-completion request with full observability logging.

        Parameters
        ----------
        messages : list[dict[str, str]]
            Chat messages in ``{"role": ..., "content": ...}`` format.
        metadata : dict[str, Any], optional
            Arbitrary key-value pairs attached to the log entries
            (e.g. ``user_id``, ``module``).

        Returns
        -------
        str
            The LLM's text response.

        Raises
        ------
        LLMError
            If all configured providers fail.
        """
        request_id = str(uuid.uuid4())
        meta = metadata or {}
        log = logger.bind(request_id=request_id, **meta)

        # --- request logging ---
        total_chars = sum(len(m.get("content", "")) for m in messages)
        log.info(
            "llm_gateway.request",
            message_count=len(messages),
            total_chars=total_chars,
            provider=self._client.primary.provider.value,
        )

        start = time.monotonic()
        try:
            response = await self._client.complete(messages)
            elapsed = time.monotonic() - start

            # --- response logging ---
            log.info(
                "llm_gateway.response",
                latency_ms=round(elapsed * 1000, 1),
                response_length=len(response),
            )
            return response

        except LLMError as exc:
            elapsed = time.monotonic() - start
            log.error(
                "llm_gateway.error",
                latency_ms=round(elapsed * 1000, 1),
                error=str(exc),
            )
            raise

    # ------------------------------------------------------------------
    # Convenience re-exports
    # ------------------------------------------------------------------

    @property
    def primary(self) -> LLMClient:
        """Access the primary LLM client."""
        return self._client.primary

    @property
    def fallback(self) -> LLMClient | None:
        """Access the fallback LLM client (may be ``None``)."""
        return self._client.fallback


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

llm_gateway = LLMGateway()

# Re-exports for convenience
__all__ = [
    "LLMClient",
    "LLMClientWithFallback",
    "LLMError",
    "LLMGateway",
    "LLMProvider",
    "get_llm_client",
    "llm_gateway",
]
