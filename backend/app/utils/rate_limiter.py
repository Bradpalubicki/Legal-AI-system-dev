"""
Legal AI System - Rate Limiter Utility
Redis-based rate limiting for API endpoints and features
"""

import asyncio
import redis.asyncio as redis
from typing import Optional
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    """Redis-based rate limiter for API and feature usage"""

    def __init__(self):
        self.redis_client = None
        self._initialized = False

    async def _ensure_connected(self):
        """Ensure Redis connection is established"""
        if not self._initialized:
            try:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self.redis_client.ping()
                self._initialized = True
                logger.info("Rate limiter Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis for rate limiting: {e}")
                self.redis_client = None

    async def get_count(self, key: str) -> int:
        """Get current count for a rate limit key"""
        try:
            await self._ensure_connected()
            if not self.redis_client:
                return 0

            count = await self.redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Rate limiter get_count failed: {e}")
            return 0

    async def increment(self, key: str, ttl: int = 3600) -> int:
        """Increment counter and set TTL"""
        try:
            await self._ensure_connected()
            if not self.redis_client:
                return 0

            # Use pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl)
            results = await pipe.execute()

            return results[0] if results else 0
        except Exception as e:
            logger.error(f"Rate limiter increment failed: {e}")
            return 0

    async def check_limit(self, key: str, limit: int, window: int = 3600) -> bool:
        """Check if under rate limit"""
        try:
            current = await self.get_count(key)
            return current < limit
        except Exception as e:
            logger.error(f"Rate limiter check_limit failed: {e}")
            return True  # Allow on error

    async def reset(self, key: str) -> bool:
        """Reset rate limit counter"""
        try:
            await self._ensure_connected()
            if not self.redis_client:
                return False

            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Rate limiter reset failed: {e}")
            return False