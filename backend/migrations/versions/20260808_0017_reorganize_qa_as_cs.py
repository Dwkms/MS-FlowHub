"""reorganize QA department as customer support and add development QA part

Revision ID: 20260808_0017
Revises: 20260807_0016
Create Date: 2026-08-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260808_0017"
down_revision: str | None = "20260807_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("UPDATE departments SET code = 'CS', name = 'CS팀' WHERE code = 'QA'"))

    op.execute(
        sa.text(
            "INSERT INTO teams (id, code, name, department_id, display_order) "
            "SELECT 'team-dev_qa', 'DEV_QA', 'QA파트', id, 3 "
            "FROM departments WHERE code = 'DEV'"
        )
    )

    op.execute(
        sa.text(
            "UPDATE employees SET position = '팀장', "
            "job_title = '고객지원 운영 및 VOC 관리 총괄', "
            "job_description = '고객지원 운영 및 VOC 관리 총괄' "
            "WHERE employee_no = 'MS0042'"
        )
    )
    for employee_no, job_title in (
        ("MS0043", "고객 문의 분석 및 지원 프로세스 개선"),
        ("MS0044", "제품 사용 문의 및 장애 접수 대응"),
        ("MS0045", "고객 안내 콘텐츠 및 반복 문의 관리"),
        ("MS0046", "고객 요청 접수 및 처리 현황 관리"),
    ):
        op.execute(
            sa.text(
                "UPDATE employees SET job_title = :job_title, job_description = :job_title "
                "WHERE employee_no = :employee_no"
            ).bindparams(employee_no=employee_no, job_title=job_title)
        )

    for employee_no, name, position, job_title, manager_no, phone_extension in (
        ("MS0047", "최다은", "파트장", "QA 전략 및 테스트 품질 관리", "MS0002", "1047"),
        ("MS0048", "정하윤", "선임", "기능·회귀 테스트와 결함 분석", "MS0047", "1048"),
        ("MS0049", "유민재", "사원", "테스트 자동화와 배포 전 검증", "MS0047", "1049"),
    ):
        op.execute(
            sa.text(
                "INSERT INTO employees (id, employee_no, name, email, role, department_id, "
                "team_id, position, job_title, job_description, manager_id, employment_type, "
                "employment_status, is_active, work_location, phone_extension) "
                "SELECT :employee_id, :employee_no, :name, :email, 'EMPLOYEE', department.id, "
                "team.id, :position, :job_title, :job_title, manager.id, 'REGULAR', 'ACTIVE', "
                "TRUE, '서울 본사', :phone_extension "
                "FROM departments AS department "
                "JOIN teams AS team ON team.code = 'DEV_QA' "
                "JOIN employees AS manager ON manager.employee_no = :manager_no "
                "WHERE department.code = 'DEV'"
            ).bindparams(
                employee_id=f"emp-ms{employee_no[-4:]}",
                employee_no=employee_no,
                name=name,
                email=f"ms{employee_no[-4:]}@msflowhub.test",
                position=position,
                job_title=job_title,
                manager_no=manager_no,
                phone_extension=phone_extension,
            )
        )


def downgrade() -> None:
    op.execute(sa.text("UPDATE employees SET team_id = NULL WHERE team_id = 'team-dev_qa'"))
    op.execute(sa.text("DELETE FROM teams WHERE id = 'team-dev_qa'"))
    op.execute(sa.text("UPDATE departments SET code = 'QA', name = 'QA팀' WHERE code = 'CS'"))
