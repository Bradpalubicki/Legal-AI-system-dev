# Database Query Optimization Guide
## Legal AI System - Production Database Performance

This guide covers database query optimization techniques, best practices, and tools for maintaining optimal database performance in production.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Performance Indexes](#performance-indexes)
3. [Query Optimization Utilities](#query-optimization-utilities)
4. [Slow Query Monitoring](#slow-query-monitoring)
5. [Common Query Patterns](#common-query-patterns)
6. [N+1 Query Prevention](#n1-query-prevention)
7. [Pagination Best Practices](#pagination-best-practices)
8. [Bulk Operations](#bulk-operations)
9. [Connection Pool Tuning](#connection-pool-tuning)
10. [Monitoring and Alerts](#monitoring-and-alerts)

---

## Quick Start

### Apply Performance Indexes

```bash
# Connect to database
psql -U postgres -d legal_ai

# Apply indexes migration
\i backend/database/migrations/add_performance_indexes.sql

# Verify indexes were created
SELECT indexname, indexdef FROM pg_indexes
WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
```

### Import Query Optimizer

```python
from backend.app.src.core.database.query_optimizer import (
    paginate_efficiently,
    bulk_insert_optimized,
    cache_query_result,
    detect_n_plus_one,
)
```

---

## Performance Indexes

### Indexes Created

The migration `add_performance_indexes.sql` adds **40+ optimized indexes** across all tables:

#### Users Table (9 indexes)
- `idx_users_active_email` - Fast login lookups
- `idx_users_role_active` - Role-based access control
- `idx_users_premium_active` - Premium user queries
- `idx_users_last_login` - Recent activity tracking
- `idx_users_password_reset` - Password recovery
- `idx_users_oauth` - OAuth provider lookups
- `idx_users_locked` - Account security
- `idx_users_deleted` - Soft delete queries
- `idx_users_search` - User search functionality

#### Documents Table (7 indexes)
- `idx_documents_session_upload` - Session document listing
- `idx_documents_type_session` - Document type filtering
- `idx_documents_active` - Active documents (soft deletes)
- `idx_documents_text_content_fts` - Full-text search (GIN index)
- `idx_documents_file_type` - File type queries
- `idx_documents_recent` - Recent documents
- `idx_documents_pagination` - Efficient pagination

#### QA Sessions (4 indexes)
- Session and document lookups
- Activity tracking
- Message retrieval

#### Defense Sessions (5 indexes)
- Phase tracking
- Completion status
- Case type analysis

### Expected Performance Improvements

| Query Type | Before | After | Improvement |
|-----------|--------|-------|-------------|
| User login | 50ms | 5ms | **10x faster** |
| Document search (full-text) | 2000ms | 50ms | **40x faster** |
| Session message retrieval | 100ms | 10ms | **10x faster** |
| Recent documents | 150ms | 15ms | **10x faster** |
| Role-based queries | 80ms | 8ms | **10x faster** |

### Index Maintenance

```sql
-- Update table statistics (run weekly)
ANALYZE users;
ANALYZE documents;
ANALYZE qa_sessions;
ANALYZE qa_messages;

-- Check index bloat
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;

-- Rebuild bloated indexes (if needed)
REINDEX INDEX idx_documents_text_content_fts;
```

---

## Query Optimization Utilities

### Efficient Pagination

**Problem**: OFFSET pagination is slow for large page numbers.

**Solution**: Use optimized pagination utilities.

```python
from backend.app.src.core.database.query_optimizer import paginate_efficiently, keyset_paginate

# Standard pagination (good for small datasets)
def get_documents(page=1, per_page=20):
    query = db.query(Document).filter(Document.is_deleted == False)
    result = paginate_efficiently(query, page=page, per_page=per_page)

    return {
        'documents': result['items'],
        'total': result['total'],
        'page': result['page'],
        'pages': result['pages'],
        'has_next': result['has_next'],
    }

# Keyset pagination (best for large datasets, infinite scroll)
def get_documents_cursor(after_id=None, limit=20):
    query = db.query(Document).filter(Document.is_deleted == False)
    documents = keyset_paginate(query, after_id=after_id, limit=limit)

    return {
        'documents': documents,
        'next_cursor': documents[-1].id if documents else None,
    }
```

**Performance**:
- Page 1: Both methods ~10ms
- Page 100: Standard ~200ms, Keyset ~10ms (20x faster)
- Page 1000: Standard ~2000ms, Keyset ~10ms (200x faster)

### Query Result Caching

Cache frequently accessed data to reduce database load.

```python
from backend.app.src.core.database.query_optimizer import cache_query_result

@cache_query_result(
    cache_key_fn=lambda user_id: f"user_documents:{user_id}",
    ttl=300  # 5 minutes
)
def get_user_documents(user_id: int):
    """Get user documents (cached for 5 minutes)"""
    return db.query(Document).filter(
        Document.user_id == user_id,
        Document.is_deleted == False
    ).order_by(Document.upload_date.desc()).all()

# First call: Hits database, caches result
docs1 = get_user_documents(123)  # ~50ms

# Subsequent calls within 5 minutes: Returns cached result
docs2 = get_user_documents(123)  # ~1ms (50x faster)
```

**When to use caching**:
- ✅ Read-heavy data (10:1 read/write ratio or higher)
- ✅ Expensive queries (joins, aggregations, full-text search)
- ✅ Data that doesn't change frequently
- ❌ Real-time data requirements
- ❌ User-specific data that changes often

---

## Slow Query Monitoring

### Automatic Slow Query Logging

Queries taking >1 second are automatically logged:

```python
# Slow queries are logged automatically
# Check logs:
import logging
logger = logging.getLogger(__name__)

# Get recent slow queries
from backend.app.src.core.database.query_optimizer import get_slow_queries

slow_queries = get_slow_queries(limit=10)
for q in slow_queries:
    print(f"Duration: {q['duration']:.3f}s")
    print(f"Query: {q['query']}")
    print(f"Parameters: {q['parameters']}")
    print("---")
```

### Manual Query Analysis

```python
from backend.app.src.core.database.query_optimizer import analyze_query_performance, explain_query

# Analyze query performance
query = db.query(Document).join(QASession).filter(QASession.is_active == True)
analysis = analyze_query_performance(db.session, query)

print(f"Execution time: {analysis['execution_time']:.3f}s")
print(f"Rows returned: {analysis['row_count']}")
print(f"Is slow: {analysis['is_slow']}")
print(f"Explain plan:\n{analysis['explain_plan']}")

# Or use context manager for EXPLAIN ANALYZE
with explain_query(db.session, query) as explain_output:
    results = query.all()
    # explain_output contains the execution plan
```

### Find Missing Indexes

```python
from backend.app.src.core.database.query_optimizer import find_missing_indexes

# Find tables that might need indexes
tables = find_missing_indexes(db.session)

for table in tables:
    print(f"Table: {table['table']}")
    print(f"Sequential scans: {table['sequential_scans']}")
    print(f"Tuples read: {table['tuples_read']}")
    print(f"Suggest adding index if scans > 1000 and tuples > 100k")
    print("---")
```

---

## Common Query Patterns

### 1. User Authentication (Optimized)

```python
# ✅ GOOD - Uses idx_users_active_email
user = db.query(User).filter(
    User.email == email,
    User.is_active == True
).first()

# ❌ BAD - No index on lowercase email
user = db.query(User).filter(
    func.lower(User.email) == email.lower()
).first()

# ✅ BETTER - Create functional index if needed
# CREATE INDEX idx_users_email_lower ON users (LOWER(email));
```

### 2. Document Listing with Filters

```python
# ✅ GOOD - Uses idx_documents_active
def get_documents(session_id, document_type=None, page=1):
    query = db.query(Document).filter(
        Document.session_id == session_id,
        Document.is_deleted == False
    ).order_by(Document.upload_date.desc())

    if document_type:
        query = query.filter(Document.document_type == document_type)

    return paginate_efficiently(query, page=page, per_page=20)

# ❌ BAD - Fetches all then filters in Python
all_docs = db.query(Document).all()
filtered = [d for d in all_docs if d.session_id == session_id and not d.is_deleted]
```

### 3. Full-Text Search

```python
# ✅ GOOD - Uses idx_documents_text_content_fts (GIN index)
from sqlalchemy import func

search_query = "contract agreement"
documents = db.query(Document).filter(
    func.to_tsvector('english', Document.text_content).match(search_query)
).order_by(Document.upload_date.desc()).limit(50).all()

# ❌ BAD - LIKE query on text field (very slow)
documents = db.query(Document).filter(
    Document.text_content.like(f'%{search_query}%')
).all()
```

### 4. Joining with Filtering

```python
# ✅ GOOD - Filter on indexed columns, use proper joins
def get_active_qa_sessions_with_documents(session_id):
    return db.query(QASession).join(
        Document, QASession.document_id == Document.id
    ).filter(
        QASession.session_id == session_id,
        QASession.is_active == True,
        Document.is_deleted == False
    ).options(
        # Eager load to avoid N+1
        joinedload(QASession.messages)
    ).all()

# ❌ BAD - Fetching all and filtering in Python
sessions = db.query(QASession).all()
filtered = [s for s in sessions if s.is_active and s.document.session_id == session_id]
```

### 5. Aggregations

```python
# ✅ GOOD - Database aggregation
from sqlalchemy import func

stats = db.query(
    func.count(Document.id).label('total'),
    func.count(func.distinct(Document.document_type)).label('types'),
    func.sum(Document.file_size).label('total_size')
).filter(
    Document.session_id == session_id,
    Document.is_deleted == False
).first()

# ❌ BAD - Fetching all and calculating in Python
docs = db.query(Document).filter_by(session_id=session_id).all()
total = len(docs)
total_size = sum(d.file_size for d in docs)
```

---

## N+1 Query Prevention

### The N+1 Problem

```python
# ❌ BAD - N+1 queries (1 + N queries)
documents = db.query(Document).limit(10).all()  # 1 query
for doc in documents:
    # Each iteration triggers another query
    sessions = doc.qa_sessions  # N queries (10 more queries!)
    print(f"Document {doc.id} has {len(sessions)} sessions")

# Total: 11 queries for 10 documents
```

### Solution 1: Eager Loading (joinedload)

```python
# ✅ GOOD - 1 query with JOIN
from sqlalchemy.orm import joinedload

documents = db.query(Document).options(
    joinedload(Document.qa_sessions)
).limit(10).all()

for doc in documents:
    sessions = doc.qa_sessions  # No additional query!
    print(f"Document {doc.id} has {len(sessions)} sessions")

# Total: 1 query for 10 documents
```

### Solution 2: Subquery Loading (subqueryload)

```python
# ✅ GOOD - 2 queries (better for one-to-many with many children)
from sqlalchemy.orm import subqueryload

documents = db.query(Document).options(
    subqueryload(Document.qa_sessions).subqueryload(QASession.messages)
).limit(10).all()

# Total: 3 queries (documents, qa_sessions, messages)
# Much better than 1 + 10 + 100+ queries
```

### Detection

```python
from backend.app.src.core.database.query_optimizer import detect_n_plus_one

# Detect N+1 problems in development
with detect_n_plus_one(db.session, expected_queries=2) as counter:
    documents = db.query(Document).options(
        joinedload(Document.qa_sessions)
    ).limit(10).all()

    for doc in documents:
        sessions = doc.qa_sessions

# Logs warning if >2 queries executed
```

---

## Pagination Best Practices

### Offset Pagination (Default)

**When to use**: Small datasets, page numbers needed

```python
from backend.app.src.core.database.query_optimizer import paginate_efficiently

result = paginate_efficiently(
    query=db.query(Document).filter(Document.is_deleted == False),
    page=1,
    per_page=20,
    max_per_page=100
)

# Returns:
# {
#     'items': [...],
#     'total': 1543,
#     'page': 1,
#     'per_page': 20,
#     'pages': 78,
#     'has_next': True,
#     'has_prev': False,
# }
```

**Performance**:
- Page 1-10: Fast (<20ms)
- Page 100: Slow (~200ms)
- Page 1000: Very slow (~2000ms)

### Keyset Pagination (Cursor-based)

**When to use**: Large datasets, infinite scroll, APIs

```python
from backend.app.src.core.database.query_optimizer import keyset_paginate

# First page
documents = keyset_paginate(
    query=db.query(Document).filter(Document.is_deleted == False),
    after_id=None,
    limit=20,
    order_column='id'
)

# Next page (use last item's ID as cursor)
last_id = documents[-1].id
next_documents = keyset_paginate(
    query=db.query(Document).filter(Document.is_deleted == False),
    after_id=last_id,
    limit=20
)
```

**Performance**:
- All pages: Fast (~10ms consistently)
- No performance degradation on large page numbers

### Comparison

| Feature | Offset Pagination | Keyset Pagination |
|---------|------------------|-------------------|
| Page numbers | ✅ Yes | ❌ No (cursor-based) |
| Performance (large pages) | ❌ Slow | ✅ Fast |
| Consistency during writes | ❌ Can skip/duplicate | ✅ Consistent |
| Total count | ✅ Yes | ❌ No |
| Use case | Admin panels, small datasets | APIs, infinite scroll, large datasets |

---

## Bulk Operations

### Bulk Insert

```python
from backend.app.src.core.database.query_optimizer import bulk_insert_optimized

# Prepare data
documents_data = [
    {
        'id': str(uuid.uuid4()),
        'session_id': session_id,
        'file_name': f'doc_{i}.pdf',
        'text_content': f'Content {i}',
        'upload_date': datetime.utcnow(),
    }
    for i in range(1000)
]

# Bulk insert (batched automatically)
count = bulk_insert_optimized(
    session=db.session,
    model_class=Document,
    data=documents_data,
    batch_size=1000
)

print(f"Inserted {count} documents")

# Performance: 1000 inserts in ~100ms (vs ~5000ms with individual inserts)
```

### Bulk Update

```python
from backend.app.src.core.database.query_optimizer import bulk_update_optimized

# Prepare update data (must include PK)
updates = [
    {'id': doc.id, 'is_deleted': True}
    for doc in documents_to_delete
]

# Bulk update
count = bulk_update_optimized(
    session=db.session,
    model_class=Document,
    data=updates,
    batch_size=1000
)

print(f"Updated {count} documents")
```

### Performance Comparison

| Operation | Individual | Bulk | Improvement |
|-----------|-----------|------|-------------|
| Insert 1000 rows | 5000ms | 100ms | **50x faster** |
| Update 1000 rows | 3000ms | 80ms | **37x faster** |
| Delete 1000 rows | 2000ms | 60ms | **33x faster** |

---

## Connection Pool Tuning

### Configuration

```python
# backend/app/src/core/database.py

from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,

    # Pool settings
    poolclass=QueuePool,
    pool_size=20,          # Permanent connections
    max_overflow=10,       # Additional connections when pool full
    pool_timeout=30,       # Timeout waiting for connection
    pool_recycle=3600,     # Recycle connections after 1 hour
    pool_pre_ping=True,    # Verify connection before using

    # Performance settings
    echo=False,            # Don't log all SQL (use in dev only)
    echo_pool=False,       # Don't log pool events
)
```

### Monitoring

```python
from backend.app.src.core.database.query_optimizer import get_pool_stats

stats = get_pool_stats(engine)
print(f"Pool size: {stats['size']}")
print(f"Checked out: {stats['checked_out']}")
print(f"Checked in: {stats['checked_in']}")
print(f"Overflow: {stats['overflow']}")
print(f"Total connections: {stats['total_connections']}")

# Alert if pool is exhausted
if stats['overflow'] >= stats['max_overflow']:
    logger.warning("Connection pool exhausted! Consider increasing pool_size.")
```

### Sizing Guidelines

**Formula**: `pool_size = (CPU cores * 2) + effective_spindle_count`

For web application on 4-core server with SSD:
- `pool_size = (4 * 2) + 1 = 9` connections
- `max_overflow = pool_size / 2 = 4-5` connections
- **Total**: 13-14 max connections

**Adjust based on**:
- More cores → larger pool
- Long-running queries → smaller pool
- Short queries → larger pool
- Connection limit → don't exceed PostgreSQL `max_connections`

---

## Monitoring and Alerts

### Prometheus Metrics

All database queries are automatically tracked:

```python
# Metrics collected:
# - db_query_duration_seconds (histogram)
# - db_queries_total (counter)
# - db_slow_queries_total (counter)
# - db_pool_size (gauge)
# - db_pool_checked_out (gauge)
# - db_query_errors_total (counter)
```

### Grafana Dashboard

Import the database panel from `monitoring/grafana/dashboards/application-overview.json`:

- Query rate (queries/second)
- Query duration (p50, p95, p99)
- Slow queries count
- Connection pool usage
- Query errors

### Alerts

Configure in `monitoring/prometheus/alerts.yml`:

```yaml
- alert: SlowDatabaseQueries
  expr: rate(db_slow_queries_total[5m]) > 10
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High rate of slow database queries"
    description: "{{ $value }} slow queries per second"

- alert: DatabasePoolExhausted
  expr: db_pool_checked_out / db_pool_size > 0.9
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Database connection pool nearly exhausted"
    description: "{{ $value | humanizePercentage }} of connections in use"
```

### Index Usage Analysis

```python
from backend.app.src.core.database.query_optimizer import analyze_index_usage

# Find unused indexes
indexes = analyze_index_usage(db.session)

for idx in indexes:
    if idx['scans'] == 0:
        print(f"Unused index: {idx['table']}.{idx['index']}")
        print(f"Size: {idx['size']}")
        print("Consider dropping if truly unused")
```

---

## Best Practices Summary

### ✅ DO

1. **Always use indexes** for frequently queried columns
2. **Use pagination** for large result sets
3. **Use eager loading** to avoid N+1 queries
4. **Cache expensive queries** when appropriate
5. **Use bulk operations** for batch inserts/updates
6. **Monitor slow queries** and optimize them
7. **Use connection pooling** with appropriate limits
8. **Run ANALYZE** regularly to update query statistics
9. **Use keyset pagination** for large datasets
10. **Test queries with EXPLAIN ANALYZE** before deploying

### ❌ DON'T

1. **Don't fetch all records** then filter in Python
2. **Don't use LIKE '%term%'** for search (use full-text search)
3. **Don't iterate relationships** without eager loading
4. **Don't ignore slow query logs**
5. **Don't create indexes on every column** (overhead)
6. **Don't use OFFSET for large page numbers**
7. **Don't forget to close database sessions**
8. **Don't run expensive queries in request handlers** (use background jobs)
9. **Don't trust the query planner** without verification
10. **Don't skip database monitoring**

---

## Troubleshooting

### Query Taking Too Long

```python
# 1. Check if query is using indexes
with explain_query(db.session, query) as plan:
    results = query.all()
    # Look for "Seq Scan" (bad) vs "Index Scan" (good)

# 2. Analyze query performance
analysis = analyze_query_performance(db.session, query)
if analysis['is_slow']:
    print(f"Slow query: {analysis['execution_time']:.3f}s")
    print(f"Explain plan:\n{analysis['explain_plan']}")

# 3. Check for missing indexes
missing = find_missing_indexes(db.session)
for table in missing:
    if table['table'] == 'your_table':
        print(f"Consider adding index to {table['table']}")
```

### Connection Pool Exhausted

```python
# 1. Check pool stats
stats = get_pool_stats(engine)
if stats['overflow'] >= stats['max_overflow']:
    # Pool is exhausted

# 2. Find long-running queries
# Run in psql:
# SELECT pid, query_start, state, query
# FROM pg_stat_activity
# WHERE state != 'idle'
# ORDER BY query_start;

# 3. Increase pool size or find query causing the issue
```

### N+1 Queries

```python
# 1. Enable query counting in tests
with detect_n_plus_one(db.session, expected_queries=2) as counter:
    # Your code here
    pass

# 2. Add eager loading
query = query.options(joinedload(Model.relationship))

# 3. Verify with logging
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

---

## Additional Resources

### PostgreSQL Documentation
- Indexes: https://www.postgresql.org/docs/current/indexes.html
- EXPLAIN: https://www.postgresql.org/docs/current/using-explain.html
- Performance Tips: https://wiki.postgresql.org/wiki/Performance_Optimization

### SQLAlchemy Documentation
- Query API: https://docs.sqlalchemy.org/en/14/orm/query.html
- Loading Techniques: https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html
- Connection Pooling: https://docs.sqlalchemy.org/en/14/core/pooling.html

---

**Last Updated**: 2024-01-15
**Version**: 1.0
