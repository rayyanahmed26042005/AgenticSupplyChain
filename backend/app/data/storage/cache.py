"""
In-memory cache with TTL support.
Falls back to dict-based cache when Redis is unavailable.
"""

from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Simple in-memory cache with TTL expiration."""

    def __init__(self, default_ttl: int = 300):
        self._store: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Get value by key, returning None if expired or missing."""
        if key not in self._store:
            return None

        entry = self._store[key]
        if datetime.now() > entry["expires_at"]:
            del self._store[key]
            return None

        return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value with optional TTL in seconds."""
        ttl = ttl or self.default_ttl
        self._store[key] = {
            "value": value,
            "expires_at": datetime.now() + timedelta(seconds=ttl),
            "created_at": datetime.now().isoformat(),
        }

    def delete(self, key: str):
        """Delete a cache entry."""
        self._store.pop(key, None)

    def clear(self):
        """Clear all cache entries."""
        self._store.clear()

    def keys(self):
        """Get all non-expired keys."""
        now = datetime.now()
        return [k for k, v in self._store.items() if now <= v["expires_at"]]

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = datetime.now()
        total = len(self._store)
        expired = sum(1 for v in self._store.values() if now > v["expires_at"])
        return {
            "total_entries": total,
            "active_entries": total - expired,
            "expired_entries": expired,
        }


# Global cache instance
cache = InMemoryCache()
