"""
Service layer for the financial engine module.

Wraps :class:`FinancialEngine` with an in-memory TTL cache so that
identical requests within the cache window are served instantly without
re-running the simulation.  The cache key is derived from a stable hash
of the request parameters.

The cache is intentionally simple (no Redis dependency) — it lives in the
application process and is bounded by ``maxsize``.  For horizontally
scaled deployments, each worker will maintain its own cache, which is
acceptable because the computations are deterministic and pure.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import OrderedDict
from decimal import Decimal
from typing import Any, Sequence

import structlog

from app.modules.financial_engine.engine import FinancialEngine
from app.modules.financial_engine.schemas import (
    DebtInput,
    PayoffResult,
    PayoffStrategy,
    StrategyComparison,
)

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# TTL LRU cache
# ---------------------------------------------------------------------------

class _TTLCache:
    """Thread-safe, bounded, in-memory TTL cache.

    Parameters
    ----------
    maxsize:
        Maximum number of entries.  When exceeded the least-recently-used
        entry is evicted.
    ttl_seconds:
        Entries older than this are treated as expired.
    """

    def __init__(self, maxsize: int = 256, ttl_seconds: float = 300) -> None:
        self._maxsize = maxsize
        self._ttl = ttl_seconds
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            ts, value = entry
            if time.monotonic() - ts > self._ttl:
                # Expired
                del self._store[key]
                return None
            # Move to end (most recently used)
            self._store.move_to_end(key)
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (time.monotonic(), value)
            # Evict oldest if over capacity
            while len(self._store) > self._maxsize:
                self._store.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


# Module-level cache instances (shared across service instances).
_calc_cache = _TTLCache(maxsize=512, ttl_seconds=300)
_compare_cache = _TTLCache(maxsize=128, ttl_seconds=300)


# ---------------------------------------------------------------------------
# Cache-key helper
# ---------------------------------------------------------------------------

def _make_cache_key(
    debts: Sequence[DebtInput],
    extra_payment: Decimal,
    strategy: str | None = None,
) -> str:
    """Produce a deterministic hash from the request parameters.

    The key is a SHA-256 hex digest so it is compact and fixed-width.
    """
    payload: dict[str, Any] = {
        "debts": [
            {
                "name": d.name,
                "balance": str(d.balance),
                "interest_rate": str(d.interest_rate),
                "minimum_payment": str(d.minimum_payment),
            }
            for d in debts
        ],
        "extra_payment": str(extra_payment),
    }
    if strategy is not None:
        payload["strategy"] = strategy
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class FinancialEngineService:
    """Thin service wrapper around :class:`FinancialEngine`.

    Adds caching and structured logging.  This is the object that
    routers and other modules should interact with — never instantiate
    ``FinancialEngine`` directly from a router.
    """

    def __init__(self) -> None:
        self._engine = FinancialEngine()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate(
        self,
        debts: Sequence[DebtInput],
        strategy: PayoffStrategy,
        extra_payment: Decimal = Decimal("0"),
    ) -> PayoffResult:
        """Calculate payoff for a single strategy, with caching."""
        cache_key = _make_cache_key(debts, extra_payment, strategy.value)

        cached = _calc_cache.get(cache_key)
        if cached is not None:
            logger.debug(
                "financial_engine.cache_hit",
                strategy=strategy.value,
                cache="calculate",
            )
            return cached  # type: ignore[return-value]

        logger.info(
            "financial_engine.calculate",
            strategy=strategy.value,
            num_debts=len(debts),
            extra_payment=str(extra_payment),
        )

        result = self._engine.calculate_payoff(debts, strategy, extra_payment)
        _calc_cache.set(cache_key, result)
        return result

    def compare(
        self,
        debts: Sequence[DebtInput],
        extra_payment: Decimal = Decimal("0"),
    ) -> StrategyComparison:
        """Compare all strategies, with caching."""
        cache_key = _make_cache_key(debts, extra_payment)

        cached = _compare_cache.get(cache_key)
        if cached is not None:
            logger.debug(
                "financial_engine.cache_hit",
                cache="compare",
            )
            return cached  # type: ignore[return-value]

        logger.info(
            "financial_engine.compare",
            num_debts=len(debts),
            extra_payment=str(extra_payment),
        )

        result = self._engine.compare_strategies(debts, extra_payment)
        _compare_cache.set(cache_key, result)
        return result

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    @staticmethod
    def clear_caches() -> None:
        """Evict all cached results.  Useful in tests or admin endpoints."""
        _calc_cache.clear()
        _compare_cache.clear()
        logger.info("financial_engine.caches_cleared")
