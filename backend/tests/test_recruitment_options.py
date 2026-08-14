"""채용 요청 선택지 제한과 경력 표기.

자유 입력이던 항목을 코드값으로 좁히면서, 이미 저장된 자유 입력 데이터가 깨지지 않는지를
함께 고정한다. 신규 입력만 막고 기존 값은 읽을 수 있어야 한다.
"""

import pytest
from fastapi.testclient import TestClient

from app.domain.recruitment_options import (
    EXPERIENCE_YEARS_MAX,
    describe_experience,
)
from tests.test_recruitment_api import create_draft, request_payload, set_authenticated_actor


class TestDescribeExperience:
    def test_new_and_any_use_labels(self) -> None:
        assert describe_experience("NEW", None) == "신입"
        assert describe_experience("ANY", None) == "경력무관"

    def test_experienced_shows_minimum_years(self) -> None:
        assert describe_experience("EXPERIENCED", 3) == "경력 3년 이상"

    def test_years_above_ceiling_collapse(self) -> None:
        """상한 위는 한 칸으로 묶는다. 화면 드롭다운의 마지막 칸과 표기를 맞춘다."""
        assert describe_experience("EXPERIENCED", 99) == f"경력 {EXPERIENCE_YEARS_MAX}년 이상"

    def test_experienced_without_years_falls_back(self) -> None:
        assert describe_experience("EXPERIENCED", None) == "경력"

    def test_legacy_free_text_survives(self) -> None:
        """자유 입력 시절의 값은 코드값이 아니다. 버리면 기존 공고 화면이 빈칸이 된다."""
        assert describe_experience("Junior", None) == "Junior"
        assert describe_experience("신입/경력", None) == "신입/경력"


class TestCreateValidation:
    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("employment_type", "풀타임"),
            ("experience_level", "경력 3년 이상"),
            ("education_level", "대졸"),
            ("apply_method", "홈페이지"),
        ],
    )
    def test_free_text_is_rejected(self, client: TestClient, field: str, value: str) -> None:
        """예전처럼 직접 친 표현은 이제 막는다. 그대로 두면 공고와 AI 프롬프트로 흘러간다."""
        set_authenticated_actor(client, "emp-product-head")
        payload = request_payload() | {field: value}
        assert client.post("/api/v1/recruitment-requests", json=payload).status_code == 422

    def test_experienced_requires_years(self, client: TestClient) -> None:
        set_authenticated_actor(client, "emp-product-head")
        payload = request_payload()
        payload.pop("experience_years_min")
        assert client.post("/api/v1/recruitment-requests", json=payload).status_code == 422

    def test_new_discards_leftover_years(self, client: TestClient) -> None:
        """화면에서 '경력'을 골랐다가 '신입'으로 되돌린 흔적을 저장하지 않는다."""
        set_authenticated_actor(client, "emp-product-head")
        payload = request_payload() | {"experience_level": "NEW", "experience_years_min": 5}
        response = client.post("/api/v1/recruitment-requests", json=payload)
        assert response.status_code == 201
        body = response.json()
        assert body["experience_years_min"] is None
        assert body["experience_label"] == "신입"

    def test_new_posting_fields_are_optional(self, client: TestClient) -> None:
        body = create_draft(client)
        assert body["work_location"] is None
        assert body["apply_method"] is None
        assert body["experience_label"] == "경력 3년 이상"


def approve_into_posting(client: TestClient, payload: dict[str, object]) -> str:
    """채용 요청을 만들어 결재까지 통과시키고 생성된 공고 본문을 돌려준다."""
    set_authenticated_actor(client, "emp-product-head")
    created = client.post("/api/v1/recruitment-requests", json=payload)
    assert created.status_code == 201
    submitted = client.post(f"/api/v1/recruitment-requests/{created.json()['id']}/submit", json={})
    set_authenticated_actor(client, "emp-hr")
    approved = client.post(
        f"/api/v1/approvals/{submitted.json()['approval_document_id']}/approve", json={}
    )
    assert approved.status_code == 200
    postings = client.get("/api/v1/job-postings")
    assert postings.status_code == 200
    return postings.json()[0]["content"]


class TestPostingContent:
    def test_posting_carries_new_fields(self, client: TestClient) -> None:
        """결재 승인으로 만들어지는 공고 본문에 새로 받은 값이 들어간다."""
        content = approve_into_posting(
            client,
            request_payload()
            | {
                "education_level": "대졸 이상",
                "work_location": "서울 강남구",
                "salary": "면접 후 협의",
                "application_deadline": "2026-09-30",
                "apply_method": "잡코리아",
            },
        )
        assert "경력: 경력 3년 이상" in content
        assert "학력: 대졸 이상" in content
        assert "근무지: 서울 강남구" in content
        assert "급여: 면접 후 협의" in content
        assert "모집 마감: 2026-09-30" in content
        assert "지원 방법: 잡코리아" in content
        # 업무·역량은 공고의 전용 항목으로 내려가므로 본문에 다시 조합하지 않는다.
        assert "주요 업무" not in content
        assert "필수 역량" not in content
        assert "우대 사항" not in content

    def test_absent_fields_leave_no_line(self, client: TestClient) -> None:
        """값이 없으면 줄 자체를 넣지 않는다. '근무지: 미정'은 안 쓴 것만 못하다."""
        content = approve_into_posting(client, request_payload())
        assert "근무지" not in content
        assert "급여" not in content
        assert "지원 방법" not in content


class TestDraftContextPrefersDatabase:
    """AI 초안이 결재 승인된 값을 쓰는지 확인한다.

    이전에는 근무지·급여·마감일·지원방법을 AI 패널에서 매번 다시 입력했다. 결재자는
    그 값을 본 적이 없는데 공고에는 실렸다.
    """

    @staticmethod
    def _generation_input(client: TestClient, posting_id: str, payload: dict) -> dict:
        from app.models.ai_generation import AiGeneration

        response = client.post(
            "/api/v1/ai/job-posting-drafts", json={"job_posting_id": posting_id, **payload}
        )
        assert response.status_code == 200
        with client.app.state.testing_session_factory() as session:
            record = session.get(AiGeneration, response.json()["generation_id"])
            return dict(record.source_input)

    def test_database_value_wins_over_user_input(self, client: TestClient) -> None:
        payload = request_payload() | {
            "work_location": "서울 강남구",
            "salary": "면접 후 협의",
            "apply_method": "잡코리아",
            "education_level": "대졸 이상",
        }
        approve_into_posting(client, payload)
        set_authenticated_actor(client, "emp-hr", "ADMIN")
        posting_id = client.get("/api/v1/job-postings").json()[0]["id"]

        context = self._generation_input(
            client, posting_id, {"work_location": "부산", "salary": "5000만원"}
        )

        assert context["work_location"] == "서울 강남구"
        assert context["salary"] == "면접 후 협의"
        assert context["apply_method"] == "잡코리아"
        assert context["education_level"] == "대졸 이상"

    def test_experience_reaches_ai_as_readable_text(self, client: TestClient) -> None:
        """코드값을 그대로 넘기면 AI가 'EXPERIENCED'를 문장에 쓴다."""
        approve_into_posting(client, request_payload())
        set_authenticated_actor(client, "emp-hr", "ADMIN")
        posting_id = client.get("/api/v1/job-postings").json()[0]["id"]

        context = self._generation_input(client, posting_id, {})

        assert context["experience_level"] == "경력 3년 이상"

    def test_legacy_request_still_accepts_user_input(self, client: TestClient) -> None:
        """칼럼이 없던 시절의 요청은 DB가 비어 있어 사용자 입력으로 채운다."""
        approve_into_posting(client, request_payload())
        set_authenticated_actor(client, "emp-hr", "ADMIN")
        posting_id = client.get("/api/v1/job-postings").json()[0]["id"]

        context = self._generation_input(client, posting_id, {"work_location": "서울 본사"})

        assert context["work_location"] == "서울 본사"


def test_part_leader_can_be_selected_as_approver() -> None:
    """파트장은 팀원의 상급자이므로 결재자로 지정될 수 있어야 한다."""
    from app.domain.recruitment_policy import is_recruitment_approver

    assert is_recruitment_approver("파트장") is True
    assert is_recruitment_approver("팀장") is True
    assert is_recruitment_approver("대표이사") is True
    assert is_recruitment_approver("선임") is False
    assert is_recruitment_approver("사원") is False
