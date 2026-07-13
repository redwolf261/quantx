"""
Simple caching layer for simulation results.
Uses in-memory dict by default. Can be swapped for Redis.
"""
from __future__ import annotations
import hashlib
import json
import time
from typing import Any, Optional
import structlog

log = structlog.get_logger()


class SimulationCache:
    """
    Cache for simulation results keyed by parameter hash.
    
    In-memory implementation with TTL. Swap for Redis in production.
    """

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 100):
        self._cache: dict[str, tuple[float, Any]] = {}  # key -> (expiry, value)
        self._ttl = ttl_seconds
        self._max_size = max_size

    def _make_key(self, params: dict) -> str:
        """Create a deterministic hash from simulation parameters."""
        # Sort keys for deterministic ordering
        serialized = json.dumps(params, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def get(self, params: dict) -> Optional[Any]:
        """Get cached result if it exists and hasn't expired."""
        key = self._make_key(params)
        if key not in self._cache:
            return None

        expiry, value = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            return None

        log.debug("cache_hit", key=key[:12])
        return value

    def set(self, params: dict, value: Any) -> None:
        """Cache a simulation result."""
        key = self._make_key(params)
        expiry = time.time() + self._ttl

        # Evict oldest if at capacity
        if len(self._cache) >= self._max_size and key not in self._cache:
            oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]

        self._cache[key] = (expiry, value)
        log.debug("cache_set", key=key[:12], ttl=self._ttl)

    def invalidate(self, params: dict) -> None:
        """Remove a specific cached result."""
        key = self._make_key(params)
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cached results."""
        self._cache.clear()
        log.info("cache_cleared")


# Global cache instance
simulation_cache = SimulationCache()