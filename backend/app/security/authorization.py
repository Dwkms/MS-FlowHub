from fastapi import HTTPException

from app.domain.employee_status import PRIVATE_REASON_VIEWER_ROLES
from app.security.identity import ActorContext


def require_self_or_admin(actor: ActorContext, target_employee_id: str) -> None:
    if actor.employee_id != target_employee_id and actor.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="본인 또는 관리자만 상태 사유를 변경할 수 있습니다.",
        )


def can_view_private_status_reasons(actor: ActorContext | None) -> bool:
    return bool(actor and actor.role in PRIVATE_REASON_VIEWER_ROLES)
