"""
Research Cache

Advanced caching system for legal research with intelligent cache management,
multi-level storage, and performance optimization for API calls and results.
"""

import asyncio
import hashlib
import logging
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from uuid import UUID, uuid4

import aioredis
from pydantic import BaseModel

from .models import (
    ResearchQuery, SearchResult, LegalDocument, Citation,
    CitationValidationResult, ResearchProvider
)

logger = logging.getLogger(__name__)


class CacheKey(BaseModel):
    """Cache key structure"""
    key: str
    category: str  # search, document, citation, validation
    provider: Optional[ResearchProvider] = None
    hash_value: str
    created_at: datetime
    expires_at: Optional[datetime] = None


class CacheMetrics(BaseModel):
    """Cache performance metrics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_ratio: float = 0.0
    
    # Storage metrics
    total_entries: int = 0
    memory_usage_bytes: int = 0
    disk_usage_bytes: int = 0
    
    # Performance metrics
    average_retrieval_time_ms: float = 0.0
    average_storage_time_ms: float = 0.0
    
    # Eviction metrics
    evictions_count: int = 0
    expired_entries: int = 0
    
    last_updated: datetime = datetime.utcnow()


class CacheConfig(BaseModel):
    """Cache configuration"""
    # TTL settings (in seconds)
    search_ttl: int = 3600  # 1 hour
    document_ttl: int = 86400  # 24 hours
    citation_ttl: int = 604800  # 1 week
    validation_ttl: int = 604800  # 1 week
    
    # Size limits
    max_memory_entries: int = 10000
    max_disk_entries: int = 100000
    max_memory_size_mb: int = 500
    max_disk_size_mb: int = 5000
    
    # Eviction policy
    eviction_policy: str = "lru"  # lru, lfu, ttl
    
    # Compression
    enable_compression: bool = True
    compression_threshold_bytes: int = 1024
    
    # Background tasks
    cleanup_interval_seconds: int = 3600
    metrics_interval_seconds: int = 300


class ResearchCache:
    """
    Advanced multi-level caching system for legal research with Redis backend,
    intelligent eviction, and comprehensive performance monitoring.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        config: Optional[CacheConfig] = None
    ):
        self.redis_url = redis_url
        self.config = config or CacheConfig()
        self.redis: Optional[aioredis.Redis] = None
        
        # In-memory cache for frequently accessed items
        self.memory_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.access_counts: Dict[str, int] = {}
        self.access_times: Dict[str, datetime] = {}
        
        # Metrics tracking
        self.metrics = CacheMetrics()
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        
        logger.info("Research Cache initialized")
    
    async def initialize(self):
        """Initialize Redis connection and start background tasks"""
        try:
            # Connect to Redis
            self.redis = aioredis.from_url(
                self.redis_url,
                decode_responses=False,  # We handle our own encoding
                max_connections=20
            )
            
            # Test connection
            await self.redis.ping()
            
            # Start background tasks
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._metrics_task = asyncio.create_task(self._metrics_loop())
            
            logger.info("Research Cache initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Research Cache: {str(e)}")
            raise
    
    async def close(self):
        """Close Redis connection and stop background tasks"""
        try:
            # Cancel background tasks
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            if self._metrics_task:
                self._metrics_task.cancel()
                try:
                    await self._metrics_task
                except asyncio.CancelledError:
                    pass
            
            # Close Redis connection
            if self.redis:
                await self.redis.close()
            
            logger.info("Research Cache closed")
            
        except Exception as e:
            logger.error(f"Error closing Research Cache: {str(e)}")
    
    async def cache_search_result(
        self,
        query: ResearchQuery,
        result: SearchResult,
        provider: Optional[ResearchProvider] = None
    ) -> str:
        """Cache search result"""
        try:
            cache_key = self._generate_search_cache_key(query, provider)
            await self._store_cached_item(
                cache_key,
                result,
                category="search",
                ttl_seconds=self.config.search_ttl,
                provider=provider
            )
            return cache_key
            
        except Exception as e:
            logger.error(f"Failed to cache search result: {str(e)}")
            return ""
    
    async def get_cached_search_result(
        self,
        query: ResearchQuery,
        provider: Optional[ResearchProvider] = None
    ) -> Optional[SearchResult]:
        """Retrieve cached search result"""
        try:
            cache_key = self._generate_search_cache_key(query, provider)
            result = await self._retrieve_cached_item(cache_key, SearchResult)
            
            if result:
                # Mark as cached
                result.cached = True
                result.cache_hit_ratio = self.metrics.cache_hit_ratio
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to retrieve cached search result: {str(e)}")
            return None
    
    async def cache_document(
        self,
        document: LegalDocument,
        provider: Optional[ResearchProvider] = None
    ) -> str:
        """Cache legal document"""
        try:
            cache_key = self._generate_document_cache_key(document.provider_id, provider)
            await self._store_cached_item(
                cache_key,
                document,
                category="document",
                ttl_seconds=self.config.document_ttl,
                provider=provider
            )
            return cache_key
            
        except Exception as e:
            logger.error(f"Failed to cache document: {str(e)}")
            return ""
    
    async def get_cached_document(
        self,
        document_id: str,
        provider: Optional[ResearchProvider] = None
    ) -> Optional[LegalDocument]:
        """Retrieve cached document"""
        try:
            cache_key = self._generate_document_cache_key(document_id, provider)
            return await self._retrieve_cached_item(cache_key, LegalDocument)
            
        except Exception as e:
            logger.error(f"Failed to retrieve cached document: {str(e)}")
            return None
    
    async def cache_citation_validation(
        self,
        citation: str,
        validation_result: CitationValidationResult,
        provider: Optional[ResearchProvider] = None
    ) -> str:
        """Cache citation validation result"""
        try:
            cache_key = self._generate_citation_cache_key(citation, provider)
            await self._store_cached_item(
                cache_key,
                validation_result,
                category="citation",
                ttl_seconds=self.config.citation_ttl,
                provider=provider
            )
            return cache_key
            
        except Exception as e:
            logger.error(f"Failed to cache citation validation: {str(e)}")
            return ""
    
    async def get_cached_citation_validation(
        self,
        citation: str,
        provider: Optional[ResearchProvider] = None
    ) -> Optional[CitationValidationResult]:
        """Retrieve cached citation validation"""
        try:
            cache_key = self._generate_citation_cache_key(citation, provider)
            return await self._retrieve_cached_item(cache_key, CitationValidationResult)
            
        except Exception as e:
            logger.error(f"Failed to retrieve cached citation validation: {str(e)}")
            return None
    
    async def invalidate_cache(
        self,
        pattern: Optional[str] = None,
        category: Optional[str] = None,
        provider: Optional[ResearchProvider] = None
    ) -> int:
        """Invalidate cache entries matching criteria"""
        try:
            invalidated_count = 0
            
            if pattern:
                # Redis pattern matching
                if self.redis:
                    keys = await self.redis.keys(pattern)
                    if keys:
                        await self.redis.delete(*keys)
                        invalidated_count += len(keys)
                
                # Memory cache pattern matching
                memory_keys_to_delete = []
                for key in self.memory_cache.keys():
                    if self._matches_pattern(key, pattern):
                        memory_keys_to_delete.append(key)
                
                for key in memory_keys_to_delete:
                    del self.memory_cache[key]
                    if key in self.access_counts:
                        del self.access_counts[key]
                    if key in self.access_times:
                        del self.access_times[key]
                
                invalidated_count += len(memory_keys_to_delete)
            
            # Category-based invalidation would require metadata tracking
            # For now, implement as pattern-based
            if category:
                pattern = f"*:{category}:*"
                return await self.invalidate_cache(pattern=pattern)
            
            logger.info(f"Invalidated {invalidated_count} cache entries")
            return invalidated_count
            
        except Exception as e:
            logger.error(f"Cache invalidation failed: {str(e)}")
            return 0
    
    async def warm_cache(
        self,
        queries: List[ResearchQuery],
        search_engine
    ):
        """Warm cache with common queries"""
        try:
            logger.info(f"Warming cache with {len(queries)} queries")
            
            for query in queries:
                try:
                    # Check if already cached
                    cached_result = await self.get_cached_search_result(query)
                    if cached_result:
                        continue
                    
                    # Execute search and cache result
                    result = await search_engine.search(query)
                    await self.cache_search_result(query, result)
                    
                except Exception as e:
                    logger.warning(f"Failed to warm cache for query: {str(e)}")
                    continue
            
            logger.info("Cache warming completed")
            
        except Exception as e:
            logger.error(f"Cache warming failed: {str(e)}")
    
    async def get_cache_statistics(self) -> CacheMetrics:
        """Get current cache statistics"""
        try:
            # Update storage metrics
            await self._update_storage_metrics()
            
            # Calculate hit ratio
            if self.metrics.total_requests > 0:
                self.metrics.cache_hit_ratio = (
                    self.metrics.cache_hits / self.metrics.total_requests
                )
            
            self.metrics.last_updated = datetime.utcnow()
            return self.metrics
            
        except Exception as e:
            logger.error(f"Failed to get cache statistics: {str(e)}")
            return self.metrics
    
    def _generate_search_cache_key(
        self,
        query: ResearchQuery,
        provider: Optional[ResearchProvider] = None
    ) -> str:
        """Generate cache key for search query"""
        # Create normalized query representation
        query_data = {
            "query_text": query.query_text.strip().lower(),
            "search_type": query.search_type.value,
            "document_types": sorted([dt.value for dt in query.document_types]),
            "jurisdictions": sorted(query.jurisdictions),
            "date_from": query.date_from.isoformat() if query.date_from else None,
            "date_to": query.date_to.isoformat() if query.date_to else None,
            "max_results": query.max_results,
            "sort_by": query.sort_by,
            "provider": provider.value if provider else "all"
        }
        
        # Generate hash
        query_str = str(sorted(query_data.items()))
        query_hash = hashlib.sha256(query_str.encode()).hexdigest()[:16]
        
        return f"search:{provider.value if provider else 'all'}:{query_hash}"
    
    def _generate_document_cache_key(
        self,
        document_id: str,
        provider: Optional[ResearchProvider] = None
    ) -> str:
        """Generate cache key for document"""
        provider_str = provider.value if provider else "all"
        return f"document:{provider_str}:{document_id}"
    
    def _generate_citation_cache_key(
        self,
        citation: str,
        provider: Optional[ResearchProvider] = None
    ) -> str:
        """Generate cache key for citation validation"""
        # Normalize citation for consistent caching
        normalized = citation.strip().lower()
        citation_hash = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        
        provider_str = provider.value if provider else "all"
        return f"citation:{provider_str}:{citation_hash}"
    
    async def _store_cached_item(
        self,
        cache_key: str,
        item: Any,
        category: str,
        ttl_seconds: int,
        provider: Optional[ResearchProvider] = None
    ):
        """Store item in cache with appropriate TTL"""
        try:
            start_time = datetime.utcnow()
            
            # Serialize item
            serialized_data = pickle.dumps(item)
            
            # Compress if enabled and above threshold
            if (self.config.enable_compression and 
                len(serialized_data) > self.config.compression_threshold_bytes):
                import gzip
                serialized_data = gzip.compress(serialized_data)
                cache_key += ":compressed"
            
            # Store in Redis
            if self.redis:
                await self.redis.setex(cache_key, ttl_seconds, serialized_data)
            
            # Store in memory cache if small enough
            if len(serialized_data) < 100 * 1024:  # 100KB threshold
                expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
                self.memory_cache[cache_key] = (item, expires_at)
                self.access_times[cache_key] = datetime.utcnow()
                self.access_counts[cache_key] = 0
            
            # Update metrics
            storage_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.metrics.average_storage_time_ms = (
                (self.metrics.average_storage_time_ms * self.metrics.total_entries + storage_time) /
                (self.metrics.total_entries + 1)
            )
            self.metrics.total_entries += 1
            
        except Exception as e:
            logger.error(f"Failed to store cached item {cache_key}: {str(e)}")
            raise
    
    async def _retrieve_cached_item(
        self,
        cache_key: str,
        item_type: type
    ) -> Optional[Any]:
        """Retrieve item from cache"""
        try:
            start_time = datetime.utcnow()
            self.metrics.total_requests += 1
            
            # Check memory cache first
            if cache_key in self.memory_cache:
                item, expires_at = self.memory_cache[cache_key]
                
                if expires_at > datetime.utcnow():
                    # Update access tracking
                    self.access_counts[cache_key] += 1
                    self.access_times[cache_key] = datetime.utcnow()
                    
                    self.metrics.cache_hits += 1
                    
                    # Update retrieval time
                    retrieval_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    self._update_average_retrieval_time(retrieval_time)
                    
                    return item
                else:
                    # Expired - remove from memory cache
                    del self.memory_cache[cache_key]
                    if cache_key in self.access_counts:
                        del self.access_counts[cache_key]
                    if cache_key in self.access_times:
                        del self.access_times[cache_key]
            
            # Check Redis
            if self.redis:
                # Try compressed version first
                compressed_key = cache_key + ":compressed"
                serialized_data = await self.redis.get(compressed_key)
                is_compressed = True
                
                if not serialized_data:
                    # Try uncompressed version
                    serialized_data = await self.redis.get(cache_key)
                    is_compressed = False
                
                if serialized_data:
                    # Decompress if needed
                    if is_compressed:
                        import gzip
                        serialized_data = gzip.decompress(serialized_data)
                    
                    # Deserialize
                    item = pickle.loads(serialized_data)
                    
                    # Store in memory cache for faster future access
                    if len(serialized_data) < 100 * 1024:
                        # Estimate TTL from Redis
                        ttl = await self.redis.ttl(compressed_key if is_compressed else cache_key)
                        if ttl > 0:
                            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
                            self.memory_cache[cache_key] = (item, expires_at)
                            self.access_times[cache_key] = datetime.utcnow()
                            self.access_counts[cache_key] = 1
                    
                    self.metrics.cache_hits += 1
                    
                    # Update retrieval time
                    retrieval_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    self._update_average_retrieval_time(retrieval_time)
                    
                    return item
            
            # Cache miss
            self.metrics.cache_misses += 1
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve cached item {cache_key}: {str(e)}")
            self.metrics.cache_misses += 1
            return None
    
    def _update_average_retrieval_time(self, retrieval_time_ms: float):
        """Update average retrieval time metric"""
        total_retrievals = self.metrics.cache_hits + self.metrics.cache_misses
        if total_retrievals > 0:
            self.metrics.average_retrieval_time_ms = (
                (self.metrics.average_retrieval_time_ms * (total_retrievals - 1) + retrieval_time_ms) /
                total_retrievals
            )
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval_seconds)
                await self._cleanup_expired_entries()
                await self._enforce_size_limits()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {str(e)}")
    
    async def _metrics_loop(self):
        """Background metrics update loop"""
        while True:
            try:
                await asyncio.sleep(self.config.metrics_interval_seconds)
                await self._update_storage_metrics()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache metrics update error: {str(e)}")
    
    async def _cleanup_expired_entries(self):
        """Clean up expired entries from memory cache"""
        try:
            now = datetime.utcnow()
            expired_keys = []
            
            for cache_key, (item, expires_at) in self.memory_cache.items():
                if expires_at <= now:
                    expired_keys.append(cache_key)
            
            for key in expired_keys:
                del self.memory_cache[key]
                if key in self.access_counts:
                    del self.access_counts[key]
                if key in self.access_times:
                    del self.access_times[key]
                
                self.metrics.expired_entries += 1
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
                
        except Exception as e:
            logger.error(f"Cleanup expired entries failed: {str(e)}")
    
    async def _enforce_size_limits(self):
        """Enforce cache size limits using eviction policy"""
        try:
            if len(self.memory_cache) <= self.config.max_memory_entries:
                return
            
            # Calculate how many entries to evict
            entries_to_evict = len(self.memory_cache) - self.config.max_memory_entries
            
            if self.config.eviction_policy == "lru":
                keys_to_evict = self._get_lru_keys(entries_to_evict)
            elif self.config.eviction_policy == "lfu":
                keys_to_evict = self._get_lfu_keys(entries_to_evict)
            else:  # ttl
                keys_to_evict = self._get_ttl_keys(entries_to_evict)
            
            # Evict selected keys
            for key in keys_to_evict:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                if key in self.access_counts:
                    del self.access_counts[key]
                if key in self.access_times:
                    del self.access_times[key]
                
                self.metrics.evictions_count += 1
            
            if keys_to_evict:
                logger.info(f"Evicted {len(keys_to_evict)} cache entries")
                
        except Exception as e:
            logger.error(f"Size limit enforcement failed: {str(e)}")
    
    def _get_lru_keys(self, count: int) -> List[str]:
        """Get least recently used keys"""
        sorted_keys = sorted(
            self.access_times.keys(),
            key=lambda k: self.access_times[k]
        )
        return sorted_keys[:count]
    
    def _get_lfu_keys(self, count: int) -> List[str]:
        """Get least frequently used keys"""
        sorted_keys = sorted(
            self.access_counts.keys(),
            key=lambda k: self.access_counts[k]
        )
        return sorted_keys[:count]
    
    def _get_ttl_keys(self, count: int) -> List[str]:
        """Get keys with shortest TTL"""
        now = datetime.utcnow()
        ttl_keys = []
        
        for key, (item, expires_at) in self.memory_cache.items():
            ttl_seconds = (expires_at - now).total_seconds()
            ttl_keys.append((key, ttl_seconds))
        
        # Sort by TTL (shortest first)
        ttl_keys.sort(key=lambda x: x[1])
        return [key for key, ttl in ttl_keys[:count]]
    
    async def _update_storage_metrics(self):
        """Update storage-related metrics"""
        try:
            self.metrics.total_entries = len(self.memory_cache)
            
            # Calculate memory usage
            memory_usage = 0
            for key, (item, expires_at) in self.memory_cache.items():
                try:
                    memory_usage += len(pickle.dumps(item))
                except:
                    pass  # Skip items that can't be pickled
            
            self.metrics.memory_usage_bytes = memory_usage
            
            # Redis storage info (if available)
            if self.redis:
                try:
                    info = await self.redis.info('memory')
                    self.metrics.disk_usage_bytes = info.get('used_memory', 0)
                except:
                    pass  # Redis info not available
                    
        except Exception as e:
            logger.error(f"Storage metrics update failed: {str(e)}")
    
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern (simplified)"""
        import fnmatch
        return fnmatch.fnmatch(key, pattern)