"""AIGenerationService 테스트. 네트워크를 타지 않고, 업무 테이블 불변을 함께 검증한다."""

import json
from collections.abc import Generator

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.ai_provider import APPROVAL_DRAFT, AIProviderResult
from app.models.ai_generation import AiGeneration
from app.models.approval import ApprovalDocument
from app.models.auth import EmployeeAccount
from app.repositories.ai_generation_repository import AiGenerationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.recruitment_repository import RecruitmentRepository
from app.schemas.ai import ApprovalDraftOutput
from app.security.identity import ActorContext
from app.services.ai_generation_service import AIGenerationService

ACTOR = ActorContext(employee_id="emp-head", role="EMPLOYEE", auth_user_id="auth-emp-head")
SUPER_ADMIN = ActorContext(employee_id="emp-head", role="SUPER_ADMIN", auth_user_id="auth-emp-head")
OTHER_ACTOR = ActorContext(employee_id="emp-sales", role="EMPLOYEE", auth_user_id="auth-emp-sales")
CONTEXT = {"department_name": "개발팀", "purpose": "노트북 교체", "main_content": "3대 교체 필요"}

VALID_PAYLOAD = json.dumps(
    {
        "title": "개발팀 노트북 교체",
        "purpose": "노후 장비 교체를 요청합니다.",
        "details": "개발용 노트북 3대 교체가 필요합니다.",
        "expected_effect": "승인 후 계획대로 진행할 수 있습니다.",
    },
    ensure_ascii=False,
)


class StubProvider:
    """호출 횟수를 세는 Provider. 한도가 Provider 호출 '전에' 막는지 확인하는 데 쓴다."""

    def __init__(self, result: AIProviderResult) -> None:
        self.result = result
        self.calls = 0

    def generate(self, feature_type, context, output_schema) -> AIProviderResult:
        self.calls += 1
        return self.result


def _success_provider() -> StubProvider:
    return StubProvider(
        AIProviderResult(
            provider="stub",
            success=True,
            content=VALID_PAYLOAD,
            model_name="stub-model",
            input_tokens=1500,
            output_tokens=2000,
        )
    )


@pytest.fixture
def session(client: TestClient) -> Generator[Session, None, None]:
    with client.app.state.testing_session_factory() as db_session:
        yield db_session


def _service(
    session: Session, provider: StubProvider, *, per_user: int = 5, global_limit: int = 30
) -> AIGenerationService:
    return AIGenerationService(
        session=session,
        repository=AiGenerationRepository(session),
        organization_repository=OrganizationRepository(session),
        recruitment_repository=RecruitmentRepository(session),
        provider=provider,
        settings=Settings(ai_daily_limit_per_user=per_user, ai_daily_limit_global=global_limit),
    )


def _generate(service: AIGenerationService, actor: ActorContext = ACTOR):
    return service.generate(
        feature_type=APPROVAL_DRAFT,
        context=CONTEXT,
        output_schema=ApprovalDraftOutput,
        actor=actor,
    )


def test_success_is_recorded_with_token_counts(session: Session):
    provider = _success_provider()

    outcome = _generate(_service(session, provider))

    assert outcome.success is True
    assert outcome.output.title == "개발팀 노트북 교체"

    record = session.get(AiGeneration, outcome.generation_id)
    assert record.success is True
    assert record.feature_type == APPROVAL_DRAFT
    assert record.generated_output["title"] == "개발팀 노트북 교체"
    assert record.final_output is None
    assert record.input_tokens == 1500
    assert record.output_tokens == 2000
    assert record.source_input == CONTEXT


def test_provider_failure_is_recorded_without_raising(session: Session):
    provider = StubProvider(
        AIProviderResult(provider="stub", success=False, error_message="AI 연결 실패")
    )

    outcome = _generate(_service(session, provider))

    assert outcome.success is False
    assert outcome.output is None
    assert outcome.error_message == "AI 연결 실패"

    record = session.get(AiGeneration, outcome.generation_id)
    assert record.success is False
    assert record.generated_output is None


def test_schema_violation_is_not_treated_as_success(session: Session):
    """스키마를 통과하지 못한 응답은 성공이 아니다. 원시 응답도 저장하지 않는다."""
    provider = StubProvider(
        AIProviderResult(
            provider="stub", success=True, content=json.dumps({"title": "제목만 있음"})
        )
    )

    outcome = _generate(_service(session, provider))

    assert outcome.success is False
    record = session.get(AiGeneration, outcome.generation_id)
    assert record.success is False
    assert record.generated_output is None
    assert "형식" in record.error_message


def test_too_long_title_fails_schema(session: Session):
    """`title`은 ApprovalDocument.title이 String(200)이라 여기서 막지 않으면 저장 때 터진다."""
    payload = json.loads(VALID_PAYLOAD)
    payload["title"] = "가" * 201
    provider = StubProvider(
        AIProviderResult(
            provider="stub", success=True, content=json.dumps(payload, ensure_ascii=False)
        )
    )

    outcome = _generate(_service(session, provider))

    assert outcome.success is False


def test_per_user_daily_limit_returns_429(session: Session):
    provider = _success_provider()
    service = _service(session, provider, per_user=2)

    _generate(service)
    _generate(service)
    with pytest.raises(HTTPException) as error:
        _generate(service)

    assert error.value.status_code == 429
    assert provider.calls == 2  # 한도 초과 요청은 Provider를 부르지 않는다


def test_global_daily_limit_returns_429(session: Session):
    provider = _success_provider()
    service = _service(session, provider, per_user=99, global_limit=1)

    _generate(service)
    with pytest.raises(HTTPException) as error:
        _generate(service)

    assert error.value.status_code == 429
    assert provider.calls == 1


def test_limit_rejection_is_not_recorded(session: Session):
    service = _service(session, _success_provider(), global_limit=1)

    _generate(service)
    with pytest.raises(HTTPException):
        _generate(service)

    assert session.scalar(select(func.count()).select_from(AiGeneration)) == 1


def test_super_admin_is_exempt_from_per_user_limit(session: Session):
    """검수·시연이 사용자당 한도에 막히지 않게 한다. 전역 한도는 그대로 적용된다."""
    provider = _success_provider()
    service = _service(session, provider, per_user=1)

    _generate(service, SUPER_ADMIN)
    _generate(service, SUPER_ADMIN)
    _generate(service, SUPER_ADMIN)

    assert provider.calls == 3


def test_super_admin_is_exempt_from_global_limit(session: Session):
    """최고 관리자는 검수용 반복 생성 중 전역 한도에도 막히지 않는다."""
    provider = _success_provider()
    service = _service(session, provider, per_user=99, global_limit=2)

    _generate(service, SUPER_ADMIN)
    _generate(service, SUPER_ADMIN)
    _generate(service, SUPER_ADMIN)

    assert provider.calls == 3


def test_super_admin_calls_do_not_consume_normal_global_limit(session: Session):
    """관리자 검수 호출 때문에 일반 직원의 전역 생성 가능 횟수가 줄면 안 된다."""
    session.add(
        EmployeeAccount(
            id="account-limit-super-admin",
            auth_user_id="auth-limit-super-admin",
            employee_id=SUPER_ADMIN.employee_id,
            role="SUPER_ADMIN",
        )
    )
    session.commit()
    provider = _success_provider()
    service = _service(session, provider, per_user=99, global_limit=2)

    for _ in range(3):
        _generate(service, SUPER_ADMIN)
    _generate(service, OTHER_ACTOR)
    _generate(service, OTHER_ACTOR)
    with pytest.raises(HTTPException):
        _generate(service, OTHER_ACTOR)

    assert provider.calls == 5


def test_limit_message_states_actual_limit(session: Session):
    """'잠시 후 다시 시도'만 쓰면 최대 24시간을 기다려야 하는 상황에서 사용자를 오도한다."""
    service = _service(session, _success_provider(), per_user=1)

    _generate(service)
    with pytest.raises(HTTPException) as error:
        _generate(service)

    assert "1회" in error.value.detail
    assert "24시간" in error.value.detail


def test_generation_does_not_touch_approval_documents(session: Session):
    """AI 호출은 업무 테이블을 건드리지 않는다. 이 서비스가 쓰는 테이블은 하나뿐이다."""
    before = session.scalar(select(func.count()).select_from(ApprovalDocument))

    _generate(_service(session, _success_provider()))

    assert session.scalar(select(func.count()).select_from(ApprovalDocument)) == before
