"""
Centralized Cache Module using cachetools.
Provides TTLCache with stale-data fallback for all backend services.
"""

from cachetools import TTLCache
from typing import Any, Optional
import threading


class ServiceCache:
    """
    A thread-safe cache with per-key TTL support and stale-data fallback.
    
    Usage:
        cache = ServiceCache(maxsize=128)
        cache.set("funding", data, ttl=60)
        result = cache.get("funding")
    """

    def __init__(self, maxsize: int = 256):
        self._lock = threading.Lock()
        self._maxsize = maxsize
        self._caches: dict[str, TTLCache] = {}
        # Stale fallback: keeps last known good value even after TTL expires
        self._fallback: dict[str, Any] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get cached value or None if expired/missing."""
        with self._lock:
            ttl_cache = self._caches.get(key)
            if ttl_cache and key in ttl_cache:
                return ttl_cache[key]
        return None

    def get_with_fallback(self, key: str) -> Optional[Any]:
        """Get cached value, falling back to stale data if TTL expired."""
        result = self.get(key)
        if result is not None:
            return result
        # Return stale data as fallback
        with self._lock:
            return self._fallback.get(key)

    def set(self, key: str, value: Any, ttl: int) -> None:
        """Set a value with a specific TTL (in seconds)."""
        with self._lock:
            # Create or replace TTLCache for this key
            self._caches[key] = TTLCache(maxsize=1, ttl=ttl)
            self._caches[key][key] = value
            # Also store in fallback
            self._fallback[key] = value

    def is_valid(self, key: str) -> bool:
        """Check if a key has a non-expired value."""
        with self._lock:
            ttl_cache = self._caches.get(key)
            return ttl_cache is not None and key in ttl_cache

    def invalidate(self, key: str) -> None:
        """Force-expire a cached key."""
        with self._lock:
            ttl_cache = self._caches.get(key)
            if ttl_cache and key in ttl_cache:
                del ttl_cache[key]

    def clear(self) -> None:
        """Clear all caches."""
        with self._lock:
            self._caches.clear()
            self._fallback.clear()


# Singleton instances for each service domain
home_cache = ServiceCache(maxsize=64)
market_cache = ServiceCache(maxsize=64)
news_cache = ServiceCache(maxsize=64)
