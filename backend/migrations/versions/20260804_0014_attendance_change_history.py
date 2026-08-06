"""add attendance change history

Revision ID: 20260804_0014
Revises: 20260803_0013
Create Date: 2026-08-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260804_0014"
down_revision: str | None = "20260803_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "attendance_change_histories",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("attendance_record_id", sa.String(length=50), nullable=False),
        sa.Column("before_work_status", sa.String(length=30), nullable=True),
        sa.Column("after_work_status", sa.String(length=30), nullable=False),
        sa.Column("before_reason_category", sa.String(length=30), nullable=True),
        sa.Column("after_reason_category", sa.String(length=30), nullable=True),
        sa.Column("before_reason_summary", sa.String(length=200), nullable=True),
        sa.Column("after_reason_summary", sa.String(length=200), nullable=True),
        sa.Column("before_private_note", sa.Text(), nullable=True),
        sa.Column("after_private_note", sa.Text(), nullable=True),
        sa.Column("changed_by_id", sa.String(length=50), nullable=False),
        sa.Column(
            "changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["attendance_record_id"], ["attendance_records.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["changed_by_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_attendance_change_history_record_changed",
        "attendance_change_histories",
        ["attendance_record_id", "changed_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_attendance_change_history_record_changed", table_name="attendance_change_histories"
    )
    op.drop_table("attendance_change_histories")
