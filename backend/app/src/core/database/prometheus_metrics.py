"""
Database Prometheus Metrics

Metrics for monitoring database query performance and health.
"""

from prometheus_client import Counter, Histogram, Gauge

# =============================================================================
# DATABASE QUERY METRICS
# =============================================================================

# Query execution time histogram
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query execution time in seconds',
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

# Total queries executed
db_queries_total = Counter(
    'db_queries_total',
    'Total number of database queries executed'
)

# Slow queries counter
db_slow_queries_total = Counter(
    'db_slow_queries_total',
    'Total number of slow database queries (>1s)'
)

# Query errors
db_query_errors_total = Counter(
    'db_query_errors_total',
    'Total number of database query errors',
    ['error_type']
)

# =============================================================================
# CONNECTION POOL METRICS
# =============================================================================

# Pool size (current connections)
db_pool_size = Gauge(
    'db_pool_size',
    'Current database connection pool size'
)

# Connections checked out
db_pool_checked_out = Gauge(
    'db_pool_checked_out',
    'Number of connections currently checked out from pool'
)

# Connections checked in (idle)
db_pool_checked_in = Gauge(
    'db_pool_checked_in',
    'Number of connections currently checked into pool (idle)'
)

# Pool overflow
db_pool_overflow = Gauge(
    'db_pool_overflow',
    'Number of overflow connections in pool'
)

# Total pool connections
db_pool_total_connections = Gauge(
    'db_pool_total_connections',
    'Total number of connections in pool (size + overflow)'
)

# =============================================================================
# DATABASE OPERATION METRICS
# =============================================================================

# Insert operations
db_inserts_total = Counter(
    'db_inserts_total',
    'Total number of INSERT operations',
    ['table']
)

# Update operations
db_updates_total = Counter(
    'db_updates_total',
    'Total number of UPDATE operations',
    ['table']
)

# Delete operations
db_deletes_total = Counter(
    'db_deletes_total',
    'Total number of DELETE operations',
    ['table']
)

# Bulk operations
db_bulk_operations_total = Counter(
    'db_bulk_operations_total',
    'Total number of bulk database operations',
    ['operation_type', 'table']
)

# Rows affected by bulk operations
db_bulk_rows_affected = Counter(
    'db_bulk_rows_affected',
    'Total number of rows affected by bulk operations',
    ['operation_type', 'table']
)

# =============================================================================
# TRANSACTION METRICS
# =============================================================================

# Transaction duration
db_transaction_duration_seconds = Histogram(
    'db_transaction_duration_seconds',
    'Database transaction duration in seconds',
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Transaction commits
db_transactions_committed = Counter(
    'db_transactions_committed',
    'Total number of committed transactions'
)

# Transaction rollbacks
db_transactions_rolled_back = Counter(
    'db_transactions_rolled_back',
    'Total number of rolled back transactions'
)

# =============================================================================
# CACHE METRICS
# =============================================================================

# Query result cache hits
db_query_cache_hits = Counter(
    'db_query_cache_hits',
    'Total number of query result cache hits'
)

# Query result cache misses
db_query_cache_misses = Counter(
    'db_query_cache_misses',
    'Total number of query result cache misses'
)

# Cache hit ratio (derived metric)
def get_cache_hit_ratio() -> float:
    """Calculate cache hit ratio"""
    hits = db_query_cache_hits._value.get()
    misses = db_query_cache_misses._value.get()
    total = hits + misses

    if total == 0:
        return 0.0

    return hits / total

# =============================================================================
# INDEX USAGE METRICS
# =============================================================================

# Sequential scans
db_sequential_scans_total = Counter(
    'db_sequential_scans_total',
    'Total number of sequential table scans',
    ['table']
)

# Index scans
db_index_scans_total = Counter(
    'db_index_scans_total',
    'Total number of index scans',
    ['table', 'index']
)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def update_db_pool_metrics(pool):
    """
    Update database pool metrics from SQLAlchemy pool.

    Args:
        pool: SQLAlchemy connection pool
    """
    try:
        db_pool_size.set(pool.size())
        db_pool_checked_out.set(pool.checkedout())
        db_pool_checked_in.set(pool.checkedin())
        db_pool_overflow.set(pool.overflow())
        db_pool_total_connections.set(pool.size() + pool.overflow())
    except Exception as e:
        # Silently fail if pool doesn't support these methods
        pass


def track_bulk_operation(operation_type: str, table: str, rows_affected: int):
    """
    Track bulk database operation.

    Args:
        operation_type: Type of operation (insert, update, delete)
        table: Table name
        rows_affected: Number of rows affected
    """
    db_bulk_operations_total.labels(
        operation_type=operation_type,
        table=table
    ).inc()

    db_bulk_rows_affected.labels(
        operation_type=operation_type,
        table=table
    ).inc(rows_affected)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'db_query_duration_seconds',
    'db_queries_total',
    'db_slow_queries_total',
    'db_query_errors_total',
    'db_pool_size',
    'db_pool_checked_out',
    'db_pool_checked_in',
    'db_pool_overflow',
    'db_pool_total_connections',
    'db_inserts_total',
    'db_updates_total',
    'db_deletes_total',
    'db_bulk_operations_total',
    'db_bulk_rows_affected',
    'db_transaction_duration_seconds',
    'db_transactions_committed',
    'db_transactions_rolled_back',
    'db_query_cache_hits',
    'db_query_cache_misses',
    'db_sequential_scans_total',
    'db_index_scans_total',
    'update_db_pool_metrics',
    'track_bulk_operation',
    'get_cache_hit_ratio',
]
