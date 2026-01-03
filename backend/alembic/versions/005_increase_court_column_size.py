"""Increase court column size in case_notifications

Revision ID: 005_court_size
Revises: 004_comprehensive_audit
Create Date: 2025-12-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_court_size'
down_revision = '004_comprehensive_audit'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Increase court column from VARCHAR(50) to VARCHAR(255)"""
    # Use raw SQL for idempotent PostgreSQL execution
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # PostgreSQL: ALTER COLUMN is idempotent, just set to 255
        op.execute("""
            DO $$
            BEGIN
                ALTER TABLE case_notifications ALTER COLUMN court TYPE VARCHAR(255);
            EXCEPTION
                WHEN undefined_column THEN NULL;
                WHEN undefined_table THEN NULL;
            END $$;
        """)
    else:
        # SQLite: Use batch mode
        with op.batch_alter_table('case_notifications') as batch_op:
            batch_op.alter_column(
                'court',
                existing_type=sa.String(50),
                type_=sa.String(255),
                existing_nullable=True
            )


def downgrade() -> None:
    """Revert court column to VARCHAR(50)"""
    with op.batch_alter_table('case_notifications') as batch_op:
        batch_op.alter_column(
            'court',
            existing_type=sa.String(255),
            type_=sa.String(50),
            existing_nullable=True
        )
