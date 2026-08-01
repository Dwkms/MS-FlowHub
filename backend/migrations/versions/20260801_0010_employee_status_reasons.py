"""add employee status reasons

Revision ID: 20260801_0010
Revises: 20260801_0009
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260801_0010"
down_revision: str | None = "20260801_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("employees", sa.Column("employment_status_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("employees", "employment_status_reason")
