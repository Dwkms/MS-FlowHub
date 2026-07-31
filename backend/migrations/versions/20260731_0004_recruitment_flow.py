"""add recruitment request and job posting flow

Revision ID: 20260731_0004
Revises: 20260730_0003
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260731_0004"
down_revision: str | None = "20260730_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    # The local fallback database used Base.metadata.create_all() before Alembic
    # was introduced. Preserve its existing approval records while bringing it
    # under the same migration history as the Supabase schema.
    if bind.dialect.name == "sqlite" and inspector.has_table("recruitment_requests"):
        approval_columns = {
            column["name"] for column in inspector.get_columns("approval_documents")
        }
        if "related_type" not in approval_columns:
            op.add_column(
                "approval_documents", sa.Column("related_type", sa.String(length=50), nullable=True)
            )
        if "related_id" not in approval_columns:
            op.add_column(
                "approval_documents", sa.Column("related_id", sa.String(length=36), nullable=True)
            )
        approval_indexes = {item["name"] for item in inspector.get_indexes("approval_documents")}
        if "ix_approval_documents_related_type" not in approval_indexes:
            op.create_index(
                "ix_approval_documents_related_type", "approval_documents", ["related_type"]
            )
        if "ix_approval_documents_related_id" not in approval_indexes:
            op.create_index(
                "ix_approval_documents_related_id", "approval_documents", ["related_id"]
            )
        employee_exists = bind.execute(
            sa.text("SELECT 1 FROM employees WHERE id = 'emp-product-head'")
        ).scalar()
        if employee_exists is None:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO employees (
                        id, employee_no, name, email, role, department_id, is_active
                    )
                    VALUES ('emp-product-head', 'MS-4001', '한유진',
                    'yujin.han@example.invalid', 'DEPARTMENT_HEAD', 'dept-product', 1)
                    """
                )
            )
        return

    op.add_column(
        "approval_documents", sa.Column("related_type", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "approval_documents", sa.Column("related_id", sa.String(length=36), nullable=True)
    )
    op.create_index("ix_approval_documents_related_type", "approval_documents", ["related_type"])
    op.create_index("ix_approval_documents_related_id", "approval_documents", ["related_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("recipient_id", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("related_type", sa.String(length=50), nullable=True),
        sa.Column("related_id", sa.String(length=36), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["recipient_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_recipient_id", "notifications", ["recipient_id"])

    op.create_table(
        "recruitment_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("request_department_id", sa.String(length=50), nullable=False),
        sa.Column("requester_id", sa.String(length=50), nullable=False),
        sa.Column("approver_id", sa.String(length=50), nullable=False),
        sa.Column("position_title", sa.String(length=150), nullable=False),
        sa.Column("headcount", sa.Integer(), nullable=False),
        sa.Column("employment_type", sa.String(length=50), nullable=False),
        sa.Column("experience_level", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("responsibilities", sa.Text(), nullable=False),
        sa.Column("required_skills", sa.Text(), nullable=True),
        sa.Column("preferred_skills", sa.Text(), nullable=True),
        sa.Column("desired_start_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="DRAFT", nullable=False),
        sa.Column("approval_document_id", sa.String(length=36), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT','PENDING_APPROVAL','APPROVED','REJECTED','POSTING_CREATED')",
            name="ck_recruitment_requests_status",
        ),
        sa.ForeignKeyConstraint(
            ["approval_document_id"], ["approval_documents.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["approver_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["request_department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["requester_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("approval_document_id"),
    )
    op.create_index(
        "ix_recruitment_requests_request_department_id",
        "recruitment_requests",
        ["request_department_id"],
    )
    op.create_index(
        "ix_recruitment_requests_requester_id", "recruitment_requests", ["requester_id"]
    )
    op.create_index("ix_recruitment_requests_status", "recruitment_requests", ["status"])

    op.create_table(
        "job_postings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("recruitment_request_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="DRAFT", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["recruitment_request_id"], ["recruitment_requests.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recruitment_request_id"),
    )

    employees = sa.table(
        "employees",
        sa.column("id", sa.String),
        sa.column("employee_no", sa.String),
        sa.column("name", sa.String),
        sa.column("email", sa.String),
        sa.column("role", sa.String),
        sa.column("department_id", sa.String),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        employees,
        [
            {
                "id": "emp-product-head",
                "employee_no": "MS-4001",
                "name": "한유진",
                "email": "yujin.han@example.invalid",
                "role": "DEPARTMENT_HEAD",
                "department_id": "dept-product",
                "is_active": True,
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("job_postings")
    op.drop_index("ix_recruitment_requests_status", table_name="recruitment_requests")
    op.drop_index("ix_recruitment_requests_requester_id", table_name="recruitment_requests")
    op.drop_index(
        "ix_recruitment_requests_request_department_id", table_name="recruitment_requests"
    )
    op.drop_table("recruitment_requests")
    op.drop_index("ix_notifications_recipient_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_approval_documents_related_id", table_name="approval_documents")
    op.drop_index("ix_approval_documents_related_type", table_name="approval_documents")
    op.drop_column("approval_documents", "related_id")
    op.drop_column("approval_documents", "related_type")
    op.execute(sa.text("DELETE FROM employees WHERE id = 'emp-product-head'"))
