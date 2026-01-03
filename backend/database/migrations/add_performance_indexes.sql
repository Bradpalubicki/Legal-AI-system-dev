-- =============================================================================
-- Database Performance Indexes Migration
-- Legal AI System - Query Optimization
-- =============================================================================
--
-- This migration adds performance-critical indexes for common query patterns.
-- Run this migration to improve database query performance.
--
-- To apply:
--   psql -U your_user -d legal_ai -f add_performance_indexes.sql
--
-- To rollback:
--   Run the rollback section at the bottom of this file
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- USERS TABLE INDEXES
-- =============================================================================

-- Composite index for active user lookups (common in authentication)
CREATE INDEX IF NOT EXISTS idx_users_active_email
    ON users(email, is_active)
    WHERE is_active = true;

-- Index for role-based queries (RBAC lookups)
CREATE INDEX IF NOT EXISTS idx_users_role_active
    ON users(role, is_active)
    WHERE is_active = true;

-- Index for premium user queries
CREATE INDEX IF NOT EXISTS idx_users_premium_active
    ON users(is_premium, is_active)
    WHERE is_premium = true AND is_active = true;

-- Index for login tracking queries (last_login_at DESC for recent users)
CREATE INDEX IF NOT EXISTS idx_users_last_login
    ON users(last_login_at DESC)
    WHERE last_login_at IS NOT NULL;

-- Index for account recovery and security
CREATE INDEX IF NOT EXISTS idx_users_password_reset
    ON users(password_reset_token, password_reset_expires)
    WHERE password_reset_token IS NOT NULL;

-- Index for OAuth lookups
CREATE INDEX IF NOT EXISTS idx_users_oauth
    ON users(oauth_provider, oauth_id)
    WHERE oauth_provider IS NOT NULL;

-- Partial index for locked accounts (small subset)
CREATE INDEX IF NOT EXISTS idx_users_locked
    ON users(account_locked_until)
    WHERE account_locked_until IS NOT NULL AND account_locked_until > NOW();

-- Index for soft deletes
CREATE INDEX IF NOT EXISTS idx_users_deleted
    ON users(deleted_at)
    WHERE deleted_at IS NOT NULL;

-- Composite index for user search queries
CREATE INDEX IF NOT EXISTS idx_users_search
    ON users(email, username, full_name)
    WHERE is_active = true;

-- =============================================================================
-- DOCUMENTS TABLE INDEXES
-- =============================================================================

-- Composite index for session document lookups
CREATE INDEX IF NOT EXISTS idx_documents_session_upload
    ON documents(session_id, upload_date DESC);

-- Index for document type filtering
CREATE INDEX IF NOT EXISTS idx_documents_type_session
    ON documents(document_type, session_id)
    WHERE document_type IS NOT NULL;

-- Partial index for active documents (exclude soft-deleted)
CREATE INDEX IF NOT EXISTS idx_documents_active
    ON documents(session_id, upload_date DESC)
    WHERE is_deleted = false;

-- Index for full-text search on document content (PostgreSQL)
CREATE INDEX IF NOT EXISTS idx_documents_text_content_fts
    ON documents USING gin(to_tsvector('english', text_content));

-- Index for file type queries
CREATE INDEX IF NOT EXISTS idx_documents_file_type
    ON documents(file_type, upload_date DESC);

-- Index for recent documents
CREATE INDEX IF NOT EXISTS idx_documents_recent
    ON documents(upload_date DESC)
    WHERE is_deleted = false;

-- Composite index for pagination queries
CREATE INDEX IF NOT EXISTS idx_documents_pagination
    ON documents(session_id, id, upload_date DESC)
    WHERE is_deleted = false;

-- =============================================================================
-- QA SESSIONS TABLE INDEXES
-- =============================================================================

-- Composite index for active session lookups
CREATE INDEX IF NOT EXISTS idx_qa_sessions_doc_active
    ON qa_sessions(document_id, is_active, last_activity DESC);

-- Index for session ID lookups (frontend session tracking)
CREATE INDEX IF NOT EXISTS idx_qa_sessions_session_id
    ON qa_sessions(session_id, started_at DESC);

-- Index for recent activity queries
CREATE INDEX IF NOT EXISTS idx_qa_sessions_last_activity
    ON qa_sessions(last_activity DESC)
    WHERE is_active = true;

-- Composite index for document session listing
CREATE INDEX IF NOT EXISTS idx_qa_sessions_doc_started
    ON qa_sessions(document_id, started_at DESC);

-- =============================================================================
-- QA MESSAGES TABLE INDEXES
-- =============================================================================

-- Composite index for message retrieval (most common query)
CREATE INDEX IF NOT EXISTS idx_qa_messages_session_timestamp
    ON qa_messages(session_id, timestamp ASC);

-- Index for role filtering (user vs AI messages)
CREATE INDEX IF NOT EXISTS idx_qa_messages_role_timestamp
    ON qa_messages(session_id, role, timestamp ASC);

-- Index for recent messages
CREATE INDEX IF NOT EXISTS idx_qa_messages_recent
    ON qa_messages(timestamp DESC);

-- =============================================================================
-- DEFENSE SESSIONS TABLE INDEXES
-- =============================================================================

-- Composite index for document defense sessions
CREATE INDEX IF NOT EXISTS idx_defense_sessions_doc_started
    ON defense_sessions(document_id, started_at DESC);

-- Index for session phase queries
CREATE INDEX IF NOT EXISTS idx_defense_sessions_phase
    ON defense_sessions(phase, last_activity DESC);

-- Index for completed sessions
CREATE INDEX IF NOT EXISTS idx_defense_sessions_completed
    ON defense_sessions(completed_at DESC)
    WHERE completed_at IS NOT NULL;

-- Composite index for active sessions
CREATE INDEX IF NOT EXISTS idx_defense_sessions_active
    ON defense_sessions(session_id, phase, last_activity DESC)
    WHERE completed_at IS NULL;

-- Index for case type analysis
CREATE INDEX IF NOT EXISTS idx_defense_sessions_case_type
    ON defense_sessions(case_type, completed_at DESC)
    WHERE case_type IS NOT NULL;

-- =============================================================================
-- DEFENSE MESSAGES TABLE INDEXES
-- =============================================================================

-- Composite index for message retrieval
CREATE INDEX IF NOT EXISTS idx_defense_messages_session_timestamp
    ON defense_messages(session_id, timestamp ASC);

-- Index for role filtering
CREATE INDEX IF NOT EXISTS idx_defense_messages_role
    ON defense_messages(session_id, role, timestamp ASC);

-- =============================================================================
-- ANALYTICS INDEXES (if analytics table exists)
-- =============================================================================

-- Check if analytics tables exist and add indexes
DO $$
BEGIN
    -- User events index (if user_events table exists)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_events') THEN
        CREATE INDEX IF NOT EXISTS idx_user_events_user_created
            ON user_events(user_id, created_at DESC);

        CREATE INDEX IF NOT EXISTS idx_user_events_event_type
            ON user_events(event_type, created_at DESC);

        CREATE INDEX IF NOT EXISTS idx_user_events_created
            ON user_events(created_at DESC);
    END IF;

    -- Audit logs index (if audit_logs table exists)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs') THEN
        CREATE INDEX IF NOT EXISTS idx_audit_logs_user_created
            ON audit_logs(user_id, created_at DESC);

        CREATE INDEX IF NOT EXISTS idx_audit_logs_action
            ON audit_logs(action, created_at DESC);

        CREATE INDEX IF NOT EXISTS idx_audit_logs_resource
            ON audit_logs(resource_type, resource_id, created_at DESC);
    END IF;
END $$;

-- =============================================================================
-- STATISTICS UPDATE
-- =============================================================================

-- Update table statistics for query planner
ANALYZE users;
ANALYZE documents;
ANALYZE qa_sessions;
ANALYZE qa_messages;
ANALYZE defense_sessions;
ANALYZE defense_messages;

-- =============================================================================
-- VERIFY INDEXES
-- =============================================================================

-- Query to verify all new indexes were created
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
    AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

COMMIT;

-- =============================================================================
-- ROLLBACK SCRIPT (if needed)
-- =============================================================================

/*
BEGIN;

-- Users table indexes
DROP INDEX IF EXISTS idx_users_active_email;
DROP INDEX IF EXISTS idx_users_role_active;
DROP INDEX IF EXISTS idx_users_premium_active;
DROP INDEX IF EXISTS idx_users_last_login;
DROP INDEX IF EXISTS idx_users_password_reset;
DROP INDEX IF EXISTS idx_users_oauth;
DROP INDEX IF EXISTS idx_users_locked;
DROP INDEX IF EXISTS idx_users_deleted;
DROP INDEX IF EXISTS idx_users_search;

-- Documents table indexes
DROP INDEX IF EXISTS idx_documents_session_upload;
DROP INDEX IF EXISTS idx_documents_type_session;
DROP INDEX IF EXISTS idx_documents_active;
DROP INDEX IF EXISTS idx_documents_text_content_fts;
DROP INDEX IF EXISTS idx_documents_file_type;
DROP INDEX IF EXISTS idx_documents_recent;
DROP INDEX IF EXISTS idx_documents_pagination;

-- QA Sessions indexes
DROP INDEX IF EXISTS idx_qa_sessions_doc_active;
DROP INDEX IF EXISTS idx_qa_sessions_session_id;
DROP INDEX IF EXISTS idx_qa_sessions_last_activity;
DROP INDEX IF EXISTS idx_qa_sessions_doc_started;

-- QA Messages indexes
DROP INDEX IF EXISTS idx_qa_messages_session_timestamp;
DROP INDEX IF EXISTS idx_qa_messages_role_timestamp;
DROP INDEX IF EXISTS idx_qa_messages_recent;

-- Defense Sessions indexes
DROP INDEX IF EXISTS idx_defense_sessions_doc_started;
DROP INDEX IF EXISTS idx_defense_sessions_phase;
DROP INDEX IF EXISTS idx_defense_sessions_completed;
DROP INDEX IF EXISTS idx_defense_sessions_active;
DROP INDEX IF EXISTS idx_defense_sessions_case_type;

-- Defense Messages indexes
DROP INDEX IF EXISTS idx_defense_messages_session_timestamp;
DROP INDEX IF EXISTS idx_defense_messages_role;

-- Analytics indexes
DROP INDEX IF EXISTS idx_user_events_user_created;
DROP INDEX IF EXISTS idx_user_events_event_type;
DROP INDEX IF EXISTS idx_user_events_created;
DROP INDEX IF EXISTS idx_audit_logs_user_created;
DROP INDEX IF EXISTS idx_audit_logs_action;
DROP INDEX IF EXISTS idx_audit_logs_resource;

COMMIT;
*/

-- =============================================================================
-- PERFORMANCE NOTES
-- =============================================================================

/*
Expected Performance Improvements:

1. User Queries:
   - Login/authentication: 10-50x faster (email + is_active lookup)
   - Role-based queries: 5-20x faster (role + is_active index)
   - User search: 3-10x faster (composite search index)

2. Document Queries:
   - Session documents: 5-15x faster (session_id + upload_date)
   - Full-text search: 20-100x faster (GIN index on text_content)
   - Recent documents: 10-30x faster (partial index on active docs)

3. Session Queries:
   - QA message retrieval: 10-40x faster (session_id + timestamp)
   - Active sessions: 5-15x faster (is_active + last_activity)

4. Index Sizes:
   - Most indexes: 5-20% of table size
   - Full-text index: 50-100% of table size (worth it for search)
   - Partial indexes: 1-10% of table size (very efficient)

5. Maintenance:
   - Indexes auto-update on INSERT/UPDATE (minimal overhead)
   - Run ANALYZE weekly for optimal query plans
   - Monitor index usage with pg_stat_user_indexes

6. Trade-offs:
   - +10-15% write overhead (acceptable for read-heavy workload)
   - +20-40% storage (compensated by query performance)
   - Significantly faster reads (10-100x depending on query)
*/
