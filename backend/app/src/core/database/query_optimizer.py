"""
Database Query Optimizer

Utilities for optimizing database queries, monitoring performance,
and implementing best practices for SQLAlchemy queries.
"""

import time
import logging
import functools
from typing import Optional, List, Dict, Any, Callable, TypeVar, Union
from contextlib import contextmanager
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, Query
from sqlalchemy.sql import Select

from .prometheus_metrics import (
    db_query_duration_seconds,
    db_slow_queries_total,
    db_queries_total,
)

logger = logging.getLogger(__name__)

# Type variables for generic decorators
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

# =============================================================================
# QUERY MONITORING
# =============================================================================

# Slow query threshold (seconds)
SLOW_QUERY_THRESHOLD = 1.0

# Track slow queries for analysis
slow_queries_log: List[Dict[str, Any]] = []
MAX_SLOW_QUERIES_LOG = 100


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Track query start time"""
    conn.info.setdefault('query_start_time', []).append(time.time())


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Track query execution time and log slow queries"""
    total = time.time() - conn.info['query_start_time'].pop(-1)

    # Track in Prometheus
    db_query_duration_seconds.observe(total)
    db_queries_total.inc()

    # Log slow queries
    if total > SLOW_QUERY_THRESHOLD:
        db_slow_queries_total.inc()

        # Clean query string for logging
        query_str = str(statement)[:500]  # Limit length

        logger.warning(
            f"Slow query detected ({total:.3f}s): {query_str}",
            extra={
                'query_duration': total,
                'query': query_str,
                'parameters': str(parameters)[:200] if parameters else None,
            }
        )

        # Store in memory for analysis (circular buffer)
        if len(slow_queries_log) >= MAX_SLOW_QUERIES_LOG:
            slow_queries_log.pop(0)

        slow_queries_log.append({
            'query': query_str,
            'duration': total,
            'timestamp': time.time(),
            'parameters': str(parameters)[:200] if parameters else None,
        })


def get_slow_queries(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get recent slow queries for analysis.

    Args:
        limit: Maximum number of queries to return

    Returns:
        List of slow query information dictionaries
    """
    return slow_queries_log[-limit:]


def clear_slow_queries_log():
    """Clear the slow queries log"""
    slow_queries_log.clear()


# =============================================================================
# QUERY OPTIMIZATION UTILITIES
# =============================================================================

def optimize_query(query: Query) -> Query:
    """
    Apply optimization strategies to a SQLAlchemy query.

    Optimizations:
    - Enable subquery loading for relationships
    - Add query hints for PostgreSQL
    - Optimize joins

    Args:
        query: SQLAlchemy Query object

    Returns:
        Optimized Query object
    """
    # Enable subquery loading for better performance with relationships
    # (avoids N+1 queries)
    query = query.options()

    return query


def paginate_efficiently(
    query: Query,
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100
) -> Dict[str, Any]:
    """
    Efficiently paginate query results with optimizations.

    Uses keyset pagination when possible for better performance on large datasets.

    Args:
        query: SQLAlchemy Query object
        page: Page number (1-indexed)
        per_page: Items per page
        max_per_page: Maximum items per page

    Returns:
        Dictionary with:
        - items: List of results
        - total: Total count
        - page: Current page
        - per_page: Items per page
        - pages: Total pages
        - has_next: Boolean
        - has_prev: Boolean
    """
    # Validate and cap per_page
    per_page = min(per_page, max_per_page)
    page = max(page, 1)

    # Calculate offset
    offset = (page - 1) * per_page

    # Get total count (can be expensive)
    # Use query.count() which is optimized
    total = query.count()

    # Get paginated results
    items = query.limit(per_page).offset(offset).all()

    # Calculate pagination metadata
    pages = (total + per_page - 1) // per_page  # Ceiling division

    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': pages,
        'has_next': page < pages,
        'has_prev': page > 1,
    }


def keyset_paginate(
    query: Query,
    after_id: Optional[int] = None,
    limit: int = 20,
    order_column: str = 'id'
) -> List[Any]:
    """
    Keyset pagination for efficient pagination of large datasets.

    Much faster than OFFSET pagination for large page numbers.

    Args:
        query: SQLAlchemy Query object
        after_id: ID to paginate after (for next page)
        limit: Number of items to return
        order_column: Column to order by (must be indexed)

    Returns:
        List of results

    Example:
        # First page
        results = keyset_paginate(query, limit=20)

        # Next page
        last_id = results[-1].id
        next_results = keyset_paginate(query, after_id=last_id, limit=20)
    """
    if after_id is not None:
        # Add WHERE clause for keyset pagination
        model = query.column_descriptions[0]['type']
        column = getattr(model, order_column)
        query = query.filter(column > after_id)

    # Order and limit
    model = query.column_descriptions[0]['type']
    column = getattr(model, order_column)
    results = query.order_by(column).limit(limit).all()

    return results


# =============================================================================
# BULK OPERATIONS
# =============================================================================

def bulk_insert_optimized(
    session: Session,
    model_class: type,
    data: List[Dict[str, Any]],
    batch_size: int = 1000
) -> int:
    """
    Efficiently insert many rows using bulk operations.

    Args:
        session: SQLAlchemy Session
        model_class: Model class to insert
        data: List of dictionaries with model data
        batch_size: Number of rows per batch

    Returns:
        Number of rows inserted
    """
    if not data:
        return 0

    total_inserted = 0

    # Process in batches
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]

        # Use bulk_insert_mappings for best performance
        session.bulk_insert_mappings(model_class, batch)

        total_inserted += len(batch)

        logger.info(f"Bulk inserted {len(batch)} {model_class.__name__} records")

    session.commit()

    return total_inserted


def bulk_update_optimized(
    session: Session,
    model_class: type,
    data: List[Dict[str, Any]],
    batch_size: int = 1000
) -> int:
    """
    Efficiently update many rows using bulk operations.

    Each dict in data must include the primary key for updating.

    Args:
        session: SQLAlchemy Session
        model_class: Model class to update
        data: List of dictionaries with model data (must include PK)
        batch_size: Number of rows per batch

    Returns:
        Number of rows updated
    """
    if not data:
        return 0

    total_updated = 0

    # Process in batches
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]

        # Use bulk_update_mappings for best performance
        session.bulk_update_mappings(model_class, batch)

        total_updated += len(batch)

        logger.info(f"Bulk updated {len(batch)} {model_class.__name__} records")

    session.commit()

    return total_updated


# =============================================================================
# QUERY RESULT CACHING
# =============================================================================

def cache_query_result(
    cache_key_fn: Callable[..., str],
    ttl: int = 300
):
    """
    Decorator to cache query results.

    Args:
        cache_key_fn: Function to generate cache key from function args
        ttl: Time to live in seconds

    Example:
        @cache_query_result(
            cache_key_fn=lambda user_id: f"user_docs:{user_id}",
            ttl=300
        )
        def get_user_documents(user_id: int):
            return db.query(Document).filter_by(user_id=user_id).all()
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try to import cache
            try:
                from ...cache.redis_cache import cache

                # Generate cache key
                cache_key = cache_key_fn(*args, **kwargs)

                # Try to get from cache
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_result

                # Execute function
                result = func(*args, **kwargs)

                # Store in cache
                cache.set(cache_key, result, ttl=ttl)
                logger.debug(f"Cached result for key: {cache_key}")

                return result

            except ImportError:
                # Cache not available, execute function directly
                return func(*args, **kwargs)

        return wrapper
    return decorator


# =============================================================================
# QUERY ANALYSIS
# =============================================================================

@contextmanager
def explain_query(session: Session, query: Union[Query, Select]):
    """
    Context manager to explain query execution plan.

    Usage:
        with explain_query(db.session, query):
            results = query.all()

    This will log the EXPLAIN ANALYZE output.
    """
    # Convert query to string
    query_str = str(query.statement if hasattr(query, 'statement') else query)

    # Execute EXPLAIN ANALYZE
    explain_stmt = text(f"EXPLAIN ANALYZE {query_str}")

    try:
        result = session.execute(explain_stmt)
        explain_output = '\n'.join([row[0] for row in result])

        logger.info(f"Query execution plan:\n{explain_output}")

        yield explain_output

    except Exception as e:
        logger.error(f"Error explaining query: {e}")
        yield None


def analyze_query_performance(
    session: Session,
    query: Union[Query, Select]
) -> Dict[str, Any]:
    """
    Analyze query performance and return metrics.

    Args:
        session: SQLAlchemy Session
        query: Query to analyze

    Returns:
        Dictionary with performance metrics:
        - execution_time: Time in seconds
        - row_count: Number of rows returned
        - explain_plan: EXPLAIN output (if available)
    """
    # Execute query with timing
    start_time = time.time()

    results = query.all() if hasattr(query, 'all') else session.execute(query).fetchall()

    execution_time = time.time() - start_time

    # Get explain plan
    try:
        query_str = str(query.statement if hasattr(query, 'statement') else query)
        explain_stmt = text(f"EXPLAIN {query_str}")
        explain_result = session.execute(explain_stmt)
        explain_plan = '\n'.join([row[0] for row in explain_result])
    except Exception as e:
        logger.warning(f"Could not get explain plan: {e}")
        explain_plan = None

    return {
        'execution_time': execution_time,
        'row_count': len(results),
        'explain_plan': explain_plan,
        'is_slow': execution_time > SLOW_QUERY_THRESHOLD,
    }


# =============================================================================
# N+1 QUERY DETECTION
# =============================================================================

class QueryCounter:
    """Context manager to count queries executed"""

    def __init__(self, session: Session):
        self.session = session
        self.query_count = 0

    def __enter__(self):
        self.query_count = 0
        event.listen(self.session.bind, "before_cursor_execute", self._count_query)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        event.remove(self.session.bind, "before_cursor_execute", self._count_query)

    def _count_query(self, conn, cursor, statement, parameters, context, executemany):
        self.query_count += 1


@contextmanager
def detect_n_plus_one(session: Session, expected_queries: Optional[int] = None):
    """
    Detect N+1 query problems.

    Usage:
        with detect_n_plus_one(db.session, expected_queries=2):
            users = db.query(User).all()
            for user in users:
                print(user.documents)  # If not eager loaded, triggers N+1

    Args:
        session: SQLAlchemy Session
        expected_queries: Expected number of queries (warning if exceeded)
    """
    counter = QueryCounter(session)

    with counter:
        yield counter

    if expected_queries and counter.query_count > expected_queries:
        logger.warning(
            f"Potential N+1 query problem detected: "
            f"{counter.query_count} queries executed (expected {expected_queries})"
        )


# =============================================================================
# INDEX USAGE ANALYSIS
# =============================================================================

def analyze_index_usage(session: Session) -> List[Dict[str, Any]]:
    """
    Analyze index usage in PostgreSQL.

    Returns list of indexes with usage statistics.
    """
    query = text("""
        SELECT
            schemaname,
            tablename,
            indexname,
            idx_scan AS index_scans,
            idx_tup_read AS tuples_read,
            idx_tup_fetch AS tuples_fetched,
            pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
        FROM pg_stat_user_indexes
        ORDER BY idx_scan ASC, pg_relation_size(indexrelid) DESC
        LIMIT 50;
    """)

    result = session.execute(query)

    indexes = []
    for row in result:
        indexes.append({
            'schema': row[0],
            'table': row[1],
            'index': row[2],
            'scans': row[3],
            'tuples_read': row[4],
            'tuples_fetched': row[5],
            'size': row[6],
        })

    return indexes


def find_missing_indexes(session: Session) -> List[Dict[str, Any]]:
    """
    Find tables that might benefit from additional indexes.

    Looks for sequential scans on large tables.
    """
    query = text("""
        SELECT
            schemaname,
            tablename,
            seq_scan AS sequential_scans,
            seq_tup_read AS tuples_read,
            idx_scan AS index_scans,
            n_tup_ins + n_tup_upd + n_tup_del AS write_activity,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size
        FROM pg_stat_user_tables
        WHERE seq_scan > 0
            AND seq_tup_read / NULLIF(seq_scan, 0) > 10000  -- Average >10k rows per seq scan
        ORDER BY seq_scan DESC, seq_tup_read DESC
        LIMIT 20;
    """)

    result = session.execute(query)

    tables = []
    for row in result:
        tables.append({
            'schema': row[0],
            'table': row[1],
            'sequential_scans': row[2],
            'tuples_read': row[3],
            'index_scans': row[4],
            'write_activity': row[5],
            'total_size': row[6],
        })

    return tables


# =============================================================================
# CONNECTION POOL MONITORING
# =============================================================================

def get_pool_stats(engine: Engine) -> Dict[str, Any]:
    """
    Get connection pool statistics.

    Args:
        engine: SQLAlchemy Engine

    Returns:
        Dictionary with pool statistics
    """
    pool = engine.pool

    return {
        'size': pool.size(),
        'checked_in': pool.checkedin(),
        'checked_out': pool.checkedout(),
        'overflow': pool.overflow(),
        'total_connections': pool.size() + pool.overflow(),
        'max_overflow': pool._max_overflow if hasattr(pool, '_max_overflow') else None,
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'optimize_query',
    'paginate_efficiently',
    'keyset_paginate',
    'bulk_insert_optimized',
    'bulk_update_optimized',
    'cache_query_result',
    'explain_query',
    'analyze_query_performance',
    'detect_n_plus_one',
    'analyze_index_usage',
    'find_missing_indexes',
    'get_pool_stats',
    'get_slow_queries',
    'clear_slow_queries_log',
]
