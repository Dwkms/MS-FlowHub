"""승인된 채용공고의 AI 포스터 미리보기 API 테스트."""

from datetime import date

from fastapi.testclient import TestClient

from app.api.dependencies import get_authenticated_actor, get_image_ai_provider
from app.domain.image_ai_provider import ImageAIProviderResult
from app.models.ai_generation import AiGeneration
from app.models.recruitment import JobPosting, RecruitmentRequest
from tests.test_ai_job_posting_api import create_posting, set_authenticated_actor

POSTER_URL = "/api/v1/ai/job-posting-posters"


def test_poster_uses_approved_facts_and_returns_preview(client: TestClient) -> None:
    posting = create_posting(client)
    with client.app.state.testing_session_factory() as session:
        stored_posting = session.get(JobPosting, posting["id"])
        request = session.get(RecruitmentRequest, stored_posting.recruitment_request_id)
        request.work_location = "서울 강남구"
        request.salary = "연봉 5,000만원"
        request.application_deadline = date(2026, 9, 30)
        session.commit()
        before_content = stored_posting.content
        before_status = stored_posting.status

    response = client.post(
        POSTER_URL,
        json={"job_posting_id": posting["id"], "design_direction": "간결한 기술 기업 스타일"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["content_type"] == "image/png"
    assert body["image_base64"]

    with client.app.state.testing_session_factory() as session:
        record = session.get(AiGeneration, body["generation_id"])
        after_posting = session.get(JobPosting, posting["id"])
        assert record.feature_type == "JOB_POSTER"
        assert record.related_type == "JOB_POSTING"
        assert record.related_id == posting["id"]
        assert record.source_input["work_location"] == "서울 강남구"
        assert record.source_input["salary"] == "연봉 5,000만원"
        assert record.source_input["application_deadline"] == "2026-09-30"
        assert record.source_input["design_direction"] == "간결한 기술 기업 스타일"
        assert "image_base64" not in record.generated_output
        assert record.generated_output["delivery"] == "preview_only"
        assert after_posting.content == before_content
        assert after_posting.status == before_status


def test_absent_facts_are_not_added_to_poster_context(client: TestClient) -> None:
    posting = create_posting(client)

    generation_id = client.post(POSTER_URL, json={"job_posting_id": posting["id"]}).json()[
        "generation_id"
    ]

    with client.app.state.testing_session_factory() as session:
        context = session.get(AiGeneration, generation_id).source_input
        assert "work_location" not in context
        assert "salary" not in context
        assert "application_deadline" not in context
        assert "design_direction" not in context


def test_poster_requires_hr_permission(client: TestClient) -> None:
    posting = create_posting(client)
    set_authenticated_actor(client, "emp-sales", role="EMPLOYEE")

    response = client.post(POSTER_URL, json={"job_posting_id": posting["id"]})

    assert response.status_code == 403


def test_poster_rejects_unknown_posting(client: TestClient) -> None:
    create_posting(client)

    response = client.post(POSTER_URL, json={"job_posting_id": "missing"})

    assert response.status_code == 404


def test_provider_failure_is_200_and_does_not_change_posting(client: TestClient) -> None:
    posting = create_posting(client)

    class FailingProvider:
        def generate(self, prompt: str) -> ImageAIProviderResult:
            return ImageAIProviderResult(
                provider="openai",
                success=False,
                model_name="gpt-image-2",
                error_message="이미지 생성 실패",
            )

    client.app.dependency_overrides[get_image_ai_provider] = FailingProvider
    response = client.post(POSTER_URL, json={"job_posting_id": posting["id"]})

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert response.json()["image_base64"] is None
    with client.app.state.testing_session_factory() as session:
        assert session.get(JobPosting, posting["id"]).status == "DRAFT"


def test_short_design_direction_is_rejected(client: TestClient) -> None:
    posting = create_posting(client)

    response = client.post(
        POSTER_URL,
        json={"job_posting_id": posting["id"], "design_direction": "짧음"},
    )

    assert response.status_code == 422


def test_image_global_limit_blocks_before_provider_call(client: TestClient) -> None:
    posting = create_posting(client)
    employees = ["emp-hr", "emp-sales", "emp-sales-head"]

    for index in range(5):
        set_authenticated_actor(client, employees[index // 2], role="HR_ADMIN")
        assert client.post(POSTER_URL, json={"job_posting_id": posting["id"]}).status_code == 200

    # 이 계정은 개인 한도가 남았지만 일반 계정 전체 호출이 5회라 전역 한도에 걸린다.
    blocked = client.post(POSTER_URL, json={"job_posting_id": posting["id"]})

    assert blocked.status_code == 429
    assert "5회" in blocked.json()["detail"]


def test_super_admin_bypasses_image_global_limit(client: TestClient) -> None:
    posting = create_posting(client)

    for _ in range(6):
        response = client.post(POSTER_URL, json={"job_posting_id": posting["id"]})
        assert response.status_code == 200


def test_poster_requires_authentication(client: TestClient) -> None:
    posting = create_posting(client)
    client.app.dependency_overrides.pop(get_authenticated_actor, None)

    response = client.post(POSTER_URL, json={"job_posting_id": posting["id"]})

    assert response.status_code == 401
