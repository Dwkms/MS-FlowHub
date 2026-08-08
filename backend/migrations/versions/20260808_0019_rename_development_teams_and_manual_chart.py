"""rename development teams and update the organization chart asset

Revision ID: 20260808_0019
Revises: 20260808_0018
"""

import sqlalchemy as sa
from alembic import op

revision = "20260808_0019"
down_revision = "20260808_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for code, name in (("DEV_SW", "SW개발팀"), ("DEV_HW", "HW개발팀"), ("DEV_QA", "QA팀")):
        op.execute(
            sa.text("UPDATE teams SET name = :name WHERE code = :code").bindparams(
                code=code, name=name
            )
        )
    op.execute(
        sa.text(
            """
            UPDATE manual_assets
            SET file_url = '/organization-chart-v2.svg'
            WHERE id = 'manual-asset-organization-chart'
            """
        )
    )


def downgrade() -> None:
    for code, name in (("DEV_SW", "SW개발파트"), ("DEV_HW", "HW개발파트"), ("DEV_QA", "QA파트")):
        op.execute(
            sa.text("UPDATE teams SET name = :name WHERE code = :code").bindparams(
                code=code, name=name
            )
        )
    op.execute(
        sa.text(
            """
            UPDATE manual_assets
            SET file_url = '/organization-chart.png'
            WHERE id = 'manual-asset-organization-chart'
            """
        )
    )
