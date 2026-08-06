from fastapi.testclient import TestClient

from app.api.dependencies import get_authenticated_actor
from app.security.identity import ActorContext


def set_authenticated_actor(client: TestClient, employee_id: str, role: str = "EMPLOYEE") -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id=employee_id,
        role=role,
        auth_user_id=f"auth-{employee_id}",
    )


def request_payload() -> dict[str, object]:
    return {
        "request_department_id": "dept-product",
        "approver_id": "emp-hr",
        "position_title": "Backend Developer",
        "headcount": 1,
        "employment_type": "Full time",
        "experience_level": "Junior",
        "reason": "Additional development capacity is required.",
        "responsibilities": "Develop FastAPI services.",
        "required_skills": "Python, SQL",
        "preferred_skills": "PostgreSQL",
        "desired_start_date": "2026-09-01",
    }


def create_draft(client: TestClient) -> dict:
    set_authenticated_actor(client, "emp-product-head")
    response = client.post("/api/v1/recruitment-requests", json=request_payload())
    assert response.status_code == 201
    return response.json()


def test_create_uses_authenticated_employee_as_requester(client: TestClient) -> None:
    request = create_draft(client)

    assert request["requester_id"] == "emp-product-head"


def test_requester_can_read_own_request_and_list(client: TestClient) -> None:
    request = create_draft(client)

    detail = client.get(f"/api/v1/recruitment-requests/{request['id']}")
    listed = client.get("/api/v1/recruitment-requests")

    assert detail.status_code == 200
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == request["id"]


def test_request_rejects_invalid_approver(client: TestClient) -> None:
    set_authenticated_actor(client, "emp-product-head")
    payload = request_payload()
    payload["approver_id"] = "emp-sales"

    response = client.post("/api/v1/recruitment-requests", json=payload)

    assert response.status_code == 422


def test_super_admin_can_approve_own_recruitment_request(client: TestClient) -> None:
    set_authenticated_actor(client, "emp-head", role="SUPER_ADMIN")
    payload = request_payload()
    payload["approver_id"] = "emp-head"

    created = client.post("/api/v1/recruitment-requests", json=payload)
    assert created.status_code == 201
    submitted = client.post(f"/api/v1/recruitment-requests/{created.json()['id']}/submit", json={})
    approved = client.post(
        f"/api/v1/approvals/{submitted.json()['approval_document_id']}/approve", json={}
    )

    assert submitted.status_code == 200
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"


def test_requester_can_upload_poster_without_actor_id(client: TestClient) -> None:
    request = create_draft(client)

    response = client.post(
        f"/api/v1/recruitment-requests/{request['id']}/poster",
        files={"poster": ("poster.png", b"poster", "image/png")},
    )

    assert response.status_code == 200
    assert response.json()["poster_original_name"] == "poster.png"

    downloaded = client.get(f"/api/v1/recruitment-requests/{request['id']}/poster")

    assert downloaded.status_code == 200
    assert downloaded.content == b"poster"


def test_unrelated_employee_cannot_upload_poster(client: TestClient) -> None:
    request = create_draft(client)
    set_authenticated_actor(client, "emp-sales")

    response = client.post(
        f"/api/v1/recruitment-requests/{request['id']}/poster",
        files={"poster": ("poster.png", b"poster", "image/png")},
    )

    assert response.status_code == 403


def test_submit_uses_authenticated_requester(client: TestClient) -> None:
    request = create_draft(client)

    response = client.post(
        f"/api/v1/recruitment-requests/{request['id']}/submit", json={"comment": "Please review."}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PENDING_APPROVAL"
    assert response.json()["approval_document_id"] is not None


def test_non_requester_cannot_submit(client: TestClient) -> None:
    request = create_draft(client)
    set_authenticated_actor(client, "emp-sales")

    response = client.post(f"/api/v1/recruitment-requests/{request['id']}/submit", json={})

    assert response.status_code == 403


def test_approval_creates_job_posting(client: TestClient) -> None:
    request = create_draft(client)
    submitted = client.post(f"/api/v1/recruitment-requests/{request['id']}/submit", json={})
    set_authenticated_actor(client, "emp-hr")
    approved = client.post(
        f"/api/v1/approvals/{submitted.json()['approval_document_id']}/approve", json={}
    )

    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"


def test_only_super_admin_can_delete_request(client: TestClient) -> None:
    request = create_draft(client)
    set_authenticated_actor(client, "emp-hr")
    forbidden = client.delete(f"/api/v1/recruitment-requests/{request['id']}")
    set_authenticated_actor(client, "emp-head", role="SUPER_ADMIN")
    deleted = client.delete(f"/api/v1/recruitment-requests/{request['id']}")

    assert forbidden.status_code == 403
    assert deleted.status_code == 204


def test_super_admin_can_delete_linked_recruitment_approval(client: TestClient) -> None:
    request = create_draft(client)
    submitted = client.post(f"/api/v1/recruitment-requests/{request['id']}/submit", json={})
    assert submitted.status_code == 200

    set_authenticated_actor(client, "emp-head", role="SUPER_ADMIN")
    deleted = client.delete(f"/api/v1/approvals/{submitted.json()['approval_document_id']}")
    missing_request = client.get(f"/api/v1/recruitment-requests/{request['id']}")

    assert deleted.status_code == 204
    assert missing_request.status_code == 404


def test_approval_processing_creates_job_posting(client: TestClient) -> None:
    request = create_draft(client)
    submitted = client.post(f"/api/v1/recruitment-requests/{request['id']}/submit", json={})
    set_authenticated_actor(client, "emp-hr")
    approved = client.post(
        f"/api/v1/approvals/{submitted.json()['approval_document_id']}/approve", json={}
    )

    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
