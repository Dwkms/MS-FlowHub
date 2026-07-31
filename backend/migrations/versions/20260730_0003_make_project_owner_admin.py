"""make project owner an admin sample user

Revision ID: 20260730_0003
Revises: 20260730_0002
Create Date: 2026-07-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260730_0003"
down_revision: str | None = "20260730_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE employees
            SET name = :name, email = :email, role = :role
            WHERE id = :employee_id
            """
        ).bindparams(
            employee_id="emp-head",
            name="김민성",
            email="minseong.kim@example.invalid",
            role="ADMIN",
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE employees
            SET name = :name, email = :email, role = :role
            WHERE id = :employee_id
            """
        ).bindparams(
            employee_id="emp-head",
            name="김민서",
            email="minseo.kim@example.invalid",
            role="DEPARTMENT_HEAD",
        )
    )
