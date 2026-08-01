from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import check_database_connection, get_db_session
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.recruitment_repository import RecruitmentRepository
from app.security.identity import ActorContext
from app.security.supabase_auth import get_supabase_auth_user_id
from app.services.approval_service import ApprovalService
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService
from app.services.employee_service import EmployeeService
from app.services.recruitment_service import RecruitmentService

DatabaseSession = Annotated[Session, Depends(get_db_session)]


def get_database_health() -> bool:
    return check_database_connection()


def get_current_auth_user(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    return get_supabase_auth_user_id(authorization.removeprefix("Bearer ").strip())


def get_authenticated_actor(
    auth_user_id: Annotated[str, Depends(get_current_auth_user)],
    session: DatabaseSession,
) -> ActorContext:
    row = AuthRepository(session).get_account_with_employee(auth_user_id)
    if row is None:
        raise HTTPException(status_code=403, detail="직원 계정 연결이 필요합니다.")
    account, employee = row
    if not account.is_active or not employee.is_active:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다.")
    return ActorContext(employee_id=employee.id, role=account.role, auth_user_id=auth_user_id)


AuthenticatedActor = Annotated[ActorContext, Depends(get_authenticated_actor)]


def get_optional_actor(
    session: DatabaseSession, actor_id: str | None = Query(default=None)
) -> ActorContext | None:
    if actor_id is None:
        return None
    employee = OrganizationRepository(session).get_employee_model(actor_id)
    if employee is None:
        raise HTTPException(status_code=401, detail="유효하지 않은 사용자입니다.")
    return ActorContext(employee_id=employee.id, role=employee.role)


def get_current_actor(
    actor: Annotated[ActorContext | None, Depends(get_optional_actor)],
) -> ActorContext:
    if actor is None:
        raise HTTPException(status_code=401, detail="사용자 정보가 필요합니다.")
    return actor


OptionalActor = Annotated[ActorContext | None, Depends(get_optional_actor)]
CurrentActor = Annotated[ActorContext, Depends(get_current_actor)]


def get_dashboard_service(session: DatabaseSession) -> DashboardService:
    return DashboardService(
        organization_repository=OrganizationRepository(session),
        approval_repository=ApprovalRepository(session),
        settings=get_settings(),
    )


def get_auth_service(session: DatabaseSession) -> AuthService:
    return AuthService(session=session, repository=AuthRepository(session))


def get_employee_service(session: DatabaseSession) -> EmployeeService:
    return EmployeeService(session=session, repository=OrganizationRepository(session))


def get_approval_service(session: DatabaseSession) -> ApprovalService:
    recruitment_service = _build_recruitment_service(session)
    return ApprovalService(
        session=session,
        approval_repository=ApprovalRepository(session),
        organization_repository=OrganizationRepository(session),
        recruitment_service=recruitment_service,
    )


def get_recruitment_service(session: DatabaseSession) -> RecruitmentService:
    return _build_recruitment_service(session)


def _build_recruitment_service(session: Session) -> RecruitmentService:
    return RecruitmentService(
        session=session,
        recruitment_repository=RecruitmentRepository(session),
        approval_repository=ApprovalRepository(session),
        organization_repository=OrganizationRepository(session),
        notification_repository=NotificationRepository(session),
    )
