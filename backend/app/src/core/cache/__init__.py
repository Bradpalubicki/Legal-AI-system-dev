"""
Cache Module

Provides Redis caching functionality for improved performance.
"""

from .redis_cache import (
    CacheService,
    cache,
    cached,
    cache_invalidate,
    get_redis_client,
)

__all__ = [
    'CacheService',
    'cache',
    'cached',
    'cache_invalidate',
    'get_redis_client',
]
