"""Add adversarial simulation tables

Revision ID: 003
Revises: 002_add_operational_details
Create Date: 2025-12-16

This migration creates the adversarial_simulations and counter_arguments
tables for the opposing counsel analysis feature.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_add_adversarial_simulation_tables'
down_revision = '002_add_operational_details'
branch_labels = None
depends_on = None


def upgrade():
    """Create adversarial simulation tables"""

    # Create adversarial_simulations table
    op.create_table(
        'adversarial_simulations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('defense_session_id', sa.String(36), sa.ForeignKey('defense_sessions.id'), nullable=False, index=True),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('progress', sa.Integer(), default=0),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('case_type', sa.String(100)),
        sa.Column('collected_facts', sa.JSON(), default=dict),
        sa.Column('counter_arguments_summary', sa.JSON(), default=list),
        sa.Column('weaknesses', sa.JSON(), default=list),
        sa.Column('overall_strength', sa.String(20)),
        sa.Column('recommendations', sa.JSON(), default=list),
        sa.Column('error_message', sa.Text()),
        sa.Column('max_counter_arguments', sa.Integer(), default=3),
    )

    # Create counter_arguments table
    op.create_table(
        'counter_arguments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('simulation_id', sa.String(36), sa.ForeignKey('adversarial_simulations.id'), nullable=False, index=True),
        sa.Column('argument_title', sa.String(500), nullable=False),
        sa.Column('argument_description', sa.Text(), nullable=False),
        sa.Column('legal_basis', sa.Text()),
        sa.Column('likelihood', sa.String(20), nullable=False),
        sa.Column('likelihood_score', sa.Integer(), default=50),
        sa.Column('likelihood_reasoning', sa.Text()),
        sa.Column('category', sa.String(50)),
        sa.Column('evidence_to_support', sa.JSON(), default=list),
        sa.Column('rebuttals', sa.JSON(), default=list),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime()),
    )

    # Create indexes for better query performance
    op.create_index('ix_adversarial_simulations_status', 'adversarial_simulations', ['status'])
    op.create_index('ix_counter_arguments_likelihood', 'counter_arguments', ['likelihood_score'])


def downgrade():
    """Drop adversarial simulation tables"""

    # Drop indexes
    op.drop_index('ix_counter_arguments_likelihood', 'counter_arguments')
    op.drop_index('ix_adversarial_simulations_status', 'adversarial_simulations')

    # Drop tables
    op.drop_table('counter_arguments')
    op.drop_table('adversarial_simulations')
