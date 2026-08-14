"""역할 이름 상수와 가장 단순한 권한 검사.

역할 문자열을 코드 곳곳에 직접 쓰지 않고 여기 상수를 import해서 씁니다. `"TEAM_ADMIN"`을
직접 타이핑하면 오타가 나도 파이썬은 아무 말 없이 넘어가고, 그 분기는 영원히 거짓이 됩니다.
상수를 쓰면 이름이 틀렸을 때 import 단계에서 바로 터집니다.

**여기 있는 값은 `employee_accounts.role`입니다.** 이 프로젝트에는 역할 값이 두 벌 있고
(`employees.role`은 Seed가 채우는 별개 값), 실제 권한 판정은 항상 이쪽을 씁니다.
배경은 docs/DOMAIN.md 참고.

역할별 **관리 범위**(어느 직원까지 볼 수 있는가)는 여기가 아니라
`app/domain/org_scope.py`에 있습니다. 이 파일은 "역할이 무엇인가"만 다룹니다.
"""

from fastapi import HTTPException

from app.security.identity import ActorContext

SUPER_ADMIN = "SUPER_ADMIN"
HR_ADMIN = "HR_ADMIN"
TEAM_ADMIN = "TEAM_ADMIN"
PART_ADMIN = "PART_ADMIN"
EMPLOYEE = "EMPLOYEE"

PRIVATE_REASON_ROLES = frozenset({SUPER_ADMIN, HR_ADMIN})


def require_roles(actor: ActorContext, *roles: str) -> None:
    if actor.role not in roles:
        raise HTTPException(status_code=403, detail="권한이 없습니다.")
