"""
Caching utilities for database query results.

Provides in-memory caching with TTL and LRU eviction for expensive database queries.
"""

import functools
import hashlib
import json
import time
from typing import Any, Callable, Dict, Optional, Tuple

from src.setup.extensions import logger


class QueryCache:
    """
    In-memory cache with TTL and LRU eviction.

    Features:
    - Time-to-live (TTL) expiration
    - Least Recently Used (LRU) eviction
    - Cache statistics
    - Configurable max size
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of cached items
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Tuple[Any, Optional[float]]] = {}
        self._access_times: Dict[str, float] = {}
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """
        Generate cache key from function name and arguments.

        Args:
            func_name: Function name
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        # Create stable representation of arguments
        key_parts = [func_name]

        # Add args
        for arg in args:
            if hasattr(arg, "__dict__"):
                # For objects, use their dict representation
                key_parts.append(str(sorted(arg.__dict__.items())))
            else:
                key_parts.append(str(arg))

        # Add kwargs
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")

        # Hash to create fixed-length key
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._stats["misses"] += 1
            return None

        value, expiry = self._cache[key]

        # Check if expired
        if expiry and time.time() > expiry:
            del self._cache[key]
            del self._access_times[key]
            self._stats["misses"] += 1
            return None

        # Update access time (for LRU)
        self._access_times[key] = time.time()
        self._stats["hits"] += 1
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default)
        """
        # Evict if at max size
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_lru()

        # Calculate expiry
        ttl = ttl if ttl is not None else self.default_ttl
        expiry = time.time() + ttl if ttl > 0 else None

        self._cache[key] = (value, expiry)
        self._access_times[key] = time.time()

    def _evict_lru(self):
        """Evict least recently used item."""
        if not self._access_times:
            return

        # Find LRU item
        lru_key = min(self._access_times, key=lambda k: self._access_times[k])

        # Remove it
        del self._cache[lru_key]
        del self._access_times[lru_key]
        self._stats["evictions"] += 1

    def clear(self):
        """Clear all cached items."""
        self._cache.clear()
        self._access_times.clear()

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with hits, misses, evictions, size, hit_rate
        """
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0

        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_rate": f"{hit_rate*100:.1f}%",
        }


# Global cache instance
_query_cache = QueryCache(max_size=500, default_ttl=300)


def cached_query(ttl: int = 300):
    """
    Decorator to cache query results.

    Args:
        ttl: Time-to-live in seconds (0 = no expiration)

    Usage:
        @cached_query(ttl=600)
        def expensive_query(arg1, arg2):
            return database_query(arg1, arg2)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _query_cache._generate_key(func.__name__, args, kwargs)

            # Try to get from cache
            result = _query_cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache HIT for {func.__name__}")
                return result

            # Execute function
            logger.debug(f"Cache MISS for {func.__name__}")
            result = func(*args, **kwargs)

            # Store in cache
            _query_cache.set(cache_key, result, ttl=ttl)

            return result

        # Add cache control methods
        wrapper.clear_cache = _query_cache.clear  # type: ignore[attr-defined]
        wrapper.get_stats = _query_cache.get_stats  # type: ignore[attr-defined]

        return wrapper

    return decorator


def get_cache_stats() -> dict:
    """
    Get global cache statistics.

    Returns:
        Cache statistics dictionary
    """
    return _query_cache.get_stats()


def clear_cache():
    """Clear all cached queries."""
    _query_cache.clear()
    logger.info("Query cache cleared")
