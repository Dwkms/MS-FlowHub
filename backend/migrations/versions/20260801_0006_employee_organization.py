"""extend organization data for employee management

Revision ID: 20260801_0006
Revises: 20260731_0005
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260801_0006"
down_revision: str | None = "20260731_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("departments") as batch_op:
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("display_order", sa.Integer(), server_default="0", nullable=False)
        )
        batch_op.create_unique_constraint("uq_departments_name", ["name"])
    op.create_table(
        "teams",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("department_id", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("name"),
    )
    with op.batch_alter_table("employees") as batch_op:
        for column in (
            sa.Column("team_id", sa.String(length=50), nullable=True),
            sa.Column("position", sa.String(length=50), server_default="사원", nullable=False),
            sa.Column("job_title", sa.String(length=200), server_default="", nullable=False),
            sa.Column("job_description", sa.Text(), nullable=True),
            sa.Column("manager_id", sa.String(length=50), nullable=True),
            sa.Column(
                "employment_type", sa.String(length=30), server_default="REGULAR", nullable=False
            ),
            sa.Column(
                "employment_status", sa.String(length=30), server_default="ACTIVE", nullable=False
            ),
            sa.Column("hire_date", sa.Date(), nullable=True),
            sa.Column("phone_extension", sa.String(length=20), nullable=True),
            sa.Column(
                "work_location", sa.String(length=100), server_default="서울 본사", nullable=False
            ),
            sa.Column("profile_image_url", sa.String(length=500), nullable=True),
        ):
            batch_op.add_column(column)
        batch_op.create_foreign_key(
            "fk_employees_team_id", "teams", ["team_id"], ["id"], ondelete="RESTRICT"
        )
        batch_op.create_foreign_key(
            "fk_employees_manager_id", "employees", ["manager_id"], ["id"], ondelete="RESTRICT"
        )
        batch_op.create_index("ix_employees_department_id", ["department_id"])
        batch_op.create_index("ix_employees_team_id", ["team_id"])
        batch_op.create_index("ix_employees_manager_id", ["manager_id"])


def downgrade() -> None:
    with op.batch_alter_table("employees") as batch_op:
        batch_op.drop_index("ix_employees_manager_id")
        batch_op.drop_index("ix_employees_team_id")
        batch_op.drop_index("ix_employees_department_id")
        batch_op.drop_constraint("fk_employees_manager_id", type_="foreignkey")
        batch_op.drop_constraint("fk_employees_team_id", type_="foreignkey")
        for name in (
            "profile_image_url",
            "work_location",
            "phone_extension",
            "hire_date",
            "employment_status",
            "employment_type",
            "manager_id",
            "job_description",
            "job_title",
            "position",
            "team_id",
        ):
            batch_op.drop_column(name)
    op.drop_table("teams")
    with op.batch_alter_table("departments") as batch_op:
        batch_op.drop_constraint("uq_departments_name", type_="unique")
        batch_op.drop_column("display_order")
        batch_op.drop_column("description")
