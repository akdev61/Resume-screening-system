"""make files column nullable and backfill

Revision ID: 0002_make_files_nullable
Revises: 0001_add_resume_columns
Create Date: 2026-06-18 00:00:00.000001
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_make_files_nullable'
down_revision = '0001_add_resume_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Backfill: if filename exists and files is NULL, copy filename into files
    op.execute(
        "UPDATE resumes SET files = filename WHERE files IS NULL AND filename IS NOT NULL;"
    )
    # Make the column nullable so new inserts that don't set it won't fail
    op.alter_column('resumes', 'files', existing_type=sa.TEXT(), nullable=True)


def downgrade() -> None:
    # Revert: attempt to set any NULL files to empty string, then set NOT NULL
    op.execute("UPDATE resumes SET files = '' WHERE files IS NULL;")
    op.alter_column('resumes', 'files', existing_type=sa.TEXT(), nullable=False)
