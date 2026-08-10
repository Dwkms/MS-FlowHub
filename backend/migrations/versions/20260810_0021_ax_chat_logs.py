"""add AX chat log table

Revision ID: 20260810_0021
Revises: 20260808_0020
Create Date: 2026-08-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260810_0021"
down_revision: str | None = "20260808_0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ax_chat_logs",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("result_type", sa.String(length=20), nullable=False),
        sa.Column("matched_type", sa.String(length=20), nullable=True),
        sa.Column("matched_id", sa.String(length=50), nullable=True),
        sa.Column("top_score", sa.Float(), nullable=True),
        sa.Column("top_candidates", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ax_chat_logs_result_created",
        "ax_chat_logs",
        ["result_type", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ax_chat_logs_result_created", table_name="ax_chat_logs")
    op.drop_table("ax_chat_logs")
