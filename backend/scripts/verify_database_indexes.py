#!/usr/bin/env python3
"""
Database Index Verification Script

Verifies that all performance indexes have been created correctly.
Provides statistics on index usage and recommendations.
"""

import sys
import os
from sqlalchemy import text, inspect

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.src.core.database import engine, DATABASE_URL


def check_database_type():
    """Check if we're using PostgreSQL or SQLite"""
    if 'postgresql' in DATABASE_URL:
        return 'postgresql'
    elif 'sqlite' in DATABASE_URL:
        return 'sqlite'
    else:
        return 'unknown'


def get_table_indexes_postgresql(table_name):
    """Get all indexes for a table in PostgreSQL"""
    query = text("""
        SELECT
            indexname,
            indexdef
        FROM pg_indexes
        WHERE tablename = :table_name
        AND schemaname = 'public'
        ORDER BY indexname;
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"table_name": table_name})
        return [(row[0], row[1]) for row in result]


def get_table_indexes_sqlite(table_name):
    """Get all indexes for a table in SQLite"""
    query = text(f"PRAGMA index_list('{table_name}');")

    with engine.connect() as conn:
        result = conn.execute(query)
        indexes = []
        for row in result:
            index_name = row[1]  # Second column is index name
            indexes.append((index_name, f"SQLite index on {table_name}"))
        return indexes


def get_index_usage_stats_postgresql():
    """Get index usage statistics from PostgreSQL"""
    query = text("""
        SELECT
            schemaname,
            tablename,
            indexname,
            idx_scan as times_used,
            idx_tup_read as tuples_read,
            idx_tup_fetch as tuples_fetched,
            pg_size_pretty(pg_relation_size(indexrelid)) as index_size
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
        ORDER BY idx_scan DESC;
    """)

    with engine.connect() as conn:
        result = conn.execute(query)
        return [dict(row._mapping) for row in result]


def get_database_cache_hit_ratio_postgresql():
    """Get PostgreSQL cache hit ratio"""
    query = text("""
        SELECT
            sum(heap_blks_read) as heap_read,
            sum(heap_blks_hit)  as heap_hit,
            CASE
                WHEN sum(heap_blks_hit) + sum(heap_blks_read) = 0 THEN 0
                ELSE sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)::numeric) * 100
            END as cache_hit_ratio
        FROM pg_statio_user_tables;
    """)

    with engine.connect() as conn:
        result = conn.execute(query)
        row = result.fetchone()
        return row[2] if row else 0


def verify_expected_indexes():
    """Verify that expected performance indexes exist"""

    db_type = check_database_type()
    print(f"📊 Database Type: {db_type.upper()}")
    print(f"📍 Database URL: {DATABASE_URL.split('@')[0] if '@' in DATABASE_URL else 'SQLite'}")
    print("")

    # Expected indexes by table
    expected_indexes = {
        'users': [
            'ix_users_active_role_created',
            'ix_users_last_active',
            'ix_users_email_verified',
            'ix_users_locked_accounts',
        ],
        'documents': [
            'ix_documents_upload_date_type',
            'ix_documents_session_upload',
            'ix_documents_type_created',
        ],
        'tracked_dockets': [
            'ix_tracked_dockets_autofetch',
            'ix_tracked_dockets_archived',
            'ix_tracked_dockets_client_matter_status',
            'ix_tracked_dockets_attorney_status',
        ],
        'recap_tasks': [
            'ix_recap_tasks_queue_priority',
            'ix_recap_tasks_retry',
            'ix_recap_tasks_cleanup',
            'ix_recap_tasks_user_status',
        ],
        'docket_documents': [
            'ix_docket_docs_download_status',
            'ix_docket_docs_filed_date',
            'ix_docket_docs_costs',
        ],
        'qa_sessions': [
            'ix_qa_sessions_active',
            'ix_qa_sessions_activity',
        ],
        'qa_messages': [
            'ix_qa_messages_session_timestamp',
        ],
        'defense_sessions': [
            'ix_defense_sessions_phase',
            'ix_defense_sessions_completed',
        ],
        'defense_messages': [
            'ix_defense_messages_session_timestamp',
        ],
    }

    # Get actual indexes
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()

    print("=" * 80)
    print("INDEX VERIFICATION REPORT")
    print("=" * 80)
    print("")

    total_expected = 0
    total_found = 0
    missing_indexes = []

    for table_name, expected in expected_indexes.items():
        if table_name not in all_tables:
            print(f"⚠️  Table '{table_name}' not found (may not be created yet)")
            continue

        print(f"📋 Table: {table_name}")
        print(f"   Expected indexes: {len(expected)}")

        # Get indexes for this table
        if db_type == 'postgresql':
            actual_indexes = get_table_indexes_postgresql(table_name)
        else:
            actual_indexes = get_table_indexes_sqlite(table_name)

        actual_index_names = [idx[0] for idx in actual_indexes]

        # Check each expected index
        found_count = 0
        for expected_idx in expected:
            total_expected += 1
            if expected_idx in actual_index_names:
                print(f"   ✅ {expected_idx}")
                found_count += 1
                total_found += 1
            else:
                print(f"   ❌ {expected_idx} (MISSING)")
                missing_indexes.append((table_name, expected_idx))

        print(f"   Found: {found_count}/{len(expected)}")
        print("")

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total expected indexes: {total_expected}")
    print(f"Total found indexes:    {total_found}")
    print(f"Missing indexes:        {total_expected - total_found}")
    print("")

    if missing_indexes:
        print("⚠️  MISSING INDEXES:")
        for table, index in missing_indexes:
            print(f"   - {table}.{index}")
        print("")
        print("💡 To create missing indexes:")
        print("   cd backend && alembic upgrade head")
        print("")
        return False
    else:
        print("✅ All performance indexes are in place!")
        print("")
        return True


def show_index_usage_stats():
    """Show index usage statistics (PostgreSQL only)"""
    db_type = check_database_type()

    if db_type != 'postgresql':
        print("ℹ️  Index usage statistics are only available for PostgreSQL")
        return

    print("=" * 80)
    print("INDEX USAGE STATISTICS")
    print("=" * 80)
    print("")

    stats = get_index_usage_stats_postgresql()

    if not stats:
        print("ℹ️  No index usage data available yet (database may be new)")
        return

    # Group by table
    from collections import defaultdict
    by_table = defaultdict(list)
    for stat in stats:
        by_table[stat['tablename']].append(stat)

    for table_name, table_stats in by_table.items():
        print(f"📋 Table: {table_name}")
        for stat in table_stats[:5]:  # Show top 5 indexes per table
            print(f"   {stat['indexname']}")
            print(f"      Scans: {stat['times_used']:,}")
            print(f"      Size:  {stat['index_size']}")
        if len(table_stats) > 5:
            print(f"   ... and {len(table_stats) - 5} more indexes")
        print("")


def show_cache_hit_ratio():
    """Show database cache hit ratio (PostgreSQL only)"""
    db_type = check_database_type()

    if db_type != 'postgresql':
        return

    print("=" * 80)
    print("DATABASE PERFORMANCE METRICS")
    print("=" * 80)
    print("")

    cache_ratio = get_database_cache_hit_ratio_postgresql()

    print(f"📊 Cache Hit Ratio: {cache_ratio:.2f}%")

    if cache_ratio >= 95:
        print("   ✅ Excellent - cache is working well")
    elif cache_ratio >= 85:
        print("   ⚠️  Good - but could be improved")
    elif cache_ratio >= 70:
        print("   ⚠️  Fair - consider increasing shared_buffers")
    else:
        print("   ❌ Poor - investigate database configuration")

    print("")
    print(f"   Target: > 95%")
    print("")


def main():
    """Main verification function"""
    print("")
    print("🔍 DATABASE INDEX VERIFICATION")
    print("")

    try:
        # Verify indexes exist
        indexes_ok = verify_expected_indexes()

        # Show usage stats (PostgreSQL only)
        if check_database_type() == 'postgresql':
            show_index_usage_stats()
            show_cache_hit_ratio()

        # Final recommendation
        if indexes_ok:
            print("=" * 80)
            print("RECOMMENDATIONS")
            print("=" * 80)
            print("")
            print("✅ Database optimization is complete!")
            print("")
            print("Next steps:")
            print("1. Run load tests to verify performance improvements:")
            print("   cd tests/load && k6 run scenarios/load-test.js")
            print("")
            print("2. Monitor index usage in production:")
            print("   python backend/scripts/verify_database_indexes.py")
            print("")
            print("3. If using PostgreSQL, run ANALYZE after initial data load:")
            print("   psql -d legal_ai_db -c 'ANALYZE;'")
            print("")
        else:
            print("=" * 80)
            print("ACTION REQUIRED")
            print("=" * 80)
            print("")
            print("❌ Some indexes are missing. Please run:")
            print("   cd backend && alembic upgrade head")
            print("")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
