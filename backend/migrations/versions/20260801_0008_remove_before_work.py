"""remove before-work attendance status

Revision ID: 20260801_0008
Revises: 20260801_0007
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260801_0008"
down_revision: str | None = "20260801_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE attendance_records SET work_status = 'OFF_WORK' "
            "WHERE work_status = 'BEFORE_WORK'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE attendance_records SET work_status = 'BEFORE_WORK' "
            "WHERE work_status = 'OFF_WORK'"
        )
    )
