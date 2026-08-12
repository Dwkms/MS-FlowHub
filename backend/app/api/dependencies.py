from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import check_database_connection, get_db_session
from app.domain.ai_provider import CLAUDE, MOCK, AIProvider, MockAIProvider
from app.domain.ax_search import KeywordSearcher
from app.models.organization import Employee
from app.repositories.ai_generation_repository import AiGenerationRepository
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.ax_repository import AxRepository
from app.repositories.manual_repository import ManualRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.recruitment_repository import RecruitmentRepository
from app.security.identity import ActorContext
from app.security.permissions import (
    EMPLOYEE,
    HR_ADMIN,
    SUPER_ADMIN,
    TEAM_ADMIN,
    require_roles,
)
from app.security.supabase_auth import get_supabase_auth_user_id
from app.services.ai_generation_service import AIGenerationService
from app.services.approval_service import ApprovalService
from app.services.auth_service import AuthService
from app.services.ax_service import AxService
from app.services.dashboard_service import DashboardService
from app.services.employee_service import EmployeeService
from app.services.manual_service import ManualService
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


def require_authenticated_user(actor: AuthenticatedActor) -> ActorContext:
    return actor


def get_current_employee(actor: AuthenticatedActor, session: DatabaseSession) -> Employee:
    employee = session.get(Employee, actor.employee_id)
    if employee is None:
        raise HTTPException(status_code=403, detail="Authenticated employee was not found.")
    return employee


def require_super_admin(actor: AuthenticatedActor) -> ActorContext:
    require_roles(actor, SUPER_ADMIN)
    return actor


def require_hr_admin(actor: AuthenticatedActor) -> ActorContext:
    require_roles(actor, SUPER_ADMIN, HR_ADMIN)
    return actor


def require_team_admin(actor: AuthenticatedActor) -> ActorContext:
    require_roles(actor, SUPER_ADMIN, TEAM_ADMIN)
    return actor


def require_employee_management_permission(actor: AuthenticatedActor) -> ActorContext:
    require_roles(actor, SUPER_ADMIN, HR_ADMIN)
    return actor


def require_approval_permission(actor: AuthenticatedActor) -> ActorContext:
    require_roles(actor, SUPER_ADMIN, HR_ADMIN, TEAM_ADMIN, EMPLOYEE)
    return actor


def get_dashboard_service(session: DatabaseSession) -> DashboardService:
    return DashboardService(
        organization_repository=OrganizationRepository(session),
        approval_repository=ApprovalRepository(session),
        recruitment_repository=RecruitmentRepository(session),
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


def get_manual_service(session: DatabaseSession) -> ManualService:
    return ManualService(session=session, repository=ManualRepository(session))


def get_ax_service(session: DatabaseSession) -> AxService:
    # v1은 키워드 검색기 하나뿐이다. v2에서 임베딩 검색기로 바꿀 때 이 한 줄만 바뀐다.
    return AxService(session=session, repository=AxRepository(session), searcher=KeywordSearcher())


@lru_cache(maxsize=1)
def _create_ai_provider(
    provider_name: str,
    api_key: str | None,
    model: str | None,
    max_tokens: int,
    timeout: float,
) -> AIProvider:
    """Provider 생성 지점을 한 곳에 모은다. HTTP 커넥션 풀 재사용을 위해 캐시한다.

    API 키가 없을 때 실제 Provider를 조용히 Mock으로 대체하지 않는다. "AI를 붙인 줄
    알았는데 샘플 응답이었다"가 더 나쁜 실패다. 기본값 누락은 Mock, 명시적 오설정은 오류다.
    """
    if provider_name == MOCK:
        return MockAIProvider()
    if provider_name != CLAUDE:
        # 설정값을 메시지에 넣지 않는다. API 키를 AI_PROVIDER 칸에 잘못 붙여넣는 실수가
        # 실제로 일어나며, 그때 값을 echo하면 키가 로그와 오류 화면에 그대로 남는다.
        raise RuntimeError(
            f"지원하지 않는 AI_PROVIDER 설정입니다. '{MOCK}' 또는 '{CLAUDE}'만 사용할 수 있습니다."
        )
    if not api_key:
        raise RuntimeError("AI_PROVIDER가 지정되었으나 AI_API_KEY가 설정되지 않았습니다.")

    # anthropic SDK는 실제 Provider가 필요할 때만 import한다. Mock 경로는 SDK 없이 돈다.
    from app.domain.claude_provider import ClaudeProvider

    return ClaudeProvider(api_key=api_key, model=model, timeout=timeout, max_tokens=max_tokens)


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    return _create_ai_provider(
        (settings.ai_provider or MOCK).strip().lower(),
        settings.ai_api_key,
        settings.ai_model,
        settings.ai_max_tokens,
        settings.ai_timeout_seconds,
    )


def get_ai_generation_service(
    session: DatabaseSession,
    # Provider를 FastAPI 의존성으로 받는다. 테스트가 이 지점을 override해 Mock을 강제하고,
    # 그래야 개발자 로컬 `.env`에 실제 키가 있어도 테스트가 네트워크를 타지 않는다.
    provider: Annotated[AIProvider, Depends(get_ai_provider)],
) -> AIGenerationService:
    return AIGenerationService(
        session=session,
        repository=AiGenerationRepository(session),
        organization_repository=OrganizationRepository(session),
        recruitment_repository=RecruitmentRepository(session),
        provider=provider,
        settings=get_settings(),
    )


def _build_recruitment_service(session: Session) -> RecruitmentService:
    return RecruitmentService(
        session=session,
        recruitment_repository=RecruitmentRepository(session),
        approval_repository=ApprovalRepository(session),
        organization_repository=OrganizationRepository(session),
        notification_repository=NotificationRepository(session),
    )
