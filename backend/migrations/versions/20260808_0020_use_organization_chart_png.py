"""use the replacement organization chart PNG

Revision ID: 20260808_0020
Revises: 20260808_0019
"""

import sqlalchemy as sa
from alembic import op

revision = "20260808_0020"
down_revision = "20260808_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE manual_assets
            SET file_url = '/organization-chart.png'
            WHERE id = 'manual-asset-organization-chart'
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE manual_assets
            SET file_url = '/organization-chart-v2.svg'
            WHERE id = 'manual-asset-organization-chart'
            """
        )
    )
