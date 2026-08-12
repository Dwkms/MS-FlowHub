"""전자결재 AI 초안 API 테스트.

기본 Provider가 Mock이라 네트워크를 타지 않는다. 초안 생성이 결재 문서를 만들거나
상태를 바꾸지 않는다는 것을 함께 검증한다.
"""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.api.dependencies import get_authenticated_actor
from app.domain.ai_context import build_approval_context
from app.models.ai_generation import AiGeneration
from app.models.approval import ApprovalDocument
from app.security.identity import ActorContext

DRAFT_URL = "/api/v1/ai/approval-drafts"

PAYLOAD = {
    "document_type": "EXPENSE",
    "purpose": "개발용 노트북 교체",
    "main_content": "내구연한을 초과한 노트북 3대를 교체하려 합니다.",
    "amount": "6,000,000원",
}


def set_authenticated_actor(client: TestClient, employee_id: str, role: str = "EMPLOYEE") -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id=employee_id,
        role=role,
        auth_user_id=f"auth-{employee_id}",
    )


def _session(client: TestClient):
    return client.app.state.testing_session_factory()


def test_create_draft_returns_structured_output(client: TestClient) -> None:
    set_authenticated_actor(client, "emp-head")

    response = client.post(DRAFT_URL, json=PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["is_sample"] is True  # 기본 Provider는 Mock이다
    assert body["provider"] == "mock"
    assert set(body["output"]) == {"title", "purpose", "details", "expected_effect"}
    assert "6,000,000원" in body["output"]["details"]


def test_create_draft_requires_authentication(client: TestClient) -> None:
    client.app.dependency_overrides.pop(get_authenticated_actor, None)

    response = client.post(DRAFT_URL, json=PAYLOAD)

    assert response.status_code == 401


def test_draft_does_not_create_approval_document(client: TestClient) -> None:
    """초안 생성만으로 결재 문서가 생기거나 상태가 바뀌면 안 된다."""
    set_authenticated_actor(client, "emp-head")
    with _session(client) as session:
        before = session.scalar(select(func.count()).select_from(ApprovalDocument))

    assert client.post(DRAFT_URL, json=PAYLOAD).status_code == 200

    with _session(client) as session:
        assert session.scalar(select(func.count()).select_from(ApprovalDocument)) == before


def test_draft_is_recorded_with_creator(client: TestClient) -> None:
    set_authenticated_actor(client, "emp-head")

    generation_id = client.post(DRAFT_URL, json=PAYLOAD).json()["generation_id"]

    with _session(client) as session:
        record = session.get(AiGeneration, generation_id)
        assert record.created_by_id == "emp-head"
        assert record.feature_type == "APPROVAL_DRAFT"
        assert record.final_output is None
        # 개인정보는 Context에 담기지 않는다.
        assert "email" not in record.source_input
        assert "employee_no" not in record.source_input


def test_expected_effect_may_be_empty(client: TestClient) -> None:
    """근거가 없으면 기대 효과를 비울 수 있어야 한다.

    프롬프트는 "쓸 근거가 없으면 빈 문자열로 둔다"고 지시한다. 스키마가 이 필드를
    필수로 막으면, AI가 규칙을 지킨 응답이 검증에서 떨어진다(실제로 발생했다).
    """
    from app.schemas.ai import ApprovalDraftOutput

    draft = ApprovalDraftOutput(title="제목", purpose="목적", details="내용", expected_effect="")

    assert draft.expected_effect == ""


def test_too_short_input_is_rejected_before_calling_ai(client: TestClient) -> None:
    """짧은 입력은 AI가 쓸 근거가 없어 실패한다. 호출 비용이 나가기 전에 막는다."""
    set_authenticated_actor(client, "emp-head")

    response = client.post(
        DRAFT_URL, json={"document_type": "GENERAL", "purpose": "ㅇㅇ", "main_content": "ㅇㅇ"}
    )

    assert response.status_code == 422


def test_missing_required_field_is_rejected(client: TestClient) -> None:
    set_authenticated_actor(client, "emp-head")

    response = client.post(DRAFT_URL, json={"document_type": "EXPENSE", "purpose": "요청 목적만"})

    assert response.status_code == 422


def test_final_output_is_recorded_without_overwriting_generated(client: TestClient) -> None:
    set_authenticated_actor(client, "emp-head")
    created = client.post(DRAFT_URL, json=PAYLOAD).json()
    edited = dict(created["output"], title="사용자가 고친 제목")

    response = client.patch(
        f"/api/v1/ai/generations/{created['generation_id']}/final",
        json={"final_output": edited},
    )

    assert response.status_code == 204
    with _session(client) as session:
        record = session.get(AiGeneration, created["generation_id"])
        assert record.final_output["title"] == "사용자가 고친 제목"
        assert record.generated_output["title"] != "사용자가 고친 제목"


def test_final_output_rejects_other_users_generation(client: TestClient) -> None:
    set_authenticated_actor(client, "emp-head")
    created = client.post(DRAFT_URL, json=PAYLOAD).json()

    set_authenticated_actor(client, "emp-hr")
    response = client.patch(
        f"/api/v1/ai/generations/{created['generation_id']}/final",
        json={"final_output": created["output"]},
    )

    assert response.status_code == 403


def test_final_output_rejects_schema_violation(client: TestClient) -> None:
    set_authenticated_actor(client, "emp-head")
    created = client.post(DRAFT_URL, json=PAYLOAD).json()

    response = client.patch(
        f"/api/v1/ai/generations/{created['generation_id']}/final",
        json={"final_output": {"title": "제목만 있음"}},
    )

    assert response.status_code == 422


def test_context_omits_absent_amount_entirely() -> None:
    """금액을 입력하지 않으면 Context에 키 자체가 없다.

    `None`을 넣어두면 AI가 '금액: 미정' 같은 문장을 쓸 여지가 생긴다. 주지 않은 사실은
    존재조차 알리지 않는 것이 §9의 구조적 차단이다.
    """
    context = build_approval_context(
        author_name="김민성",
        position="대표이사",
        department_name="개발팀",
        drafted_on=date(2026, 8, 12),
        document_type="GENERAL",
        purpose="교육 참가",
        main_content="외부 세미나 참가",
    )

    assert "amount" not in context
    assert "quantity" not in context
    assert "desired_date" not in context
    assert context["document_type_label"] == "일반 품의"
