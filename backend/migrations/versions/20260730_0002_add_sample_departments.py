"""add sample departments for approval form

Revision ID: 20260730_0002
Revises: 20260730_0001
Create Date: 2026-07-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260730_0002"
down_revision: str | None = "20260730_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SAMPLE_DEPARTMENTS = [
    {"id": "dept-development", "code": "DEV", "name": "개발팀"},
    {"id": "dept-finance", "code": "FINANCE", "name": "재무팀"},
]


def upgrade() -> None:
    departments = sa.table(
        "departments",
        sa.column("id", sa.String),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
    )
    op.bulk_insert(departments, _SAMPLE_DEPARTMENTS)


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM departments WHERE id IN (:development_id, :finance_id)").bindparams(
            development_id="dept-development",
            finance_id="dept-finance",
        )
    )
