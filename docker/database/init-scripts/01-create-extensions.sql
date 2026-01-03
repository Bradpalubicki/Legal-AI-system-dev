-- Legal AI System Database Extensions
-- Initialize PostgreSQL extensions for legal document processing

-- Enable UUID extension for generating unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable full-text search capabilities for legal documents
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Enable fuzzy string matching for legal citations
CREATE EXTENSION IF NOT EXISTS "fuzzystrmatch";

-- Enable unaccent for text normalization in legal documents
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Enable btree_gin for advanced indexing
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Enable pg_stat_statements for query performance monitoring
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Enable pgcrypto for encryption capabilities
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom schema for legal AI system
CREATE SCHEMA IF NOT EXISTS legalai;

-- Set search path to include legal AI schema
ALTER DATABASE legalai_db SET search_path TO legalai, public;

-- Create custom text search configuration for legal documents
CREATE TEXT SEARCH CONFIGURATION legal_english (COPY = english);

-- Custom dictionary for legal terms
CREATE TEXT SEARCH DICTIONARY legal_dict (
    TEMPLATE = simple,
    STOPWORDS = legal_stopwords,
    ACCEPT = false
);

-- Comments
COMMENT ON EXTENSION "uuid-ossp" IS 'UUID generation functions for legal document identifiers';
COMMENT ON EXTENSION "pg_trgm" IS 'Trigram matching for legal document search';
COMMENT ON EXTENSION "fuzzystrmatch" IS 'Fuzzy string matching for legal citations';
COMMENT ON EXTENSION "unaccent" IS 'Text normalization for legal documents';
COMMENT ON EXTENSION "btree_gin" IS 'Advanced indexing for legal document queries';
COMMENT ON EXTENSION "pg_stat_statements" IS 'Query performance monitoring';
COMMENT ON EXTENSION "pgcrypto" IS 'Encryption for sensitive legal data';

COMMENT ON SCHEMA legalai IS 'Legal AI System main schema for legal document processing';
COMMENT ON TEXT SEARCH CONFIGURATION legal_english IS 'Custom full-text search configuration optimized for legal documents';