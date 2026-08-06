"""add ATS applicants and stage histories

Revision ID: 20260805_0015
Revises: 20260804_0014
Create Date: 2026-08-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260805_0015"
down_revision: str | None = "20260804_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "applicants",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_posting_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("career_summary", sa.Text(), nullable=False),
        sa.Column("stage", sa.String(length=20), nullable=False),
        sa.Column("created_by_id", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "stage IN ('APPLIED','SCREENING','INTERVIEW','OFFERED','HIRED','REJECTED')",
            name="ck_applicants_stage",
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["job_posting_id"], ["job_postings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_posting_id", "email", name="uq_applicants_posting_email"),
    )
    op.create_index("ix_applicants_job_posting_id", "applicants", ["job_posting_id"])
    op.create_index("ix_applicants_stage", "applicants", ["stage"])
    op.create_table(
        "applicant_stage_histories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("applicant_id", sa.String(length=36), nullable=False),
        sa.Column("from_stage", sa.String(length=20), nullable=True),
        sa.Column("to_stage", sa.String(length=20), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["applicant_id"], ["applicants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_applicant_stage_histories_applicant_id",
        "applicant_stage_histories",
        ["applicant_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_applicant_stage_histories_applicant_id",
        table_name="applicant_stage_histories",
    )
    op.drop_table("applicant_stage_histories")
    op.drop_index("ix_applicants_stage", table_name="applicants")
    op.drop_index("ix_applicants_job_posting_id", table_name="applicants")
    op.drop_table("applicants")
