"""Establish the SwarVox foundation migration baseline.

Revision ID: 20260928_0001
Revises:
Create Date: 2026-09-28 00:00:00
"""

revision = "20260928_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The foundation has no domain tables yet. Alembic records this revision so
    # later business-scoped schema changes have a single, explicit baseline.
    pass


def downgrade() -> None:
    pass
