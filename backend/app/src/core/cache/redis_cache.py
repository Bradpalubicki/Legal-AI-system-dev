"""
Redis Cache Service

Provides caching functionality using Redis for improved performance.
Supports TTL, cache invalidation, and common caching patterns.
"""

import json
import logging
import hashlib
from typing import Any, Optional, Callable, Dict, List
from functools import wraps
from datetime import timedelta
import os

try:
    import redis
    from redis import Redis, ConnectionPool
    REDIS_AVAILABLE = True

    # Check if we should use fake redis
    USE_FAKE_REDIS = os.getenv('USE_FAKE_REDIS', 'false').lower() == 'true'
    if USE_FAKE_REDIS:
        try:
            import fakeredis
            FAKEREDIS_AVAILABLE = True
        except ImportError:
            FAKEREDIS_AVAILABLE = False
            logging.warning("fakeredis not installed. Install with: pip install fakeredis")
    else:
        FAKEREDIS_AVAILABLE = False

except ImportError:
    REDIS_AVAILABLE = False
    FAKEREDIS_AVAILABLE = False
    logging.warning("redis package not installed. Install with: pip install redis")

logger = logging.getLogger(__name__)


# =============================================================================
# REDIS CONNECTION
# =============================================================================

class RedisConnectionManager:
    """Manages Redis connection pool and provides singleton access"""

    _instance = None
    _redis_client: Optional[Redis] = None
    _connection_pool: Optional[ConnectionPool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Redis connection from environment variables"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - caching disabled")
            return

        if self._redis_client is not None:
            return  # Already initialized

        # Redis configuration from environment
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))
        redis_password = os.getenv('REDIS_PASSWORD', None)
        redis_max_connections = int(os.getenv('REDIS_MAX_CONNECTIONS', 50))

        try:
            # Use fakeredis if enabled
            if USE_FAKE_REDIS and FAKEREDIS_AVAILABLE:
                import fakeredis
                self._redis_client = fakeredis.FakeRedis(decode_responses=True)
                logger.info("✅ Redis connected: In-Memory FakeRedis (development mode)")
            else:
                # Create connection pool for real Redis
                self._connection_pool = ConnectionPool(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    max_connections=redis_max_connections,
                    decode_responses=True,  # Auto-decode responses to strings
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                )

                # Create Redis client
                self._redis_client = Redis(connection_pool=self._connection_pool)

                # Test connection
                self._redis_client.ping()

                logger.info(f"✅ Redis connected: {redis_host}:{redis_port} (db={redis_db})")

        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self._redis_client = None
            self._connection_pool = None

    def get_client(self) -> Optional[Redis]:
        """Get Redis client instance"""
        return self._redis_client

    def is_available(self) -> bool:
        """Check if Redis is available"""
        if not REDIS_AVAILABLE or self._redis_client is None:
            return False

        try:
            self._redis_client.ping()
            return True
        except Exception:
            return False

    def close(self):
        """Close Redis connection"""
        if self._connection_pool:
            self._connection_pool.disconnect()
            logger.info("Redis connection closed")


# Global Redis manager instance
_redis_manager = RedisConnectionManager()


def get_redis_client() -> Optional[Redis]:
    """Get Redis client instance"""
    return _redis_manager.get_client()


# =============================================================================
# CACHE SERVICE
# =============================================================================

class CacheService:
    """
    Redis cache service with common caching operations.

    Features:
    - Set/get with TTL
    - JSON serialization
    - Cache invalidation patterns
    - Bulk operations
    - Cache stats
    """

    def __init__(self):
        self.redis = get_redis_client()

    def is_available(self) -> bool:
        """Check if caching is available"""
        return _redis_manager.is_available()

    def _make_key(self, key: str, prefix: str = "cache") -> str:
        """Generate cache key with namespace prefix"""
        return f"{prefix}:{key}"

    def _serialize(self, value: Any) -> str:
        """Serialize value to JSON string"""
        try:
            return json.dumps(value, default=str)
        except (TypeError, ValueError) as e:
            logger.error(f"Serialization error: {e}")
            raise

    def _deserialize(self, value: str) -> Any:
        """Deserialize JSON string to Python object"""
        try:
            return json.loads(value)
        except (TypeError, ValueError) as e:
            logger.error(f"Deserialization error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Basic Operations
    # -------------------------------------------------------------------------

    def get(self, key: str, prefix: str = "cache") -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key
            prefix: Key namespace prefix

        Returns:
            Cached value or None if not found
        """
        if not self.is_available():
            return None

        try:
            cache_key = self._make_key(key, prefix)
            value = self.redis.get(cache_key)

            if value is None:
                return None

            return self._deserialize(value)

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        prefix: str = "cache"
    ) -> bool:
        """
        Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = no expiration)
            prefix: Key namespace prefix

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False

        try:
            cache_key = self._make_key(key, prefix)
            serialized = self._serialize(value)

            if ttl:
                self.redis.setex(cache_key, ttl, serialized)
            else:
                self.redis.set(cache_key, serialized)

            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str, prefix: str = "cache") -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key
            prefix: Key namespace prefix

        Returns:
            True if deleted, False otherwise
        """
        if not self.is_available():
            return False

        try:
            cache_key = self._make_key(key, prefix)
            self.redis.delete(cache_key)
            return True

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def exists(self, key: str, prefix: str = "cache") -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key
            prefix: Key namespace prefix

        Returns:
            True if exists, False otherwise
        """
        if not self.is_available():
            return False

        try:
            cache_key = self._make_key(key, prefix)
            return bool(self.redis.exists(cache_key))

        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False

    # -------------------------------------------------------------------------
    # Pattern-Based Operations
    # -------------------------------------------------------------------------

    def delete_pattern(self, pattern: str, prefix: str = "cache") -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "user:*")
            prefix: Key namespace prefix

        Returns:
            Number of keys deleted
        """
        if not self.is_available():
            return 0

        try:
            full_pattern = self._make_key(pattern, prefix)
            keys = self.redis.keys(full_pattern)

            if keys:
                return self.redis.delete(*keys)
            return 0

        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
            return 0

    def get_keys_by_pattern(self, pattern: str, prefix: str = "cache") -> List[str]:
        """
        Get all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "user:*")
            prefix: Key namespace prefix

        Returns:
            List of matching keys
        """
        if not self.is_available():
            return []

        try:
            full_pattern = self._make_key(pattern, prefix)
            keys = self.redis.keys(full_pattern)

            # Remove prefix from keys
            prefix_len = len(f"{prefix}:")
            return [key[prefix_len:] for key in keys]

        except Exception as e:
            logger.error(f"Cache get keys error: {e}")
            return []

    # -------------------------------------------------------------------------
    # Hash Operations
    # -------------------------------------------------------------------------

    def hset(self, key: str, field: str, value: Any, prefix: str = "cache") -> bool:
        """Set field in hash"""
        if not self.is_available():
            return False

        try:
            cache_key = self._make_key(key, prefix)
            serialized = self._serialize(value)
            self.redis.hset(cache_key, field, serialized)
            return True

        except Exception as e:
            logger.error(f"Cache hset error: {e}")
            return False

    def hget(self, key: str, field: str, prefix: str = "cache") -> Optional[Any]:
        """Get field from hash"""
        if not self.is_available():
            return None

        try:
            cache_key = self._make_key(key, prefix)
            value = self.redis.hget(cache_key, field)

            if value is None:
                return None

            return self._deserialize(value)

        except Exception as e:
            logger.error(f"Cache hget error: {e}")
            return None

    def hgetall(self, key: str, prefix: str = "cache") -> Dict[str, Any]:
        """Get all fields from hash"""
        if not self.is_available():
            return {}

        try:
            cache_key = self._make_key(key, prefix)
            data = self.redis.hgetall(cache_key)

            return {k: self._deserialize(v) for k, v in data.items()}

        except Exception as e:
            logger.error(f"Cache hgetall error: {e}")
            return {}

    # -------------------------------------------------------------------------
    # Increment/Decrement
    # -------------------------------------------------------------------------

    def increment(self, key: str, amount: int = 1, prefix: str = "cache") -> int:
        """Increment numeric value"""
        if not self.is_available():
            return 0

        try:
            cache_key = self._make_key(key, prefix)
            return self.redis.incrby(cache_key, amount)

        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return 0

    def decrement(self, key: str, amount: int = 1, prefix: str = "cache") -> int:
        """Decrement numeric value"""
        if not self.is_available():
            return 0

        try:
            cache_key = self._make_key(key, prefix)
            return self.redis.decrby(cache_key, amount)

        except Exception as e:
            logger.error(f"Cache decrement error: {e}")
            return 0

    # -------------------------------------------------------------------------
    # Cache Stats
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.is_available():
            return {"available": False}

        try:
            info = self.redis.info("stats")
            memory = self.redis.info("memory")

            return {
                "available": True,
                "total_connections": info.get("total_connections_received", 0),
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                ),
                "used_memory_human": memory.get("used_memory_human", "0B"),
                "used_memory_peak_human": memory.get("used_memory_peak_human", "0B"),
            }

        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"available": False, "error": str(e)}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def flush_all(self) -> bool:
        """
        Flush all cache data (USE WITH CAUTION!)

        Returns:
            True if successful
        """
        if not self.is_available():
            return False

        try:
            self.redis.flushdb()
            logger.warning("⚠️  Cache flushed - all data cleared")
            return True

        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False


# Global cache service instance
cache = CacheService()


# =============================================================================
# CACHE DECORATORS
# =============================================================================

def cached(
    ttl: int = 300,
    prefix: str = "cache",
    key_func: Optional[Callable] = None
):
    """
    Decorator for caching function results.

    Args:
        ttl: Time-to-live in seconds (default: 5 minutes)
        prefix: Cache key prefix
        key_func: Custom function to generate cache key from args

    Example:
        @cached(ttl=600, prefix="users")
        def get_user(user_id: int):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(func.__name__, args, kwargs)

            # Try to get from cache
            cached_value = cache.get(cache_key, prefix=prefix)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value

            # Cache miss - execute function
            logger.debug(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl=ttl, prefix=prefix)

            return result

        return wrapper
    return decorator


def cache_invalidate(pattern: str, prefix: str = "cache"):
    """
    Decorator to invalidate cache after function execution.

    Args:
        pattern: Pattern of keys to invalidate (e.g., "user:*")
        prefix: Cache key prefix

    Example:
        @cache_invalidate(pattern="user:*", prefix="users")
        def update_user(user_id: int, data: dict):
            # Update user in database
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute function
            result = func(*args, **kwargs)

            # Invalidate cache
            deleted = cache.delete_pattern(pattern, prefix=prefix)
            logger.debug(f"Cache invalidated: {pattern} ({deleted} keys)")

            return result

        return wrapper
    return decorator


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate cache key from function name and arguments"""
    # Create a stable representation of args and kwargs
    key_data = {
        "func": func_name,
        "args": args,
        "kwargs": sorted(kwargs.items()) if kwargs else None
    }

    # Generate hash
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_str.encode()).hexdigest()

    return f"{func_name}:{key_hash}"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'CacheService',
    'cache',
    'cached',
    'cache_invalidate',
    'get_redis_client',
]
