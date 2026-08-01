"""add structured employee status reasons

Revision ID: 20260801_0011
Revises: 20260801_0010
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260801_0011"
down_revision: str | None = "20260801_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table_name, columns in {
        "attendance_records": (
            sa.Column("reason_category", sa.String(length=30), nullable=True),
            sa.Column("reason_summary", sa.String(length=200), nullable=True),
            sa.Column("private_note", sa.Text(), nullable=True),
            sa.Column("reason_registered_by_id", sa.String(length=50), nullable=True),
            sa.Column("reason_registered_at", sa.DateTime(timezone=True), nullable=True),
        ),
        "employees": (
            sa.Column("employment_status_reason_category", sa.String(length=30), nullable=True),
            sa.Column("employment_status_reason_summary", sa.String(length=200), nullable=True),
            sa.Column("employment_status_private_note", sa.Text(), nullable=True),
            sa.Column(
                "employment_status_reason_registered_by_id", sa.String(length=50), nullable=True
            ),
            sa.Column(
                "employment_status_reason_registered_at", sa.DateTime(timezone=True), nullable=True
            ),
            sa.Column("employment_status_effective_from", sa.Date(), nullable=True),
        ),
    }.items():
        for column in columns:
            op.add_column(table_name, column)
    op.execute(
        sa.text(
            "UPDATE attendance_records SET reason_summary = note "
            "WHERE reason_summary IS NULL AND note IS NOT NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE employees SET employment_status_reason_summary = employment_status_reason "
            "WHERE employment_status_reason_summary IS NULL "
            "AND employment_status_reason IS NOT NULL"
        )
    )


def downgrade() -> None:
    for table_name, columns in {
        "employees": (
            "employment_status_effective_from",
            "employment_status_reason_registered_at",
            "employment_status_reason_registered_by_id",
            "employment_status_private_note",
            "employment_status_reason_summary",
            "employment_status_reason_category",
        ),
        "attendance_records": (
            "reason_registered_at",
            "reason_registered_by_id",
            "private_note",
            "reason_summary",
            "reason_category",
        ),
    }.items():
        for column_name in columns:
            op.drop_column(table_name, column_name)
