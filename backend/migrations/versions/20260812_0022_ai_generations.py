"""add ai_generations table

Revision ID: 20260812_0022
Revises: 20260810_0021
Create Date: 2026-08-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260812_0022"
down_revision: str | None = "20260810_0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_generations",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("feature_type", sa.String(length=40), nullable=False),
        sa.Column("related_type", sa.String(length=40), nullable=True),
        sa.Column("related_id", sa.String(length=50), nullable=True),
        sa.Column("source_input", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("generated_output", sa.JSON(), nullable=True),
        sa.Column("final_output", sa.JSON(), nullable=True),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("created_by_id", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_generations_feature_created",
        "ai_generations",
        ["feature_type", "created_at"],
    )
    op.create_index(
        "ix_ai_generations_related",
        "ai_generations",
        ["related_type", "related_id"],
    )
    # 일일 호출 제한 조회용.
    op.create_index(
        "ix_ai_generations_creator_created",
        "ai_generations",
        ["created_by_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ai_generations_creator_created", table_name="ai_generations")
    op.drop_index("ix_ai_generations_related", table_name="ai_generations")
    op.drop_index("ix_ai_generations_feature_created", table_name="ai_generations")
    op.drop_table("ai_generations")
