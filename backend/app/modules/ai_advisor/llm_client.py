"""
Provider-agnostic LLM client.

Supports OpenAI and Anthropic APIs with automatic fallback.
"""

from __future__ import annotations

import json
from enum import Enum

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = structlog.get_logger()


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class LLMError(Exception):
    """Raised when an LLM API call fails after retries."""


class LLMClient:
    """Provider-agnostic LLM client with retry and fallback support."""

    # API endpoint mapping
    _ENDPOINTS: dict[LLMProvider, str] = {
        LLMProvider.OPENAI: "https://api.openai.com/v1/chat/completions",
        LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1/messages",
        LLMProvider.LOCAL: "http://localhost:11434/api/chat",
    }

    def __init__(
        self,
        provider: LLMProvider,
        api_key: str,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> None:
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError)),
        reraise=True,
    )
    async def complete(self, messages: list[dict[str, str]]) -> str:
        """Send a chat completion request to the configured LLM provider."""
        # Fail fast if no API key for cloud providers
        if not self.api_key and self.provider != LLMProvider.LOCAL:
            raise LLMError(f"No API key configured for {self.provider.value} provider")

        handler = {
            LLMProvider.OPENAI: self._complete_openai,
            LLMProvider.ANTHROPIC: self._complete_anthropic,
            LLMProvider.LOCAL: self._complete_local,
        }[self.provider]
        return await handler(messages)

    async def _complete_openai(self, messages: list[dict[str, str]]) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self._ENDPOINTS[LLMProvider.OPENAI],
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _complete_anthropic(self, messages: list[dict[str, str]]) -> str:
        # Anthropic separates system prompt from messages
        system = ""
        filtered: list[dict[str, str]] = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                filtered.append(msg)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self._ENDPOINTS[LLMProvider.ANTHROPIC],
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "system": system,
                    "messages": filtered,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    async def _complete_local(self, messages: list[dict[str, str]]) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self._ENDPOINTS[LLMProvider.LOCAL],
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": self.temperature},
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]


class LLMClientWithFallback:
    """Wraps a primary and optional fallback LLM client."""

    def __init__(self, primary: LLMClient, fallback: LLMClient | None = None) -> None:
        self.primary = primary
        self.fallback = fallback

    async def complete(self, messages: list[dict[str, str]]) -> str:
        try:
            return await self.primary.complete(messages)
        except Exception as primary_err:
            logger.warning(
                "llm.primary_failed",
                provider=self.primary.provider.value,
                error=str(primary_err),
            )
            if self.fallback:
                logger.info("llm.falling_back", provider=self.fallback.provider.value)
                try:
                    return await self.fallback.complete(messages)
                except Exception as fallback_err:
                    raise LLMError(
                        f"Both LLM providers failed. Primary: {primary_err}, Fallback: {fallback_err}"
                    ) from fallback_err
            raise LLMError(f"LLM provider failed: {primary_err}") from primary_err


def get_llm_client() -> LLMClientWithFallback:
    """Factory: build an LLM client from application settings."""
    primary = LLMClient(
        provider=LLMProvider(settings.LLM_PROVIDER),
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
        max_tokens=settings.LLM_MAX_TOKENS,
        temperature=settings.LLM_TEMPERATURE,
    )

    fallback = None
    if settings.LLM_FALLBACK_PROVIDER and settings.LLM_FALLBACK_API_KEY:
        fallback = LLMClient(
            provider=LLMProvider(settings.LLM_FALLBACK_PROVIDER),
            api_key=settings.LLM_FALLBACK_API_KEY,
            model=settings.LLM_FALLBACK_MODEL,
        )

    return LLMClientWithFallback(primary=primary, fallback=fallback)
