"""split department teams and reassign employee numbers

Revision ID: 20260808_0018
Revises: 20260808_0017
"""

import sqlalchemy as sa
from alembic import op

revision = "20260808_0018"
down_revision = "20260808_0017"
branch_labels = None
depends_on = None


_TEAM_ROWS = (
    ("team-mkt_1", "MKT_1", "마케팅1팀", "MKT", 1),
    ("team-mkt_2", "MKT_2", "마케팅2팀", "MKT", 2),
    ("team-hr_1", "HR_1", "인사1팀", "HR", 1),
    ("team-hr_2", "HR_2", "인사2팀", "HR", 2),
    ("team-plan_1", "PLAN_1", "기획1팀", "PLAN", 1),
    ("team-plan_2", "PLAN_2", "기획2팀", "PLAN", 2),
    ("team-cs_1", "CS_1", "CS1팀", "CS", 1),
)


def _insert_teams() -> None:
    for team_id, code, name, department_code, display_order in _TEAM_ROWS:
        op.execute(
            sa.text(
                """
                INSERT INTO teams (id, code, name, department_id, display_order)
                SELECT :team_id, :code, :name, id, :display_order
                FROM departments
                WHERE code = :department_code
                  AND NOT EXISTS (SELECT 1 FROM teams WHERE code = :code)
                """
            ).bindparams(
                team_id=team_id,
                code=code,
                name=name,
                department_code=department_code,
                display_order=display_order,
            )
        )


def _set_team(employee_nos: range, team_code: str) -> None:
    for employee_no in employee_nos:
        op.execute(
            sa.text(
                """
                UPDATE employees
                SET team_id = (SELECT id FROM teams WHERE code = :team_code)
                WHERE employee_no = :employee_no
                """
            ).bindparams(team_code=team_code, employee_no=f"MS{employee_no:04d}")
        )


def _reassign_employee_numbers(*, forward: bool) -> None:
    op.execute(
        sa.text(
            """
            UPDATE employees
            SET employee_no = 'TMP-' || employee_no
            WHERE employee_no BETWEEN 'MS0012' AND 'MS0049'
            """
        )
    )
    mappings: list[tuple[int, int]] = []
    if forward:
        mappings.extend((number, number + 3) for number in range(12, 47))
        mappings.extend(((47, 12), (48, 13), (49, 14)))
    else:
        mappings.extend((number + 3, number) for number in range(12, 47))
        mappings.extend(((12, 47), (13, 48), (14, 49)))
    for before, after in mappings:
        op.execute(
            sa.text(
                "UPDATE employees SET employee_no = :after WHERE employee_no = :before"
            ).bindparams(before=f"TMP-MS{before:04d}", after=f"MS{after:04d}")
        )


def upgrade() -> None:
    _insert_teams()
    _set_team(range(12, 17), "MKT_1")
    _set_team(range(17, 22), "MKT_2")
    _set_team(range(22, 27), "HR_1")
    _set_team(range(27, 32), "HR_2")
    _set_team(range(32, 37), "PLAN_1")
    _set_team(range(37, 42), "PLAN_2")
    _set_team(range(42, 47), "CS_1")
    _reassign_employee_numbers(forward=True)


def downgrade() -> None:
    _reassign_employee_numbers(forward=False)
    op.execute(
        sa.text(
            """
            UPDATE employees
            SET team_id = NULL
            WHERE team_id IN (
                SELECT id FROM teams
                WHERE code IN ('MKT_1', 'MKT_2', 'HR_1', 'HR_2', 'PLAN_1', 'PLAN_2', 'CS_1')
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            DELETE FROM teams
            WHERE code IN ('MKT_1', 'MKT_2', 'HR_1', 'HR_2', 'PLAN_1', 'PLAN_2', 'CS_1')
            """
        )
    )
