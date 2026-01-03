-- Legal AI System Database Schema
-- Create core tables for legal document management and AI processing

\c legalai_db;

SET search_path TO legalai, public;

-- Users and Authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'lawyer', 'paralegal', 'user')),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Clients and Organizations
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    client_type VARCHAR(50) DEFAULT 'individual' CHECK (client_type IN ('individual', 'corporation', 'partnership', 'llc', 'nonprofit')),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    address JSONB,
    tax_id VARCHAR(100),
    billing_address JSONB,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Legal Cases
CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_number VARCHAR(100) UNIQUE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    case_type VARCHAR(100) CHECK (case_type IN ('litigation', 'contract', 'compliance', 'corporate', 'employment', 'real_estate', 'intellectual_property')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'pending', 'closed', 'archived')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    client_id UUID REFERENCES clients(id),
    assigned_attorney_id UUID REFERENCES users(id),
    court_jurisdiction VARCHAR(200),
    filing_date DATE,
    expected_resolution_date DATE,
    actual_resolution_date DATE,
    billable_hours DECIMAL(10,2) DEFAULT 0,
    total_fees DECIMAL(12,2) DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Legal Documents
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    document_type VARCHAR(100) CHECK (document_type IN ('contract', 'brief', 'motion', 'pleading', 'correspondence', 'evidence', 'research', 'other')),
    file_name VARCHAR(255),
    file_path VARCHAR(1000),
    file_size BIGINT,
    mime_type VARCHAR(100),
    checksum VARCHAR(64),
    version INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'approved', 'executed', 'archived')),
    case_id UUID REFERENCES cases(id),
    client_id UUID REFERENCES clients(id),
    uploaded_by UUID REFERENCES users(id),
    content_text TEXT,
    content_vector TSVECTOR,
    extracted_metadata JSONB,
    ai_analysis JSONB,
    retention_date DATE,
    confidentiality_level VARCHAR(50) DEFAULT 'internal' CHECK (confidentiality_level IN ('public', 'internal', 'confidential', 'attorney_client')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ
);

-- Legal Citations
CREATE TABLE IF NOT EXISTS citations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id),
    citation_text VARCHAR(1000) NOT NULL,
    citation_type VARCHAR(50) CHECK (citation_type IN ('case_law', 'statute', 'regulation', 'constitutional', 'secondary')),
    jurisdiction VARCHAR(200),
    court_level VARCHAR(100),
    decision_date DATE,
    citation_format VARCHAR(50) DEFAULT 'bluebook',
    is_valid BOOLEAN DEFAULT true,
    verification_date TIMESTAMPTZ,
    parallel_citations TEXT[],
    case_name VARCHAR(500),
    volume INTEGER,
    reporter VARCHAR(100),
    page INTEGER,
    year INTEGER,
    pinpoint_citation VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Contract Analysis
CREATE TABLE IF NOT EXISTS contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id),
    contract_type VARCHAR(100) CHECK (contract_type IN ('service_agreement', 'employment', 'nda', 'lease', 'purchase', 'license', 'partnership', 'other')),
    parties JSONB NOT NULL,
    effective_date DATE,
    expiration_date DATE,
    auto_renewal BOOLEAN DEFAULT false,
    governing_law VARCHAR(200),
    total_value DECIMAL(15,2),
    currency VARCHAR(10) DEFAULT 'USD',
    key_terms JSONB,
    obligations JSONB,
    risk_assessment JSONB,
    compliance_status VARCHAR(50) DEFAULT 'pending' CHECK (compliance_status IN ('compliant', 'non_compliant', 'pending', 'review_required')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- AI Analysis Results
CREATE TABLE IF NOT EXISTS ai_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id),
    analysis_type VARCHAR(100) CHECK (analysis_type IN ('document_classification', 'sentiment_analysis', 'entity_extraction', 'contract_review', 'risk_assessment', 'compliance_check')),
    ai_model VARCHAR(100),
    model_version VARCHAR(50),
    confidence_score DECIMAL(5,4),
    analysis_results JSONB NOT NULL,
    processing_time_ms INTEGER,
    tokens_used INTEGER,
    cost DECIMAL(10,6),
    status VARCHAR(50) DEFAULT 'completed' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

-- Billing and Time Tracking
CREATE TABLE IF NOT EXISTS time_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID REFERENCES cases(id),
    user_id UUID REFERENCES users(id),
    description TEXT NOT NULL,
    hours DECIMAL(5,2) NOT NULL CHECK (hours > 0),
    billable_rate DECIMAL(8,2),
    total_amount DECIMAL(10,2) GENERATED ALWAYS AS (hours * COALESCE(billable_rate, 0)) STORED,
    entry_date DATE NOT NULL,
    billing_status VARCHAR(50) DEFAULT 'pending' CHECK (billing_status IN ('pending', 'billable', 'billed', 'non_billable')),
    task_category VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Audit Trail
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    user_id UUID REFERENCES users(id),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);

CREATE INDEX idx_clients_name ON clients USING GIN (name gin_trgm_ops);
CREATE INDEX idx_clients_type ON clients(client_type);
CREATE INDEX idx_clients_status ON clients(status);

CREATE INDEX idx_cases_number ON cases(case_number);
CREATE INDEX idx_cases_client_id ON cases(client_id);
CREATE INDEX idx_cases_attorney_id ON cases(assigned_attorney_id);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_type ON cases(case_type);
CREATE INDEX idx_cases_title ON cases USING GIN (title gin_trgm_ops);

CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_case_id ON documents(case_id);
CREATE INDEX idx_documents_client_id ON documents(client_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_content_vector ON documents USING GIN (content_vector);
CREATE INDEX idx_documents_title ON documents USING GIN (title gin_trgm_ops);
CREATE INDEX idx_documents_created_at ON documents(created_at);

CREATE INDEX idx_citations_document_id ON citations(document_id);
CREATE INDEX idx_citations_type ON citations(citation_type);
CREATE INDEX idx_citations_jurisdiction ON citations(jurisdiction);
CREATE INDEX idx_citations_text ON citations USING GIN (citation_text gin_trgm_ops);

CREATE INDEX idx_contracts_document_id ON contracts(document_id);
CREATE INDEX idx_contracts_type ON contracts(contract_type);
CREATE INDEX idx_contracts_effective_date ON contracts(effective_date);
CREATE INDEX idx_contracts_expiration_date ON contracts(expiration_date);

CREATE INDEX idx_ai_analyses_document_id ON ai_analyses(document_id);
CREATE INDEX idx_ai_analyses_type ON ai_analyses(analysis_type);
CREATE INDEX idx_ai_analyses_status ON ai_analyses(status);
CREATE INDEX idx_ai_analyses_created_at ON ai_analyses(created_at);

CREATE INDEX idx_time_entries_case_id ON time_entries(case_id);
CREATE INDEX idx_time_entries_user_id ON time_entries(user_id);
CREATE INDEX idx_time_entries_date ON time_entries(entry_date);
CREATE INDEX idx_time_entries_billing_status ON time_entries(billing_status);

CREATE INDEX idx_audit_logs_table_record ON audit_logs(table_name, record_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Create triggers for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cases_updated_at BEFORE UPDATE ON cases FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_citations_updated_at BEFORE UPDATE ON citations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_contracts_updated_at BEFORE UPDATE ON contracts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_time_entries_updated_at BEFORE UPDATE ON time_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for updating document content vector
CREATE OR REPLACE FUNCTION update_document_content_vector()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.content_text IS NOT NULL AND NEW.content_text != OLD.content_text THEN
        NEW.content_vector := to_tsvector('legal_english', NEW.content_text);
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_document_vector BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_document_content_vector();

-- Comments on tables
COMMENT ON TABLE users IS 'System users including lawyers, paralegals, and administrators';
COMMENT ON TABLE clients IS 'Client organizations and individuals';
COMMENT ON TABLE cases IS 'Legal cases and matters';
COMMENT ON TABLE documents IS 'Legal documents with AI analysis capabilities';
COMMENT ON TABLE citations IS 'Legal citations extracted from documents';
COMMENT ON TABLE contracts IS 'Contract-specific analysis and metadata';
COMMENT ON TABLE ai_analyses IS 'AI analysis results for legal documents';
COMMENT ON TABLE time_entries IS 'Billable time tracking for legal work';
COMMENT ON TABLE audit_logs IS 'Comprehensive audit trail for compliance';