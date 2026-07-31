"""create organization and approval tables

Revision ID: 20260730_0001
Revises:
Create Date: 2026-07-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260730_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    departments = op.create_table(
        "departments",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    employees = op.create_table(
        "employees",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("employee_no", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("department_id", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("employee_no"),
    )
    op.create_table(
        "approval_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("department_id", sa.String(length=50), nullable=False),
        sa.Column("author_id", sa.String(length=50), nullable=False),
        sa.Column("approver_id", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="DRAFT", nullable=False),
        sa.Column("decision_comment", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT','PENDING','APPROVED','REJECTED','CANCELLED')",
            name="ck_approval_documents_status",
        ),
        sa.ForeignKeyConstraint(["approver_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["author_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approval_documents_approver_id", "approval_documents", ["approver_id"])
    op.create_index("ix_approval_documents_author_id", "approval_documents", ["author_id"])
    op.create_index("ix_approval_documents_status", "approval_documents", ["status"])
    op.create_table(
        "approval_histories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("approval_document_id", sa.String(length=36), nullable=False),
        sa.Column("actor_id", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("from_status", sa.String(length=20), nullable=True),
        sa.Column("to_status", sa.String(length=20), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["approval_document_id"], ["approval_documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_approval_histories_approval_document_id",
        "approval_histories",
        ["approval_document_id"],
    )

    op.bulk_insert(
        departments,
        [
            {"id": "dept-hr", "code": "HR", "name": "인사팀"},
            {"id": "dept-sales", "code": "SALES", "name": "영업팀"},
            {"id": "dept-product", "code": "PRODUCT", "name": "서비스기획팀"},
        ],
    )
    op.bulk_insert(
        employees,
        [
            {
                "id": "emp-head",
                "employee_no": "MS-1001",
                "name": "김민서",
                "email": "minseo.kim@example.invalid",
                "role": "DEPARTMENT_HEAD",
                "department_id": "dept-product",
                "is_active": True,
            },
            {
                "id": "emp-hr",
                "employee_no": "MS-2001",
                "name": "박지우",
                "email": "jiwoo.park@example.invalid",
                "role": "HR_MANAGER",
                "department_id": "dept-hr",
                "is_active": True,
            },
            {
                "id": "emp-sales",
                "employee_no": "MS-3001",
                "name": "이도윤",
                "email": "doyoon.lee@example.invalid",
                "role": "SALES_REP",
                "department_id": "dept-sales",
                "is_active": True,
            },
            {
                "id": "emp-sales-head",
                "employee_no": "MS-3002",
                "name": "최서윤",
                "email": "seoyoon.choi@example.invalid",
                "role": "SALES_MANAGER",
                "department_id": "dept-sales",
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_approval_histories_approval_document_id", table_name="approval_histories")
    op.drop_table("approval_histories")
    op.drop_index("ix_approval_documents_status", table_name="approval_documents")
    op.drop_index("ix_approval_documents_author_id", table_name="approval_documents")
    op.drop_index("ix_approval_documents_approver_id", table_name="approval_documents")
    op.drop_table("approval_documents")
    op.drop_table("employees")
    op.drop_table("departments")
