from fastapi import HTTPException

from app.security.identity import ActorContext

SUPER_ADMIN = "SUPER_ADMIN"
HR_ADMIN = "HR_ADMIN"
TEAM_ADMIN = "TEAM_ADMIN"
EMPLOYEE = "EMPLOYEE"

PRIVATE_REASON_ROLES = frozenset({SUPER_ADMIN, HR_ADMIN})


def require_roles(actor: ActorContext, *roles: str) -> None:
    if actor.role not in roles:
        raise HTTPException(status_code=403, detail="권한이 없습니다.")
