"""역할별 조직 관리 범위를 한 곳에서 정한다.

TEAM_ADMIN(팀장)은 부서 전체를, PART_ADMIN(파트장)은 자기 파트만 관리한다.
범위 기준을 역할에 고정해 두는 것이 핵심이다. 관리자의 `team_id`가 채워져
있는지에 따라 범위가 달라지면 같은 역할이 두 가지로 동작하게 된다.
"""

from typing import Protocol

from app.security.permissions import PART_ADMIN, TEAM_ADMIN

# 팀장은 부서(`departments`) 단위, 파트장은 파트(`teams`) 단위로 범위를 잡는다.
# DATA_MODEL 기준으로 `teams`는 부서 산하 파트(DEV_SW/DEV_HW/DEV_QA)를 뜻한다.
DEPARTMENT_SCOPED_ROLES = frozenset({TEAM_ADMIN})
TEAM_SCOPED_ROLES = frozenset({PART_ADMIN})
ORG_SCOPED_ROLES = DEPARTMENT_SCOPED_ROLES | TEAM_SCOPED_ROLES


class OrgMember(Protocol):
    """`Employee` 모델과 `EmployeeDetail` 스키마가 함께 만족하는 최소 형태."""

    department_id: str
    team_id: str | None


def is_org_scoped_role(role: str) -> bool:
    return role in ORG_SCOPED_ROLES


def is_within_scope(role: str, manager: OrgMember, target: OrgMember) -> bool:
    if role in DEPARTMENT_SCOPED_ROLES:
        # `department_id`는 NOT NULL이라 팀장은 항상 범위가 성립한다.
        return manager.department_id == target.department_id
    if role in TEAM_SCOPED_ROLES:
        # 파트가 지정되지 않은 파트장은 관리 대상이 없다. 부서 전체로 넓히지 않는다.
        return manager.team_id is not None and manager.team_id == target.team_id
    return False
