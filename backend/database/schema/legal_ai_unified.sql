-- Legal AI System - Unified Database Schema
-- Supports: Cases, PACER Monitoring, Defense Building, Sessions

-- =============================================================================
-- CASES TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_number VARCHAR(100) NOT NULL,
    case_name VARCHAR(500) NOT NULL,
    case_type VARCHAR(100),
    client_id UUID REFERENCES users(id) ON DELETE CASCADE,
    client_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'new',
    priority VARCHAR(20) DEFAULT 'medium',
    filed_date DATE,
    response_deadline TIMESTAMP,
    court VARCHAR(255),
    judge VARCHAR(255),
    plaintiff VARCHAR(255),
    defendant VARCHAR(255),
    description TEXT,
    amount_claimed DECIMAL(12, 2),
    defense_strategy JSONB,
    documents TEXT[],
    notes TEXT,
    last_pacer_check TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    assigned_to UUID REFERENCES users(id)
);

CREATE INDEX idx_cases_client_id ON cases(client_id);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_case_number ON cases(case_number);
CREATE INDEX idx_cases_response_deadline ON cases(response_deadline);

-- =============================================================================
-- COURT FILINGS TABLE (PACER Monitor)
-- =============================================================================
CREATE TABLE IF NOT EXISTS court_filings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    document_number VARCHAR(50),
    document_url TEXT,
    filing_date TIMESTAMP,
    description TEXT,
    filed_by VARCHAR(255),
    document_type VARCHAR(100),
    analysis JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(case_id, document_number)
);

CREATE INDEX idx_court_filings_case_id ON court_filings(case_id);
CREATE INDEX idx_court_filings_filing_date ON court_filings(filing_date);

-- =============================================================================
-- DOCKET ENTRIES TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS docket_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    entry_number INTEGER,
    date TIMESTAMP,
    description TEXT,
    document_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(case_id, entry_number)
);

CREATE INDEX idx_docket_entries_case_id ON docket_entries(case_id);

-- =============================================================================
-- CASE STATUS HISTORY
-- =============================================================================
CREATE TABLE IF NOT EXISTS case_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    field VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT NOW(),
    changed_by UUID REFERENCES users(id)
);

CREATE INDEX idx_case_status_history_case_id ON case_status_history(case_id);

-- =============================================================================
-- ALERTS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    alert_type VARCHAR(50),
    title VARCHAR(255),
    message TEXT,
    severity VARCHAR(20) DEFAULT 'medium',
    document_id UUID,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    read_at TIMESTAMP
);

CREATE INDEX idx_alerts_user_id ON alerts(user_id);
CREATE INDEX idx_alerts_case_id ON alerts(case_id);
CREATE INDEX idx_alerts_is_read ON alerts(is_read);

-- =============================================================================
-- AI SESSIONS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    session_token VARCHAR(255) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    case_id UUID REFERENCES cases(id) ON DELETE SET NULL,
    context JSONB DEFAULT '{}',
    analysis JSONB,
    interview_answers JSONB DEFAULT '{}',
    strategy JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_fingerprint VARCHAR(255),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ai_sessions_user_id ON ai_sessions(user_id);
CREATE INDEX idx_ai_sessions_case_id ON ai_sessions(case_id);
CREATE INDEX idx_ai_sessions_session_id ON ai_sessions(session_id);
CREATE INDEX idx_ai_sessions_expires_at ON ai_sessions(expires_at);

-- =============================================================================
-- ACTIVITIES TABLE (Audit Log)
-- =============================================================================
CREATE TABLE IF NOT EXISTS activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    activity_type VARCHAR(100),
    action VARCHAR(255),
    table_name VARCHAR(100),
    record_id UUID,
    ip_address VARCHAR(45),
    user_agent TEXT,
    metadata JSONB,
    security_relevant BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_activities_user_id ON activities(user_id);
CREATE INDEX idx_activities_created_at ON activities(created_at);
CREATE INDEX idx_activities_security_relevant ON activities(security_relevant);

-- =============================================================================
-- DATA ACCESS LOG (Compliance)
-- =============================================================================
CREATE TABLE IF NOT EXISTS data_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),
    user_role VARCHAR(50),
    table_name VARCHAR(100),
    record_id UUID,
    case_id UUID REFERENCES cases(id) ON DELETE SET NULL,
    document_id UUID,
    access_type VARCHAR(50),
    contains_pii BOOLEAN DEFAULT FALSE,
    attorney_client_privileged BOOLEAN DEFAULT FALSE,
    access_purpose VARCHAR(255),
    ip_address VARCHAR(45),
    accessed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_data_access_log_user_id ON data_access_log(user_id);
CREATE INDEX idx_data_access_log_accessed_at ON data_access_log(accessed_at);
CREATE INDEX idx_data_access_log_contains_pii ON data_access_log(contains_pii);

-- =============================================================================
-- FUNCTIONS AND TRIGGERS
-- =============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_cases_updated_at BEFORE UPDATE ON cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_sessions_updated_at BEFORE UPDATE ON ai_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- SAMPLE DATA (Optional - for development)
-- =============================================================================

-- Uncomment for development/testing
-- INSERT INTO cases (case_number, case_name, case_type, client_name, status, plaintiff, defendant)
-- VALUES
--   ('2024-CC-12345', 'Midland Credit v. Doe', 'debt_collection', 'John Doe', 'new', 'Midland Credit Management', 'John Doe'),
--   ('2024-CC-67890', 'ABC Collections v. Smith', 'debt_collection', 'Jane Smith', 'in_progress', 'ABC Collections Inc', 'Jane Smith');
