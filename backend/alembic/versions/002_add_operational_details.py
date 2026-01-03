"""Add operational_details column to documents table

Revision ID: 002
Revises: 001
Create Date: 2025-10-23

This migration adds the operational_details JSON column to store
enhanced extraction data including action items, obligations,
contacts, jurisdiction details, and more.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '002_add_operational_details'
down_revision = '001_performance_indexes'  # Depends on performance indexes migration
branch_labels = None
depends_on = None


def upgrade():
    """Add operational_details column to documents table"""
    # Add the new column
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('operational_details', sa.JSON(), nullable=True)
        )


def downgrade():
    """Remove operational_details column from documents table"""
    # Remove the column
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.drop_column('operational_details')
