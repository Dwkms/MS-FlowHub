"""add recruitment request fields used by job postings

채용공고에 필요한 값(근무지·급여·마감일·지원방법·학력)을 채용 요청 단계에서 받는다.
지금까지는 AI 초안 패널에서 매번 다시 입력했고 결재자도 볼 수 없었다.
경력은 자유 입력이라 "Junior" 같은 값이 공고에 그대로 박혀, 최소 년수를 따로 받는다.

기존 행을 건드리지 않도록 **전부 nullable**로 넣는다. `experience_level`은 칼럼을
그대로 두고 신규 입력만 코드값(NEW/EXPERIENCED/ANY)으로 좁힌다.

Revision ID: 20260813_0023
Revises: 20260812_0022
Create Date: 2026-08-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260813_0023"
down_revision: str | None = "20260812_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "recruitment_requests",
        sa.Column("experience_years_min", sa.Integer(), nullable=True),
    )
    op.add_column(
        "recruitment_requests",
        sa.Column("education_level", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "recruitment_requests",
        sa.Column("work_location", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "recruitment_requests",
        sa.Column("salary", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "recruitment_requests",
        sa.Column("application_deadline", sa.Date(), nullable=True),
    )
    op.add_column(
        "recruitment_requests",
        sa.Column("apply_method", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("recruitment_requests", "apply_method")
    op.drop_column("recruitment_requests", "application_deadline")
    op.drop_column("recruitment_requests", "salary")
    op.drop_column("recruitment_requests", "work_location")
    op.drop_column("recruitment_requests", "education_level")
    op.drop_column("recruitment_requests", "experience_years_min")
