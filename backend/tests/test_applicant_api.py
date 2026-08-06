from fastapi.testclient import TestClient

from app.api.dependencies import get_authenticated_actor
from app.security.identity import ActorContext


def set_authenticated_actor(client: TestClient, employee_id: str, role: str) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id=employee_id,
        role=role,
        auth_user_id=f"auth-{employee_id}",
    )


def create_job_posting(client: TestClient) -> dict[str, object]:
    set_authenticated_actor(client, "emp-product-head", "TEAM_ADMIN")
    created = client.post(
        "/api/v1/recruitment-requests",
        json={
            "request_department_id": "dept-product",
            "approver_id": "emp-hr",
            "position_title": "Backend Engineer",
            "headcount": 1,
            "employment_type": "정규직",
            "experience_level": "경력",
            "reason": "ATS 지원자 관리 테스트",
            "responsibilities": "백엔드 개발",
        },
    )
    assert created.status_code == 201
    submitted = client.post(f"/api/v1/recruitment-requests/{created.json()['id']}/submit", json={})
    assert submitted.status_code == 200
    set_authenticated_actor(client, "emp-hr", "HR_ADMIN")
    approved = client.post(
        f"/api/v1/approvals/{submitted.json()['approval_document_id']}/approve", json={}
    )
    assert approved.status_code == 200
    postings = client.get("/api/v1/job-postings")
    assert postings.status_code == 200
    return postings.json()[0]


def create_applicant(client: TestClient) -> dict[str, object]:
    posting = create_job_posting(client)
    created = client.post(
        f"/api/v1/job-postings/{posting['id']}/applicants",
        json={
            "name": "홍지원",
            "email": "Hong.Applicant@Example.com",
            "phone": "010-1234-5678",
            "career_summary": "FastAPI와 PostgreSQL 기반 서비스 개발 경험",
        },
    )
    assert created.status_code == 201
    return created.json()


def test_hr_admin_can_create_and_search_applicant(client: TestClient) -> None:
    applicant = create_applicant(client)

    listed = client.get("/api/v1/applicants", params={"search": "hong.applicant"})

    assert listed.status_code == 200
    assert listed.json()[0]["id"] == applicant["id"]
    assert applicant["email"] == "hong.applicant@example.com"
    assert applicant["stage"] == "APPLIED"
    assert applicant["stage_histories"][0]["from_stage"] is None


def test_stage_change_keeps_history_and_rejected_requires_note(client: TestClient) -> None:
    applicant = create_applicant(client)

    missing_note = client.post(
        f"/api/v1/applicants/{applicant['id']}/stage", json={"stage": "REJECTED"}
    )
    changed = client.post(
        f"/api/v1/applicants/{applicant['id']}/stage",
        json={"stage": "INTERVIEW", "note": "1차 인터뷰 진행"},
    )
    detail = client.get(f"/api/v1/applicants/{applicant['id']}")

    assert missing_note.status_code == 422
    assert changed.status_code == 200
    assert detail.json()["stage"] == "INTERVIEW"
    assert len(detail.json()["stage_histories"]) == 2
    assert detail.json()["stage_histories"][0]["from_stage"] == "APPLIED"


def test_team_admin_can_only_read_own_department_applicants(client: TestClient) -> None:
    applicant = create_applicant(client)

    set_authenticated_actor(client, "emp-product-head", "TEAM_ADMIN")
    allowed = client.get(f"/api/v1/applicants/{applicant['id']}")
    blocked_write = client.patch(f"/api/v1/applicants/{applicant['id']}", json={"name": "수정"})
    set_authenticated_actor(client, "emp-sales", "TEAM_ADMIN")
    denied = client.get(f"/api/v1/applicants/{applicant['id']}")

    assert allowed.status_code == 200
    assert blocked_write.status_code == 403
    assert denied.status_code == 403


def test_employee_cannot_read_or_delete_applicant(client: TestClient) -> None:
    applicant = create_applicant(client)

    set_authenticated_actor(client, "emp-sales", "EMPLOYEE")
    listed = client.get("/api/v1/applicants")
    deleted = client.delete(f"/api/v1/applicants/{applicant['id']}")

    assert listed.status_code == 403
    assert deleted.status_code == 403
