"""add recruitment request poster metadata

Revision ID: 20260731_0005
Revises: 20260731_0004
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260731_0005"
down_revision: str | None = "20260731_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "recruitment_requests",
        sa.Column("poster_original_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "recruitment_requests",
        sa.Column("poster_stored_name", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "recruitment_requests",
        sa.Column("poster_content_type", sa.String(length=100), nullable=True),
    )
    op.add_column("recruitment_requests", sa.Column("poster_size", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("recruitment_requests", "poster_size")
    op.drop_column("recruitment_requests", "poster_content_type")
    op.drop_column("recruitment_requests", "poster_stored_name")
    op.drop_column("recruitment_requests", "poster_original_name")
