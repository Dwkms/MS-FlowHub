"""채용공고 AI 초안 API와 공고 수정 API 테스트.

`PATCH /job-postings/{id}`는 이번에 신설한 엔드포인트다. AI 전용이 아니라, 승인 시
자동 생성된 공고를 이후에 손볼 방법이 아예 없던 구멍을 메운 것이다.
"""

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.dependencies import get_authenticated_actor
from app.models.ai_generation import AiGeneration
from app.models.recruitment import JobPosting
from app.security.identity import ActorContext

DRAFT_URL = "/api/v1/ai/job-posting-drafts"


def set_authenticated_actor(client: TestClient, employee_id: str, role: str = "EMPLOYEE") -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id=employee_id, role=role, auth_user_id=f"auth-{employee_id}"
    )


def create_posting(client: TestClient) -> dict:
    """채용 요청 → 상신 → 승인으로 공고를 만든다. 승인 시 공고가 자동 생성된다."""
    set_authenticated_actor(client, "emp-head", role="SUPER_ADMIN")
    payload = {
        "request_department_id": "dept-product",
        "approver_id": "emp-head",
        "position_title": "백엔드 개발자",
        "headcount": 2,
        "employment_type": "정규직",
        "experience_level": "EXPERIENCED",
        "experience_years_min": 3,
        "reason": "서비스 확장에 따른 충원",
        "responsibilities": "API 설계\n데이터 모델링",
        "required_skills": "Python 3년 이상",
        "preferred_skills": "PostgreSQL 경험",
        "desired_start_date": "2026-09-01",
    }
    created = client.post("/api/v1/recruitment-requests", json=payload)
    assert created.status_code == 201
    submitted = client.post(f"/api/v1/recruitment-requests/{created.json()['id']}/submit", json={})
    approved = client.post(
        f"/api/v1/approvals/{submitted.json()['approval_document_id']}/approve", json={}
    )
    assert approved.status_code == 200

    postings = client.get("/api/v1/job-postings")
    assert postings.status_code == 200
    return postings.json()[0]


def test_draft_uses_request_facts_and_user_input(client: TestClient) -> None:
    posting = create_posting(client)

    response = client.post(
        DRAFT_URL,
        json={
            "job_posting_id": posting["id"],
            "work_location": "서울 본사",
            "application_deadline": "2026-09-30",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["is_sample"] is True
    output = body["output"]
    # 담당자가 쓴 개조식 텍스트가 항목 배열로 옮겨진다. 없던 항목을 만들지 않는다.
    assert output["responsibilities"] == ["API 설계", "데이터 모델링"]
    assert output["requirements"] == ["Python 3년 이상"]
    assert "2026-09-30" in output["closing_message"]


def test_draft_omits_absent_user_input_from_context(client: TestClient) -> None:
    """근무지·마감일을 입력하지 않으면 Context에 키가 없어 AI가 지어낼 근거가 없다."""
    posting = create_posting(client)

    generation_id = client.post(DRAFT_URL, json={"job_posting_id": posting["id"]}).json()[
        "generation_id"
    ]

    with client.app.state.testing_session_factory() as session:
        record = session.get(AiGeneration, generation_id)
        assert "work_location" not in record.source_input
        assert "application_deadline" not in record.source_input
        assert "salary" not in record.source_input
        # DB에 있는 사실은 들어간다.
        assert record.source_input["position_title"] == "백엔드 개발자"
        assert record.related_type == "JOB_POSTING"
        assert record.related_id == posting["id"]


def test_draft_does_not_change_posting_or_request_state(client: TestClient) -> None:
    """초안 생성만으로 공고 본문이나 상태가 바뀌면 안 된다."""
    posting = create_posting(client)
    with client.app.state.testing_session_factory() as session:
        before = session.get(JobPosting, posting["id"])
        before_content, before_status = before.content, before.status

    assert client.post(DRAFT_URL, json={"job_posting_id": posting["id"]}).status_code == 200

    with client.app.state.testing_session_factory() as session:
        after = session.get(JobPosting, posting["id"])
        assert after.content == before_content
        assert after.status == before_status


def test_draft_requires_hr_permission(client: TestClient) -> None:
    posting = create_posting(client)
    set_authenticated_actor(client, "emp-sales", role="EMPLOYEE")

    response = client.post(DRAFT_URL, json={"job_posting_id": posting["id"]})

    assert response.status_code == 403


def test_draft_rejects_unknown_posting(client: TestClient) -> None:
    create_posting(client)

    response = client.post(DRAFT_URL, json={"job_posting_id": "no-such-posting"})

    assert response.status_code == 404


def test_too_short_optional_input_is_rejected(client: TestClient) -> None:
    """선택 항목이라도 값을 넣었다면 최소 길이를 요구한다.

    다만 길이 검증의 한계는 분명하다. `근무 위치`는 "서울"이 2자라 최소를 2자로 둘 수밖에
    없고, 그러면 "ㅇㅇ" 같은 2자 낙서는 통과한다. 문장을 기대하는 항목(지원 방법·팀 소개)
    에서만 실효가 있으며, 무의미한 입력의 최종 방어선은 사용자가 보는 미리보기다.
    """
    posting = create_posting(client)

    short_sentence = client.post(
        DRAFT_URL, json={"job_posting_id": posting["id"], "apply_method": "ㅇㅇ"}
    )
    single_char = client.post(
        DRAFT_URL, json={"job_posting_id": posting["id"], "work_location": "ㅇ"}
    )

    assert short_sentence.status_code == 422
    assert single_char.status_code == 422


def test_all_optional_inputs_may_be_omitted(client: TestClient) -> None:
    """비워두는 것은 정상이다. 최소 길이는 '넣었을 때'만 적용된다."""
    posting = create_posting(client)

    response = client.post(DRAFT_URL, json={"job_posting_id": posting["id"]})

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_patch_updates_title_and_content(client: TestClient) -> None:
    posting = create_posting(client)

    response = client.patch(
        f"/api/v1/job-postings/{posting['id']}",
        json={"title": "백엔드 개발자 채용", "content": "AI가 다듬은 공고 본문"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "백엔드 개발자 채용"
    assert response.json()["content"] == "AI가 다듬은 공고 본문"


def test_patch_cannot_change_status(client: TestClient) -> None:
    """`status`를 받지 않는다. AI 흐름이 공고를 게시 상태로 바꾸는 경로를 원천 차단한다."""
    posting = create_posting(client)
    with client.app.state.testing_session_factory() as session:
        before_status = session.get(JobPosting, posting["id"]).status

    response = client.patch(
        f"/api/v1/job-postings/{posting['id']}",
        json={"content": "본문만 수정", "status": "PUBLISHED"},
    )

    assert response.status_code == 200
    with client.app.state.testing_session_factory() as session:
        assert session.get(JobPosting, posting["id"]).status == before_status


def test_patch_requires_hr_permission(client: TestClient) -> None:
    posting = create_posting(client)
    set_authenticated_actor(client, "emp-sales", role="EMPLOYEE")

    response = client.patch(f"/api/v1/job-postings/{posting['id']}", json={"content": "무단 수정"})

    assert response.status_code == 403


def test_patch_requires_at_least_one_field(client: TestClient) -> None:
    posting = create_posting(client)

    response = client.patch(f"/api/v1/job-postings/{posting['id']}", json={})

    assert response.status_code == 422


def test_existing_recruitment_flow_still_creates_posting(client: TestClient) -> None:
    """기존 채용 요청 → 승인 → 공고 생성 흐름 회귀 확인."""
    posting = create_posting(client)

    with client.app.state.testing_session_factory() as session:
        stored = session.scalars(select(JobPosting)).all()

    assert len(stored) == 1
    assert stored[0].id == posting["id"]
    assert posting["headcount"] == 2
