#!/usr/bin/env python3
"""
PERFORMANCE OPTIMIZATION SYSTEM

Comprehensive performance optimization for legal AI system:
- Disclaimer content caching with TTL
- Encryption operation batching and pooling
- Audit log indexing and query optimization
- Database connection pooling
- Monitoring metrics collection
- Health check endpoints with <100ms response

CRITICAL: Optimizes system performance while maintaining security and compliance.
"""

import os
import time
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import json
import hashlib
from collections import defaultdict, deque
try:
    import psutil
except ImportError:
    psutil = None
import weakref
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for system monitoring"""
    system_name: str
    response_time_ms: float
    throughput_ops_per_sec: float
    accuracy_rate: float
    error_count: int
    cache_hit_rate: float
    timestamp: datetime
    memory_usage_mb: float
    cpu_usage_percent: float

class SystemHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    DOWN = "down"

class DisclaimerCache:
    """High-performance disclaimer content caching system"""
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.cache = {}
        self.access_times = {}
        self.hit_count = 0
        self.miss_count = 0
        self.lock = threading.RLock()
        
        # Start cache cleanup thread
        self._start_cleanup_thread()
    
    def get(self, key: str) -> Optional[str]:
        """Get cached disclaimer content"""
        with self.lock:
            current_time = time.time()
            
            if key in self.cache:
                entry_time = self.access_times[key]
                if current_time - entry_time < self.ttl_seconds:
                    self.hit_count += 1
                    self.access_times[key] = current_time  # Update access time
                    return self.cache[key]
                else:
                    # Expired - remove entry
                    del self.cache[key]
                    del self.access_times[key]
            
            self.miss_count += 1
            return None
    
    def set(self, key: str, value: str) -> None:
        """Set cached disclaimer content"""
        with self.lock:
            current_time = time.time()
            
            # Evict old entries if cache is full
            if len(self.cache) >= self.max_size:
                self._evict_oldest()
            
            self.cache[key] = value
            self.access_times[key] = current_time
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate_percent': hit_rate,
                'cache_size': len(self.cache),
                'max_size': self.max_size,
                'ttl_seconds': self.ttl_seconds
            }
    
    def _evict_oldest(self) -> None:
        """Evict oldest cache entries"""
        if not self.access_times:
            return
        
        # Remove 10% of oldest entries
        remove_count = max(1, len(self.access_times) // 10)
        oldest_keys = sorted(self.access_times.keys(), 
                            key=lambda k: self.access_times[k])[:remove_count]
        
        for key in oldest_keys:
            del self.cache[key]
            del self.access_times[key]
    
    def _start_cleanup_thread(self) -> None:
        """Start background cleanup thread"""
        def cleanup_expired():
            while True:
                try:
                    time.sleep(60)  # Cleanup every minute
                    current_time = time.time()
                    
                    with self.lock:
                        expired_keys = [
                            key for key, access_time in self.access_times.items()
                            if current_time - access_time >= self.ttl_seconds
                        ]
                        
                        for key in expired_keys:
                            del self.cache[key]
                            del self.access_times[key]
                            
                except Exception as e:
                    logger.error(f"Cache cleanup error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_expired, name="DisclaimerCacheCleanup", daemon=True)
        cleanup_thread.start()

class EncryptionBatchProcessor:
    """Batch processing system for encryption operations"""
    
    def __init__(self, batch_size: int = 50, max_wait_time: float = 0.1):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_operations = queue.Queue()
        self.results = {}
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="EncryptionBatch")
        self.processing_lock = threading.Lock()
        
        # Start batch processor
        self._start_batch_processor()
    
    def encrypt_async(self, data: bytes, operation_id: str) -> str:
        """Add encryption operation to batch queue"""
        future = asyncio.get_event_loop().create_future()
        self.pending_operations.put((data, operation_id, future))
        return operation_id
    
    def get_result(self, operation_id: str, timeout: float = 5.0) -> Optional[bytes]:
        """Get encryption result"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if operation_id in self.results:
                return self.results.pop(operation_id)
            time.sleep(0.01)
        return None
    
    def _start_batch_processor(self) -> None:
        """Start background batch processor"""
        def process_batches():
            batch = []
            last_batch_time = time.time()
            
            while True:
                try:
                    # Collect batch items
                    try:
                        while len(batch) < self.batch_size:
                            timeout = max(0.01, self.max_wait_time - (time.time() - last_batch_time))
                            item = self.pending_operations.get(timeout=timeout)
                            batch.append(item)
                    except queue.Empty:
                        pass
                    
                    # Process batch if we have items and conditions are met
                    if batch and (len(batch) >= self.batch_size or 
                                time.time() - last_batch_time >= self.max_wait_time):
                        self._process_batch(batch)
                        batch = []
                        last_batch_time = time.time()
                        
                except Exception as e:
                    logger.error(f"Batch processing error: {e}")
        
        processor_thread = threading.Thread(target=process_batches, name="EncryptionBatchProcessor", daemon=True)
        processor_thread.start()
    
    def _process_batch(self, batch: List[tuple]) -> None:
        """Process a batch of encryption operations"""
        if not batch:
            return
        
        futures = []
        for data, operation_id, result_future in batch:
            future = self.executor.submit(self._encrypt_single, data, operation_id)
            futures.append((future, operation_id, result_future))
        
        # Collect results
        for future, operation_id, result_future in futures:
            try:
                encrypted_data = future.result(timeout=1.0)
                self.results[operation_id] = encrypted_data
                if not result_future.done():
                    result_future.set_result(encrypted_data)
            except Exception as e:
                logger.error(f"Encryption batch item failed: {e}")
                if not result_future.done():
                    result_future.set_exception(e)
    
    def _encrypt_single(self, data: bytes, operation_id: str) -> bytes:
        """Encrypt single data item (placeholder - integrate with actual encryption)"""
        # This would integrate with the actual encryption system
        import hashlib
        return hashlib.sha256(data).digest()
    
    def encrypt_document_batch(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Encrypt a batch of documents with metadata"""
        encrypted_docs = []
        
        for doc in documents:
            try:
                filename = doc.get('filename', 'unknown.txt')
                content = doc.get('content', b'')
                metadata = doc.get('metadata', {})
                
                # Generate operation ID
                operation_id = f"{filename}_{int(time.time() * 1000)}"
                
                # Encrypt content (simplified for testing)
                if isinstance(content, str):
                    content = content.encode('utf-8')
                
                encrypted_content = self._encrypt_single(content, operation_id)
                encryption_key = f"key_{operation_id}"  # Simplified key generation
                
                encrypted_doc = {
                    'filename': filename,
                    'original_size': len(content),
                    'encrypted_content': encrypted_content,
                    'encrypted_size': len(encrypted_content),
                    'key_id': encryption_key,
                    'metadata': {
                        **metadata,
                        'encrypted_at': datetime.utcnow().isoformat(),
                        'encryption_algorithm': 'sha256_placeholder'
                    }
                }
                
                encrypted_docs.append(encrypted_doc)
                
            except Exception as e:
                logger.error(f"Failed to encrypt document {doc.get('filename', 'unknown')}: {e}")
                # Return error document
                encrypted_docs.append({
                    'filename': doc.get('filename', 'unknown'),
                    'error': str(e),
                    'encrypted': False
                })
        
        return encrypted_docs

class AuditLogOptimizer:
    """Audit log indexing and query optimization"""
    
    def __init__(self, db_paths: List[str]):
        self.db_paths = db_paths
        self.connection_pool = {}
        self.query_cache = {}
        self.query_stats = defaultdict(list)
        
        # Initialize optimizations
        self._create_indexes()
        self._setup_connection_pooling()
    
    def _create_indexes(self) -> None:
        """Create performance indexes on audit tables"""
        indexes = [
            # Security audit indexes
            ("security_events", "idx_security_timestamp", "timestamp"),
            ("security_events", "idx_security_user", "user_id"),
            ("security_events", "idx_security_type", "event_type"),
            ("security_events", "idx_security_severity", "severity"),
            
            # Admin audit indexes
            ("admin_actions", "idx_admin_timestamp", "timestamp"),
            ("admin_actions", "idx_admin_user", "admin_user_id"),
            ("admin_actions", "idx_admin_type", "action_type"),
            
            # Emergency audit indexes
            ("emergency_audit_log", "idx_emergency_timestamp", "timestamp"),
            ("emergency_audit_log", "idx_emergency_type", "event_type"),
            ("emergency_audit_log", "idx_emergency_source", "source_system"),
        ]
        
        for db_path in self.db_paths:
            if os.path.exists(db_path):
                try:
                    with sqlite3.connect(db_path) as conn:
                        for table_name, index_name, column in indexes:
                            try:
                                conn.execute(f"""
                                    CREATE INDEX IF NOT EXISTS {index_name} 
                                    ON {table_name} ({column})
                                """)
                            except sqlite3.OperationalError:
                                # Table might not exist, skip
                                pass
                        conn.commit()
                    logger.info(f"Created indexes for {db_path}")
                except Exception as e:
                    logger.error(f"Failed to create indexes for {db_path}: {e}")
    
    def _setup_connection_pooling(self) -> None:
        """Setup connection pooling for databases"""
        for db_path in self.db_paths:
            if os.path.exists(db_path):
                self.connection_pool[db_path] = queue.Queue(maxsize=10)
                # Pre-populate pool
                for _ in range(5):
                    try:
                        conn = sqlite3.connect(db_path)
                        conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
                        conn.execute("PRAGMA synchronous=NORMAL")  # Faster writes
                        conn.execute("PRAGMA cache_size=10000")  # Increase cache
                        self.connection_pool[db_path].put(conn)
                    except Exception as e:
                        logger.error(f"Failed to create pooled connection for {db_path}: {e}")
    
    def get_connection(self, db_path: str) -> sqlite3.Connection:
        """Get pooled database connection"""
        pool = self.connection_pool.get(db_path)
        if pool:
            try:
                return pool.get(timeout=1.0)
            except queue.Empty:
                pass
        
        # Fallback to new connection
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn
    
    def return_connection(self, db_path: str, conn: sqlite3.Connection) -> None:
        """Return connection to pool"""
        pool = self.connection_pool.get(db_path)
        if pool:
            try:
                pool.put_nowait(conn)
                return
            except queue.Full:
                pass
        
        # Pool full or doesn't exist, close connection
        conn.close()

class MetricsCollector:
    """System metrics collection and monitoring"""
    
    def __init__(self):
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))
        self.collection_lock = threading.Lock()
        self.start_time = time.time()
        
        # Start metrics collection thread
        self._start_metrics_collection()
    
    def record_metric(self, system_name: str, response_time: float, 
                     throughput: float = 0, accuracy: float = 100, 
                     error_count: int = 0, cache_hit_rate: float = 0) -> None:
        """Record performance metric"""
        with self.collection_lock:
            metric = PerformanceMetrics(
                system_name=system_name,
                response_time_ms=response_time * 1000,  # Convert to ms
                throughput_ops_per_sec=throughput,
                accuracy_rate=accuracy,
                error_count=error_count,
                cache_hit_rate=cache_hit_rate,
                timestamp=datetime.utcnow(),
                memory_usage_mb=psutil.Process().memory_info().rss / 1024 / 1024 if psutil else 0,
                cpu_usage_percent=psutil.Process().cpu_percent() if psutil else 0
            )
            
            self.metrics_history[system_name].append(metric)
    
    def get_metrics(self, system_name: str, minutes: int = 5) -> List[PerformanceMetrics]:
        """Get recent metrics for system"""
        with self.collection_lock:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            recent_metrics = [
                metric for metric in self.metrics_history[system_name]
                if metric.timestamp >= cutoff_time
            ]
            return recent_metrics
    
    def get_system_summary(self, system_name: str) -> Dict[str, Any]:
        """Get performance summary for system"""
        metrics = self.get_metrics(system_name, minutes=5)
        
        if not metrics:
            return {
                'system_name': system_name,
                'status': 'no_data',
                'avg_response_time_ms': 0,
                'avg_throughput': 0,
                'avg_accuracy': 0,
                'error_count': 0,
                'sample_count': 0
            }
        
        avg_response = sum(m.response_time_ms for m in metrics) / len(metrics)
        avg_throughput = sum(m.throughput_ops_per_sec for m in metrics) / len(metrics)
        avg_accuracy = sum(m.accuracy_rate for m in metrics) / len(metrics)
        total_errors = sum(m.error_count for m in metrics)
        
        # Determine health status
        if avg_response > 1000 or avg_accuracy < 80 or total_errors > 10:
            status = SystemHealth.CRITICAL
        elif avg_response > 500 or avg_accuracy < 90 or total_errors > 5:
            status = SystemHealth.DEGRADED
        elif avg_response > 100:
            status = SystemHealth.DEGRADED
        else:
            status = SystemHealth.HEALTHY
        
        return {
            'system_name': system_name,
            'status': status.value,
            'avg_response_time_ms': round(avg_response, 2),
            'avg_throughput': round(avg_throughput, 2),
            'avg_accuracy': round(avg_accuracy, 2),
            'error_count': total_errors,
            'sample_count': len(metrics),
            'health_status': status.value
        }
    
    def _start_metrics_collection(self) -> None:
        """Start background metrics collection"""
        def collect_system_metrics():
            while True:
                try:
                    time.sleep(30)  # Collect every 30 seconds
                    
                    # Collect system-wide metrics if psutil available
                    if psutil:
                        cpu_percent = psutil.cpu_percent(interval=1)
                        memory = psutil.virtual_memory()
                        try:
                            disk = psutil.disk_usage('/')
                        except:
                            disk = None
                    
                    self.record_metric(
                        'system_resources',
                        response_time=0,
                        throughput=0,
                        accuracy=100,
                        error_count=0,
                        cache_hit_rate=0
                    )
                    
                except Exception as e:
                    logger.error(f"System metrics collection error: {e}")
        
        metrics_thread = threading.Thread(target=collect_system_metrics, name="SystemMetrics", daemon=True)
        metrics_thread.start()

class PerformanceOptimizer:
    """Main performance optimization coordinator"""
    
    def __init__(self):
        self.disclaimer_cache = DisclaimerCache(ttl_seconds=300, max_size=1000)
        self.encryption_batch = EncryptionBatchProcessor(batch_size=50, max_wait_time=0.1)
        
        # Setup audit log optimization
        audit_db_paths = [
            "security_events.db",
            "admin_actions.db", 
            "emergency_audit.db",
            "professional_audit.db",
            "legal_advice_detection.db"
        ]
        self.audit_optimizer = AuditLogOptimizer(audit_db_paths)
        self.metrics_collector = MetricsCollector()
        
        # Add encryption optimizer alias for compatibility
        self.encryption_optimizer = self.encryption_batch
        
        # Performance monitoring
        self.health_checks = {}
        self.response_time_targets = {
            'advice_detection': 100,  # ms
            'disclaimers': 50,        # ms
            'encryption': 200,        # ms
            'audit': 100             # ms
        }
        
        logger.info("[PERFORMANCE] Performance optimization system initialized")
    
    def optimize_disclaimer_retrieval(self, disclaimer_key: str, 
                                    generator_func: Callable[[], str]) -> str:
        """Optimized disclaimer retrieval with caching"""
        start_time = time.time()
        
        # Try cache first
        cached_content = self.disclaimer_cache.get(disclaimer_key)
        if cached_content:
            response_time = time.time() - start_time
            self.metrics_collector.record_metric(
                'disclaimers', response_time, throughput=1, 
                cache_hit_rate=self.disclaimer_cache.get_cache_stats()['hit_rate_percent']
            )
            return cached_content
        
        # Generate and cache
        try:
            content = generator_func()
            self.disclaimer_cache.set(disclaimer_key, content)
            response_time = time.time() - start_time
            self.metrics_collector.record_metric(
                'disclaimers', response_time, throughput=1,
                cache_hit_rate=self.disclaimer_cache.get_cache_stats()['hit_rate_percent']
            )
            return content
        except Exception as e:
            response_time = time.time() - start_time
            self.metrics_collector.record_metric(
                'disclaimers', response_time, error_count=1
            )
            raise
    
    def get_health_status(self, system_name: str) -> Dict[str, Any]:
        """Get system health status with <100ms response target"""
        start_time = time.time()
        
        try:
            summary = self.metrics_collector.get_system_summary(system_name)
            response_time = time.time() - start_time
            
            # Check if response time meets target
            target_ms = self.response_time_targets.get(system_name, 100)
            response_time_ms = response_time * 1000
            
            meets_target = response_time_ms < target_ms
            
            health_data = {
                **summary,
                'response_time_ms': round(response_time_ms, 2),
                'target_ms': target_ms,
                'meets_target': meets_target,
                'uptime_seconds': time.time() - self.metrics_collector.start_time,
                'cache_stats': self.disclaimer_cache.get_cache_stats() if system_name == 'disclaimers' else None
            }
            
            return health_data
            
        except Exception as e:
            response_time = time.time() - start_time
            return {
                'system_name': system_name,
                'status': 'error',
                'error': str(e),
                'response_time_ms': round(response_time * 1000, 2),
                'meets_target': False
            }
    
    def get_all_health_status(self) -> Dict[str, Any]:
        """Get health status for all systems"""
        systems = ['advice_detection', 'disclaimers', 'encryption', 'audit']
        health_status = {}
        
        for system in systems:
            health_status[system] = self.get_health_status(system)
        
        # Overall system health
        all_healthy = all(
            status.get('meets_target', False) and status.get('status') == 'healthy'
            for status in health_status.values()
        )
        
        health_status['overall'] = {
            'status': 'healthy' if all_healthy else 'degraded',
            'systems_count': len(systems),
            'healthy_systems': sum(1 for s in health_status.values() if s.get('status') == 'healthy'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return health_status
    
    def health_check(self) -> Dict[str, Any]:
        """Fast health check for performance optimizer - Target: <10ms"""
        start_time = time.time()
        
        try:
            # Test basic functionality
            cache_size = len(self.disclaimer_cache.cache) if hasattr(self.disclaimer_cache, 'cache') else 0
            metrics_count = len(self.metrics_collector.metrics) if hasattr(self.metrics_collector, 'metrics') else 0
            
            response_time_ms = (time.time() - start_time) * 1000
            
            return {
                'service': 'performance_optimizer',
                'status': 'healthy' if response_time_ms < 10 else 'degraded',
                'response_time_ms': round(response_time_ms, 2),
                'meets_target': response_time_ms < 10,
                'cache_size': cache_size,
                'metrics_tracked': metrics_count,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return {
                'service': 'performance_optimizer',
                'status': 'error',
                'error': str(e),
                'response_time_ms': round(response_time_ms, 2),
                'meets_target': False,
                'timestamp': datetime.utcnow().isoformat()
            }

# Global performance optimizer
performance_optimizer = PerformanceOptimizer()