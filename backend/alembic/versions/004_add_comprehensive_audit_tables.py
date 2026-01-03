"""Add comprehensive audit tables

Revision ID: 004_comprehensive_audit
Revises: 003_add_adversarial_simulation_tables
Create Date: 2024-12-19

This migration adds comprehensive audit tables for:
- AI response logging
- Hallucination audit trails
- Document access tracking
- Admin action logging
- Search query analytics
- API usage tracking
- User session activity
- Error logging
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_comprehensive_audit'
down_revision = '003_add_adversarial_simulation_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE aimodelprovider AS ENUM ('openai', 'anthropic', 'local', 'hybrid');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE aianalysistype AS ENUM (
                'document_summary', 'document_extraction', 'legal_research',
                'case_analysis', 'citation_validation', 'risk_assessment',
                'defense_generation', 'qa_response', 'multi_layer_analysis'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE hallucinationtype AS ENUM (
                'fabricated_party', 'fabricated_date', 'fabricated_amount',
                'fabricated_citation', 'fabricated_case_number', 'incorrect_fact',
                'unsupported_claim', 'misattribution', 'context_confusion', 'other'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE hallucinationseverity AS ENUM ('low', 'medium', 'high', 'critical');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE correctionaction AS ENUM ('removed', 'corrected', 'flagged', 'verified_accurate');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE documentaccesstype AS ENUM (
                'view', 'download', 'print', 'share', 'export', 'analyze', 'edit', 'delete', 'restore'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE adminactiontype AS ENUM (
                'user_create', 'user_update', 'user_delete', 'user_suspend', 'user_restore',
                'user_impersonate', 'role_assign', 'role_revoke', 'permission_grant',
                'permission_revoke', 'config_change', 'data_export', 'data_delete',
                'audit_view', 'system_restart', 'credits_adjust', 'refund_issue',
                'legal_hold', 'api_key_generate', 'api_key_revoke'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # AI Response Logs table
    op.create_table(
        'ai_response_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('request_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('correlation_id', sa.String(64), nullable=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('user_email', sa.String(255), nullable=True),
        sa.Column('session_id', sa.String(128), nullable=True),
        sa.Column('source_ip', postgresql.INET(), nullable=True),
        sa.Column('document_id', sa.Integer(), nullable=True, index=True),
        sa.Column('document_name', sa.String(500), nullable=True),
        sa.Column('document_type', sa.String(100), nullable=True),
        sa.Column('document_hash', sa.String(64), nullable=True),
        sa.Column('analysis_type', sa.Enum('document_summary', 'document_extraction', 'legal_research',
                  'case_analysis', 'citation_validation', 'risk_assessment', 'defense_generation',
                  'qa_response', 'multi_layer_analysis', name='aianalysistype'), nullable=False, index=True),
        sa.Column('model_provider', sa.Enum('openai', 'anthropic', 'local', 'hybrid', name='aimodelprovider'), nullable=False, index=True),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('prompt_template', sa.Text(), nullable=True),
        sa.Column('input_text', sa.Text(), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('input_parameters', postgresql.JSONB(), nullable=True),
        sa.Column('raw_response', sa.Text(), nullable=False),
        sa.Column('processed_response', postgresql.JSONB(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('hallucination_count', sa.Integer(), default=0),
        sa.Column('correction_count', sa.Integer(), default=0),
        sa.Column('post_processing_applied', postgresql.JSONB(), nullable=True),
        sa.Column('final_output', postgresql.JSONB(), nullable=True),
        sa.Column('estimated_cost', sa.Numeric(10, 6), nullable=True),
        sa.Column('actual_cost', sa.Numeric(10, 6), nullable=True),
        sa.Column('request_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('response_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, default=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('api_version', sa.String(20), nullable=True),
        sa.Column('request_headers', postgresql.JSONB(), nullable=True),
    )

    op.create_index('ix_ai_response_user_time', 'ai_response_logs', ['user_id', 'request_timestamp'])
    op.create_index('ix_ai_response_doc_time', 'ai_response_logs', ['document_id', 'request_timestamp'])
    op.create_index('ix_ai_response_type_time', 'ai_response_logs', ['analysis_type', 'request_timestamp'])
    op.create_index('ix_ai_response_provider_time', 'ai_response_logs', ['model_provider', 'request_timestamp'])

    # Hallucination Audits table
    op.create_table(
        'hallucination_audits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ai_response_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ai_response_logs.id'), nullable=True, index=True),
        sa.Column('hallucination_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('hallucination_type', sa.Enum('fabricated_party', 'fabricated_date', 'fabricated_amount',
                  'fabricated_citation', 'fabricated_case_number', 'incorrect_fact', 'unsupported_claim',
                  'misattribution', 'context_confusion', 'other', name='hallucinationtype'), nullable=False, index=True),
        sa.Column('severity', sa.Enum('low', 'medium', 'high', 'critical', name='hallucinationseverity'), nullable=False, index=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('field_name', sa.String(255), nullable=False),
        sa.Column('field_path', sa.String(500), nullable=True),
        sa.Column('section', sa.String(255), nullable=True),
        sa.Column('line_number', sa.Integer(), nullable=True),
        sa.Column('original_value', postgresql.JSONB(), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=True),
        sa.Column('source_layer', sa.String(100), nullable=False),
        sa.Column('source_prompt_excerpt', sa.Text(), nullable=True),
        sa.Column('source_document_excerpt', sa.Text(), nullable=True),
        sa.Column('detection_method', sa.String(100), nullable=False),
        sa.Column('detection_layer', sa.String(100), nullable=False),
        sa.Column('detection_rule', sa.String(255), nullable=True),
        sa.Column('detection_confidence', sa.Float(), nullable=False),
        sa.Column('detection_reasoning', sa.Text(), nullable=True),
        sa.Column('cross_validation_performed', sa.Boolean(), default=False),
        sa.Column('cross_validation_sources', postgresql.JSONB(), nullable=True),
        sa.Column('cross_validation_results', postgresql.JSONB(), nullable=True),
        sa.Column('correction_action', sa.Enum('removed', 'corrected', 'flagged', 'verified_accurate', name='correctionaction'), nullable=False),
        sa.Column('corrected_value', postgresql.JSONB(), nullable=True),
        sa.Column('corrected_text', sa.Text(), nullable=True),
        sa.Column('correction_source', sa.String(255), nullable=True),
        sa.Column('correction_reasoning', sa.Text(), nullable=True),
        sa.Column('impact_assessment', sa.Text(), nullable=True),
        sa.Column('affected_downstream', postgresql.JSONB(), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('corrected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('shown_to_user', sa.Boolean(), default=False),
        sa.Column('user_notified', sa.Boolean(), default=False),
        sa.Column('user_acknowledged', sa.Boolean(), default=False),
        sa.Column('user_feedback', sa.Text(), nullable=True),
    )

    op.create_index('ix_halluc_response_time', 'hallucination_audits', ['ai_response_id', 'detected_at'])
    op.create_index('ix_halluc_type_severity', 'hallucination_audits', ['hallucination_type', 'severity'])
    op.create_index('ix_halluc_field', 'hallucination_audits', ['field_name'])
    op.create_index('ix_halluc_detection', 'hallucination_audits', ['detection_method', 'detection_layer'])

    # Document Access Logs table
    op.create_table(
        'document_access_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('access_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('user_role', sa.String(50), nullable=True),
        sa.Column('session_id', sa.String(128), nullable=True),
        sa.Column('document_id', sa.Integer(), nullable=False, index=True),
        sa.Column('document_name', sa.String(500), nullable=False),
        sa.Column('document_type', sa.String(100), nullable=True),
        sa.Column('document_hash', sa.String(64), nullable=True),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('access_type', sa.Enum('view', 'download', 'print', 'share', 'export', 'analyze', 'edit', 'delete', 'restore', name='documentaccesstype'), nullable=False, index=True),
        sa.Column('access_method', sa.String(100), nullable=True),
        sa.Column('access_reason', sa.Text(), nullable=True),
        sa.Column('case_id', sa.Integer(), nullable=True, index=True),
        sa.Column('case_name', sa.String(500), nullable=True),
        sa.Column('matter_id', sa.String(100), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=True),
        sa.Column('source_ip', postgresql.INET(), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_fingerprint', sa.String(128), nullable=True),
        sa.Column('api_endpoint', sa.String(255), nullable=True),
        sa.Column('shared_with', postgresql.JSONB(), nullable=True),
        sa.Column('export_format', sa.String(50), nullable=True),
        sa.Column('modification_type', sa.String(100), nullable=True),
        sa.Column('before_state', postgresql.JSONB(), nullable=True),
        sa.Column('after_state', postgresql.JSONB(), nullable=True),
        sa.Column('accessed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, default=True),
        sa.Column('bytes_transferred', sa.BigInteger(), nullable=True),
        sa.Column('pages_viewed', sa.Integer(), nullable=True),
    )

    op.create_index('ix_doc_access_user_time', 'document_access_logs', ['user_id', 'accessed_at'])
    op.create_index('ix_doc_access_doc_time', 'document_access_logs', ['document_id', 'accessed_at'])
    op.create_index('ix_doc_access_type_time', 'document_access_logs', ['access_type', 'accessed_at'])
    op.create_index('ix_doc_access_case', 'document_access_logs', ['case_id', 'accessed_at'])

    # Admin Action Logs table
    op.create_table(
        'admin_action_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('action_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('admin_id', sa.Integer(), nullable=False, index=True),
        sa.Column('admin_email', sa.String(255), nullable=False),
        sa.Column('admin_role', sa.String(50), nullable=False),
        sa.Column('action_type', sa.Enum('user_create', 'user_update', 'user_delete', 'user_suspend', 'user_restore',
                  'user_impersonate', 'role_assign', 'role_revoke', 'permission_grant', 'permission_revoke',
                  'config_change', 'data_export', 'data_delete', 'audit_view', 'system_restart',
                  'credits_adjust', 'refund_issue', 'legal_hold', 'api_key_generate', 'api_key_revoke',
                  name='adminactiontype'), nullable=False, index=True),
        sa.Column('action_description', sa.Text(), nullable=False),
        sa.Column('target_type', sa.String(100), nullable=False),
        sa.Column('target_id', sa.String(255), nullable=True, index=True),
        sa.Column('target_name', sa.String(500), nullable=True),
        sa.Column('before_state', postgresql.JSONB(), nullable=True),
        sa.Column('after_state', postgresql.JSONB(), nullable=True),
        sa.Column('changes_made', postgresql.JSONB(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('ticket_number', sa.String(100), nullable=True),
        sa.Column('authorization_reference', sa.String(255), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), default=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_notes', sa.Text(), nullable=True),
        sa.Column('source_ip', postgresql.INET(), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(128), nullable=True),
        sa.Column('performed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False, default=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('reversible', sa.Boolean(), default=True),
        sa.Column('reversed', sa.Boolean(), default=False),
        sa.Column('reversed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reversed_by', sa.Integer(), nullable=True),
        sa.Column('reversal_reason', sa.Text(), nullable=True),
    )

    op.create_index('ix_admin_action_admin_time', 'admin_action_logs', ['admin_id', 'performed_at'])
    op.create_index('ix_admin_action_target_time', 'admin_action_logs', ['target_type', 'target_id', 'performed_at'])
    op.create_index('ix_admin_action_type_time', 'admin_action_logs', ['action_type', 'performed_at'])

    # Search Query Logs table
    op.create_table(
        'search_query_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('query_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('session_id', sa.String(128), nullable=True),
        sa.Column('source_ip', postgresql.INET(), nullable=True),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_type', sa.String(100), nullable=False),
        sa.Column('search_filters', postgresql.JSONB(), nullable=True),
        sa.Column('search_parameters', postgresql.JSONB(), nullable=True),
        sa.Column('results_count', sa.Integer(), nullable=False, default=0),
        sa.Column('results_returned', sa.Integer(), nullable=True),
        sa.Column('top_result_ids', postgresql.JSONB(), nullable=True),
        sa.Column('result_clicked', sa.Boolean(), default=False),
        sa.Column('clicked_result_id', sa.String(255), nullable=True),
        sa.Column('clicked_position', sa.Integer(), nullable=True),
        sa.Column('search_time_ms', sa.Integer(), nullable=True),
        sa.Column('searched_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index('ix_search_user_time', 'search_query_logs', ['user_id', 'searched_at'])
    op.create_index('ix_search_type_time', 'search_query_logs', ['query_type', 'searched_at'])
    op.create_index('ix_search_results', 'search_query_logs', ['results_count', 'searched_at'])

    # API Usage Logs table
    op.create_table(
        'api_usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('request_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('api_key_id', sa.String(64), nullable=True, index=True),
        sa.Column('endpoint', sa.String(255), nullable=False, index=True),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('path_params', postgresql.JSONB(), nullable=True),
        sa.Column('query_params', postgresql.JSONB(), nullable=True),
        sa.Column('request_size_bytes', sa.Integer(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_size_bytes', sa.Integer(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=False),
        sa.Column('source_ip', postgresql.INET(), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('credits_used', sa.Numeric(10, 4), nullable=True),
        sa.Column('billing_category', sa.String(100), nullable=True),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index('ix_api_usage_user_time', 'api_usage_logs', ['user_id', 'requested_at'])
    op.create_index('ix_api_usage_endpoint_time', 'api_usage_logs', ['endpoint', 'requested_at'])
    op.create_index('ix_api_usage_status', 'api_usage_logs', ['status_code', 'requested_at'])

    # User Session Activities table
    op.create_table(
        'user_session_activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', sa.String(128), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('activity_type', sa.String(100), nullable=False),
        sa.Column('activity_name', sa.String(255), nullable=False),
        sa.Column('activity_details', postgresql.JSONB(), nullable=True),
        sa.Column('page_path', sa.String(500), nullable=True),
        sa.Column('page_title', sa.String(255), nullable=True),
        sa.Column('referrer', sa.String(500), nullable=True),
        sa.Column('source_ip', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('activity_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
    )

    op.create_index('ix_session_activity_user_time', 'user_session_activities', ['user_id', 'activity_at'])
    op.create_index('ix_session_activity_session_time', 'user_session_activities', ['session_id', 'activity_at'])

    # Error Logs table
    op.create_table(
        'error_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('error_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('session_id', sa.String(128), nullable=True),
        sa.Column('request_id', sa.String(64), nullable=True, index=True),
        sa.Column('error_type', sa.String(255), nullable=False, index=True),
        sa.Column('error_code', sa.String(50), nullable=True, index=True),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('error_stack_trace', sa.Text(), nullable=True),
        sa.Column('component', sa.String(100), nullable=False),
        sa.Column('module', sa.String(255), nullable=True),
        sa.Column('function_name', sa.String(255), nullable=True),
        sa.Column('line_number', sa.Integer(), nullable=True),
        sa.Column('endpoint', sa.String(255), nullable=True),
        sa.Column('method', sa.String(10), nullable=True),
        sa.Column('request_data', postgresql.JSONB(), nullable=True),
        sa.Column('environment', sa.String(50), nullable=True),
        sa.Column('server_id', sa.String(100), nullable=True),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('source_ip', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(20), nullable=False, default='error'),
        sa.Column('affected_users', sa.Integer(), nullable=True),
        sa.Column('acknowledged', sa.Boolean(), default=False),
        sa.Column('acknowledged_by', sa.Integer(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved', sa.Boolean(), default=False),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index('ix_error_type_time', 'error_logs', ['error_type', 'occurred_at'])
    op.create_index('ix_error_severity_time', 'error_logs', ['severity', 'occurred_at'])
    op.create_index('ix_error_resolved', 'error_logs', ['resolved', 'occurred_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('error_logs')
    op.drop_table('user_session_activities')
    op.drop_table('api_usage_logs')
    op.drop_table('search_query_logs')
    op.drop_table('admin_action_logs')
    op.drop_table('document_access_logs')
    op.drop_table('hallucination_audits')
    op.drop_table('ai_response_logs')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS adminactiontype')
    op.execute('DROP TYPE IF EXISTS documentaccesstype')
    op.execute('DROP TYPE IF EXISTS correctionaction')
    op.execute('DROP TYPE IF EXISTS hallucinationseverity')
    op.execute('DROP TYPE IF EXISTS hallucinationtype')
    op.execute('DROP TYPE IF EXISTS aianalysistype')
    op.execute('DROP TYPE IF EXISTS aimodelprovider')
