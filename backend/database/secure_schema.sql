-- =============================================================================
-- LEGAL AI SYSTEM - SECURE DATABASE SCHEMA
-- =============================================================================
-- Enhanced security features:
-- - Field-level encryption for PII
-- - Audit trails for all modifications
-- - Row-level security support
-- - Data retention policies
-- - Attorney-client privilege protection
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- ENUMS FOR TYPE SAFETY
-- =============================================================================

CREATE TYPE user_role AS ENUM ('client', 'attorney', 'admin', 'staff');
CREATE TYPE case_status AS ENUM ('active', 'closed', 'archived', 'pending');
CREATE TYPE data_classification AS ENUM ('public', 'confidential', 'attorney_client_privileged', 'restricted');
CREATE TYPE access_level AS ENUM ('public', 'internal', 'confidential', 'restricted');

-- =============================================================================
-- USERS TABLE - Enhanced Security
-- =============================================================================

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Contact information (ENCRYPTED)
  email VARCHAR(255) UNIQUE NOT NULL,
  email_encrypted BYTEA, -- Encrypted version for PII compliance
  name VARCHAR(255) NOT NULL,
  phone VARCHAR(50),
  phone_encrypted BYTEA,

  -- Professional information
  role user_role DEFAULT 'client',
  bar_number VARCHAR(100),
  bar_number_encrypted BYTEA, -- SSN-equivalent, must encrypt
  bar_state VARCHAR(2),
  firm_name VARCHAR(255),

  -- Security & Access
  password_hash VARCHAR(255) NOT NULL,
  mfa_enabled BOOLEAN DEFAULT false,
  mfa_secret_encrypted BYTEA,
  failed_login_attempts INT DEFAULT 0,
  account_locked BOOLEAN DEFAULT false,
  last_login TIMESTAMP,
  password_changed_at TIMESTAMP DEFAULT NOW(),

  -- Audit trail
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  created_by UUID REFERENCES users(id),
  updated_by UUID REFERENCES users(id),

  -- Soft delete & retention
  deleted_at TIMESTAMP,
  deleted_by UUID REFERENCES users(id),
  retention_until DATE,

  -- Compliance
  gdpr_consent BOOLEAN DEFAULT false,
  gdpr_consent_date TIMESTAMP,
  data_classification data_classification DEFAULT 'confidential'
);

-- =============================================================================
-- CASES TABLE - Enhanced with Security & Compliance
-- =============================================================================

CREATE TABLE cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),

  -- Case identification
  case_number VARCHAR(255) UNIQUE NOT NULL,
  case_name VARCHAR(500) NOT NULL,
  court VARCHAR(255) NOT NULL,
  case_type VARCHAR(100) NOT NULL,
  status case_status DEFAULT 'active',

  -- Client information (ENCRYPTED)
  client_name VARCHAR(255),
  client_name_encrypted BYTEA,
  client_email VARCHAR(255),
  client_email_encrypted BYTEA,
  client_phone VARCHAR(50),
  client_phone_encrypted BYTEA,
  client_ssn_encrypted BYTEA, -- Never store unencrypted

  -- Case parties
  plaintiff_name VARCHAR(255),
  plaintiff_type VARCHAR(100),
  plaintiff_attorney VARCHAR(255),
  defendant_name VARCHAR(255),

  -- Important dates
  filed_date DATE,
  served_date DATE,
  response_deadline DATE,

  -- PACER integration
  pacer_enabled BOOLEAN DEFAULT false,
  pacer_case_id VARCHAR(255),
  last_pacer_check TIMESTAMP,

  -- AI Analysis (from Defense Builder)
  ai_analysis JSONB,
  defense_strategy JSONB,
  interview_complete BOOLEAN DEFAULT false,

  -- Security & Access Control
  access_level access_level DEFAULT 'confidential',
  attorney_client_privileged BOOLEAN DEFAULT true,
  data_classification data_classification DEFAULT 'attorney_client_privileged',

  -- Compliance tags
  contains_pii BOOLEAN DEFAULT true,
  requires_encryption BOOLEAN DEFAULT true,
  subject_to_retention_policy BOOLEAN DEFAULT true,
  retention_years INT DEFAULT 7, -- Legal industry standard

  -- Audit trail
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  created_by UUID REFERENCES users(id),
  updated_by UUID REFERENCES users(id),

  -- Soft delete
  deleted_at TIMESTAMP,
  deleted_by UUID REFERENCES users(id),
  deletion_reason TEXT,

  CONSTRAINT valid_retention CHECK (retention_years BETWEEN 1 AND 50)
);

-- =============================================================================
-- DOCUMENTS TABLE - Enhanced Security
-- =============================================================================

CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID REFERENCES cases(id) ON DELETE CASCADE,

  -- Document metadata
  filename VARCHAR(500) NOT NULL,
  filename_sanitized VARCHAR(500) NOT NULL, -- Security: sanitized filename
  document_type VARCHAR(100),
  file_path TEXT,
  file_path_encrypted TEXT, -- Encrypted storage path
  file_size_bytes BIGINT,
  file_hash_sha256 VARCHAR(64), -- Integrity verification

  -- Content (ENCRYPTED)
  document_text TEXT,
  document_text_encrypted BYTEA, -- Legal docs must be encrypted

  -- AI Processing
  ai_processed BOOLEAN DEFAULT false,
  ai_summary TEXT,
  extracted_deadlines JSONB,
  extracted_amounts JSONB,

  -- Security scanning
  virus_scanned BOOLEAN DEFAULT false,
  virus_scan_result VARCHAR(50),
  virus_scan_date TIMESTAMP,
  malware_detected BOOLEAN DEFAULT false,

  -- Source tracking
  source VARCHAR(50),
  pacer_doc_id VARCHAR(255),

  -- Security & Access
  access_level access_level DEFAULT 'confidential',
  attorney_client_privileged BOOLEAN DEFAULT false,
  data_classification data_classification DEFAULT 'confidential',
  encryption_key_id VARCHAR(255), -- Reference to encryption key
  encrypted_at TIMESTAMP,

  -- Audit trail
  uploaded_at TIMESTAMP DEFAULT NOW(),
  uploaded_by UUID REFERENCES users(id),
  accessed_count INT DEFAULT 0,
  last_accessed_at TIMESTAMP,
  last_accessed_by UUID REFERENCES users(id),

  -- Soft delete & retention
  deleted_at TIMESTAMP,
  deleted_by UUID REFERENCES users(id),
  retention_until DATE,

  CONSTRAINT valid_file_size CHECK (file_size_bytes > 0 AND file_size_bytes <= 104857600) -- 100MB max
);

-- =============================================================================
-- SESSIONS TABLE - Enhanced Security
-- =============================================================================

CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  case_id UUID REFERENCES cases(id),
  session_type VARCHAR(50),

  -- Session security
  session_token_hash VARCHAR(255) UNIQUE, -- Hashed token, never plaintext
  ip_address INET,
  user_agent TEXT,
  device_fingerprint VARCHAR(255),

  -- Context (may contain sensitive data - encrypt if needed)
  context JSONB DEFAULT '{}',
  context_encrypted BYTEA,
  interview_answers JSONB DEFAULT '{}',
  qa_history JSONB DEFAULT '[]',

  -- Session management
  active BOOLEAN DEFAULT true,
  expires_at TIMESTAMP NOT NULL,
  revoked BOOLEAN DEFAULT false,
  revoked_at TIMESTAMP,
  revoked_reason TEXT,

  -- Security flags
  suspicious_activity BOOLEAN DEFAULT false,
  geo_location JSONB,

  -- Audit trail
  created_at TIMESTAMP DEFAULT NOW(),
  last_activity TIMESTAMP DEFAULT NOW(),

  -- Auto-delete old sessions
  retention_until TIMESTAMP DEFAULT (NOW() + INTERVAL '30 days'),

  CONSTRAINT valid_expiry CHECK (expires_at > created_at)
);

-- =============================================================================
-- DEADLINES TABLE - Enhanced with Compliance
-- =============================================================================

CREATE TABLE deadlines (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID REFERENCES cases(id) ON DELETE CASCADE,

  deadline_type VARCHAR(100),
  description TEXT,
  due_date DATE NOT NULL,
  priority VARCHAR(20) DEFAULT 'normal',
  completed BOOLEAN DEFAULT false,
  completed_at TIMESTAMP,
  completed_by UUID REFERENCES users(id),

  -- Notification tracking
  notification_sent BOOLEAN DEFAULT false,
  notification_sent_at TIMESTAMP,

  -- Source tracking
  source VARCHAR(50),
  document_id UUID REFERENCES documents(id),
  confidence_score DECIMAL(3,2), -- AI confidence if extracted

  -- Audit trail
  created_at TIMESTAMP DEFAULT NOW(),
  created_by UUID REFERENCES users(id),
  updated_at TIMESTAMP DEFAULT NOW(),
  updated_by UUID REFERENCES users(id),

  -- Soft delete
  deleted_at TIMESTAMP,
  deleted_by UUID REFERENCES users(id)
);

-- =============================================================================
-- ACTIVITIES LOG - Comprehensive Audit Trail
-- =============================================================================

CREATE TABLE activities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- What was done
  activity_type VARCHAR(100) NOT NULL,
  action VARCHAR(50) NOT NULL, -- CREATE, READ, UPDATE, DELETE, EXPORT
  description TEXT,

  -- Who did it
  user_id UUID REFERENCES users(id),
  user_email VARCHAR(255),
  user_role user_role,

  -- Where it happened
  case_id UUID REFERENCES cases(id),
  document_id UUID REFERENCES documents(id),
  table_name VARCHAR(100),
  record_id UUID,

  -- When it happened
  created_at TIMESTAMP DEFAULT NOW(),

  -- How it happened
  ip_address INET,
  user_agent TEXT,
  session_id UUID REFERENCES sessions(id),

  -- Additional context
  metadata JSONB,
  old_values JSONB, -- Before change
  new_values JSONB, -- After change

  -- Security classification
  security_relevant BOOLEAN DEFAULT false,
  compliance_relevant BOOLEAN DEFAULT true,

  -- Retention (audit logs kept longer)
  retention_until TIMESTAMP DEFAULT (NOW() + INTERVAL '7 years')
);

-- =============================================================================
-- DATA ACCESS LOG - Track all PII/Privileged access
-- =============================================================================

CREATE TABLE data_access_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Who accessed
  user_id UUID REFERENCES users(id) NOT NULL,
  user_email VARCHAR(255),
  user_role user_role,

  -- What was accessed
  table_name VARCHAR(100) NOT NULL,
  record_id UUID NOT NULL,
  case_id UUID REFERENCES cases(id),
  document_id UUID REFERENCES documents(id),

  -- Access details
  access_type VARCHAR(50) NOT NULL, -- READ, EXPORT, DOWNLOAD, DECRYPT
  data_classification data_classification,
  contains_pii BOOLEAN,
  attorney_client_privileged BOOLEAN,

  -- Purpose (GDPR requirement)
  access_purpose TEXT,
  access_authorized BOOLEAN DEFAULT true,
  authorization_reference VARCHAR(255),

  -- Context
  ip_address INET,
  user_agent TEXT,
  accessed_at TIMESTAMP DEFAULT NOW(),

  -- Compliance
  gdpr_logged BOOLEAN DEFAULT true,
  hipaa_logged BOOLEAN DEFAULT false,

  -- Retention (keep access logs for 10 years)
  retention_until TIMESTAMP DEFAULT (NOW() + INTERVAL '10 years')
);

-- =============================================================================
-- SECURITY INCIDENTS - Track security events
-- =============================================================================

CREATE TABLE security_incidents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Incident details
  incident_type VARCHAR(100) NOT NULL, -- brute_force, data_breach, unauthorized_access
  severity VARCHAR(20) NOT NULL, -- LOW, MEDIUM, HIGH, CRITICAL
  title VARCHAR(500) NOT NULL,
  description TEXT,

  -- Affected resources
  user_id UUID REFERENCES users(id),
  case_id UUID REFERENCES cases(id),
  ip_address INET,

  -- Detection
  detected_at TIMESTAMP DEFAULT NOW(),
  detected_by VARCHAR(100), -- system, user, automated_scan

  -- Response
  status VARCHAR(50) DEFAULT 'open', -- open, investigating, resolved, false_positive
  assigned_to UUID REFERENCES users(id),
  resolved_at TIMESTAMP,
  resolution_notes TEXT,

  -- Compliance reporting
  requires_breach_notification BOOLEAN DEFAULT false,
  breach_notification_sent BOOLEAN DEFAULT false,
  regulatory_reporting_required BOOLEAN DEFAULT false,

  -- Evidence
  evidence JSONB,
  related_activities JSONB,

  created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- ENCRYPTION KEYS METADATA (NOT the actual keys!)
-- =============================================================================

CREATE TABLE encryption_keys_metadata (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  key_id VARCHAR(255) UNIQUE NOT NULL,
  key_type VARCHAR(50) NOT NULL, -- MASTER, DATA, SESSION
  algorithm VARCHAR(50) NOT NULL, -- AES-256-GCM, RSA-4096

  -- Key lifecycle
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  rotated_at TIMESTAMP,
  deprecated BOOLEAN DEFAULT false,

  -- Usage tracking
  encrypted_records_count BIGINT DEFAULT 0,
  last_used_at TIMESTAMP,

  -- Compliance
  fips_compliant BOOLEAN DEFAULT true,
  key_strength_bits INT NOT NULL,

  -- NOTE: Actual keys stored in secure key management system (Vault/KMS)
  key_storage_reference TEXT, -- Reference to external key vault

  CONSTRAINT valid_key_strength CHECK (key_strength_bits >= 256)
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE & SECURITY
-- =============================================================================

-- Primary indexes
CREATE INDEX idx_cases_user ON cases(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_documents_case ON documents(case_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_sessions_active ON sessions(user_id, active) WHERE active = true;
CREATE INDEX idx_deadlines_due ON deadlines(due_date, completed) WHERE completed = false;

-- Security indexes
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_sessions_token ON sessions(session_token_hash);
CREATE INDEX idx_sessions_expires ON sessions(expires_at) WHERE active = true;
CREATE INDEX idx_documents_privileged ON documents(case_id) WHERE attorney_client_privileged = true;

-- Audit indexes
CREATE INDEX idx_activities_user ON activities(user_id, created_at DESC);
CREATE INDEX idx_activities_case ON activities(case_id, created_at DESC);
CREATE INDEX idx_activities_security ON activities(created_at DESC) WHERE security_relevant = true;
CREATE INDEX idx_data_access_user ON data_access_log(user_id, accessed_at DESC);
CREATE INDEX idx_data_access_pii ON data_access_log(accessed_at DESC) WHERE contains_pii = true;
CREATE INDEX idx_security_incidents_open ON security_incidents(created_at DESC) WHERE status = 'open';

-- =============================================================================
-- ROW LEVEL SECURITY POLICIES
-- =============================================================================

-- Enable RLS on sensitive tables
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own cases
CREATE POLICY cases_user_isolation ON cases
  FOR ALL
  TO authenticated_user
  USING (user_id = current_setting('app.current_user_id')::UUID OR
         current_setting('app.user_role') = 'admin');

-- Policy: Documents inherit case access
CREATE POLICY documents_case_access ON documents
  FOR ALL
  TO authenticated_user
  USING (
    case_id IN (
      SELECT id FROM cases
      WHERE user_id = current_setting('app.current_user_id')::UUID
    )
  );

-- =============================================================================
-- AUTOMATIC AUDIT TRIGGERS
-- =============================================================================

CREATE OR REPLACE FUNCTION audit_log_changes()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO activities (
    activity_type,
    action,
    table_name,
    record_id,
    user_id,
    old_values,
    new_values,
    ip_address,
    created_at
  ) VALUES (
    TG_TABLE_NAME || '_' || TG_OP,
    TG_OP,
    TG_TABLE_NAME,
    COALESCE(NEW.id, OLD.id),
    current_setting('app.current_user_id', true)::UUID,
    to_jsonb(OLD),
    to_jsonb(NEW),
    current_setting('app.client_ip', true)::INET,
    NOW()
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to all critical tables
CREATE TRIGGER audit_users AFTER INSERT OR UPDATE OR DELETE ON users
  FOR EACH ROW EXECUTE FUNCTION audit_log_changes();

CREATE TRIGGER audit_cases AFTER INSERT OR UPDATE OR DELETE ON cases
  FOR EACH ROW EXECUTE FUNCTION audit_log_changes();

CREATE TRIGGER audit_documents AFTER INSERT OR UPDATE OR DELETE ON documents
  FOR EACH ROW EXECUTE FUNCTION audit_log_changes();

-- =============================================================================
-- AUTO-CLEANUP FUNCTIONS
-- =============================================================================

CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
  UPDATE sessions
  SET active = false, revoked = true, revoked_reason = 'expired'
  WHERE active = true
    AND expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Schedule: Run every hour (use pg_cron extension)
-- SELECT cron.schedule('cleanup-sessions', '0 * * * *', 'SELECT cleanup_expired_sessions()');

-- =============================================================================
-- DATA RETENTION ENFORCEMENT
-- =============================================================================

CREATE OR REPLACE FUNCTION enforce_data_retention()
RETURNS void AS $$
BEGIN
  -- Soft delete expired records
  UPDATE cases SET
    deleted_at = NOW(),
    deleted_by = '00000000-0000-0000-0000-000000000000'::UUID
  WHERE deleted_at IS NULL
    AND (created_at + (retention_years || ' years')::INTERVAL) < NOW();

  -- Hard delete very old audit logs (beyond legal requirement)
  DELETE FROM activities
  WHERE created_at < (NOW() - INTERVAL '10 years');
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE users IS 'User accounts with encrypted PII fields';
COMMENT ON TABLE cases IS 'Legal cases with attorney-client privilege protection';
COMMENT ON TABLE documents IS 'Encrypted legal documents with virus scanning';
COMMENT ON TABLE sessions IS 'Secure session management with token hashing';
COMMENT ON TABLE activities IS 'Comprehensive audit trail for compliance';
COMMENT ON TABLE data_access_log IS 'GDPR/HIPAA compliant access logging';
COMMENT ON TABLE security_incidents IS 'Security event tracking and breach notification';

COMMENT ON COLUMN users.email_encrypted IS 'PII: Encrypted email for GDPR compliance';
COMMENT ON COLUMN cases.client_ssn_encrypted IS 'CRITICAL: SSN must never be stored unencrypted';
COMMENT ON COLUMN documents.document_text_encrypted IS 'Attorney-client privileged content encrypted';
COMMENT ON COLUMN sessions.session_token_hash IS 'SECURITY: Only hash stored, never plaintext token';
