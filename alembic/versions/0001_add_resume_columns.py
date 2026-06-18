"""add resume columns

Revision ID: 0001_add_resume_columns
Revises: 
Create Date: 2026-06-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_resume_columns'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use IF NOT EXISTS so running this migration multiple times is idempotent
    op.execute(
        """
        ALTER TABLE resumes
        ADD COLUMN IF NOT EXISTS filename VARCHAR(255),
        ADD COLUMN IF NOT EXISTS stored_path VARCHAR(500),
        ADD COLUMN IF NOT EXISTS extracted_text TEXT;
        """
    )
    # uploaded_at may already exist; add it only if missing
    op.execute(
        "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT now();"
    )


def downgrade() -> None:
    op.drop_column('resumes', 'uploaded_at')
    op.drop_column('resumes', 'extracted_text')
    op.drop_column('resumes', 'stored_path')
    op.drop_column('resumes', 'filename')
