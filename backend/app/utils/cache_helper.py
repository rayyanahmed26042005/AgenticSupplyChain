"""
Cache helper utilities.
"""

from app.data.storage.cache import cache


def get_cached(key: str, factory=None, ttl: int = None):
    """Get cached value or compute and cache it."""
    value = cache.get(key)
    if value is not None:
        return value
    if factory:
        value = factory()
        cache.set(key, value, ttl)
        return value
    return None


def invalidate(key: str):
    """Invalidate a cache entry."""
    cache.delete(key)
