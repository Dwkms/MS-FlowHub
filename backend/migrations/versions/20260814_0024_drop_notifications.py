"""알림 기능 제거에 따른 notifications 테이블 삭제

인앱 알림은 조회·읽음 처리 API가 없는 상태로 데이터만 쌓이고 있었고, 화면의 종
아이콘도 비활성으로만 남아 있었다. 사내 메일 시스템 도입 전까지 쓰지 않기로 해서
코드와 스키마에서 함께 걷어낸다.

downgrade는 테이블 구조만 되살린다. 삭제된 행은 복구되지 않는다.

Revision ID: 20260814_0024
Revises: 20260813_0023
Create Date: 2026-08-14
"""

import sqlalchemy as sa
from alembic import op

revision = "20260814_0024"
down_revision = "20260813_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_notifications_recipient_id", table_name="notifications")
    op.drop_table("notifications")


def downgrade() -> None:
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
