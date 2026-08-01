"""add daily attendance records

Revision ID: 20260801_0007
Revises: 20260801_0006
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260801_0007"
down_revision: str | None = "20260801_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "attendance_records",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("employee_id", sa.String(length=50), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("work_status", sa.String(length=30), nullable=False),
        sa.Column("check_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("check_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "work_date", name="uq_attendance_employee_date"),
    )
    op.create_index("ix_attendance_records_work_date", "attendance_records", ["work_date"])
    op.create_index("ix_attendance_records_employee_id", "attendance_records", ["employee_id"])


def downgrade() -> None:
    op.drop_index("ix_attendance_records_employee_id", table_name="attendance_records")
    op.drop_index("ix_attendance_records_work_date", table_name="attendance_records")
    op.drop_table("attendance_records")
