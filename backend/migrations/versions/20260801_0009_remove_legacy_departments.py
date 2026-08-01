"""remove legacy empty departments

Revision ID: 20260801_0009
Revises: 20260801_0008
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260801_0009"
down_revision: str | None = "20260801_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM departments d "
            "WHERE d.code IN ('FINANCE', 'PRODUCT', 'SALES') "
            "AND NOT EXISTS (SELECT 1 FROM employees e WHERE e.department_id = d.id) "
            "AND NOT EXISTS (SELECT 1 FROM teams t WHERE t.department_id = d.id)"
        )
    )


def downgrade() -> None:
    departments = sa.table(
        "departments",
        sa.column("id", sa.String),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
    )
    op.bulk_insert(
        departments,
        [
            {"id": "dept-finance", "code": "FINANCE", "name": "재무팀"},
            {"id": "dept-product", "code": "PRODUCT", "name": "제품팀"},
            {"id": "dept-sales", "code": "SALES", "name": "영업팀"},
        ],
    )
