from fastapi.testclient import TestClient

from app.api.dependencies import get_authenticated_actor
from app.security.identity import ActorContext


def set_authenticated_actor(client: TestClient, role: str) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0010", role=role, auth_user_id="auth-employee"
    )


def test_attendance_update_requires_bearer_auth(client: TestClient) -> None:
    response = client.put(
        "/api/v1/employees/emp-ms0010/attendance",
        json={"work_status": "WORKING"},
    )

    assert response.status_code == 401


def test_approval_submit_requires_bearer_auth(client: TestClient) -> None:
    response = client.post("/api/v1/approvals/missing/submit", json={})

    assert response.status_code == 401


def test_approval_decision_requires_bearer_auth(client: TestClient) -> None:
    approve_response = client.post("/api/v1/approvals/missing/approve", json={})
    reject_response = client.post(
        "/api/v1/approvals/missing/reject",
        json={"comment": "Reason"},
    )

    assert approve_response.status_code == 401
    assert reject_response.status_code == 401


def test_approval_authoring_endpoints_require_bearer_auth(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/approvals",
        json={
            "title": "Request",
            "document_type": "GENERAL",
            "content": "Content",
            "department_id": "dept-product",
            "approver_id": "emp-hr",
        },
    )
    list_response = client.get("/api/v1/approvals")
    update_response = client.patch("/api/v1/approvals/missing", json={"title": "Updated"})
    delete_response = client.delete("/api/v1/approvals/missing")

    assert create_response.status_code == 401
    assert list_response.status_code == 401
    assert update_response.status_code == 401
    assert delete_response.status_code == 401


def test_recruitment_mutation_endpoints_require_bearer_auth(client: TestClient) -> None:
    payload = {
        "request_department_id": "dept-product",
        "approver_id": "emp-hr",
        "position_title": "Developer",
        "headcount": 1,
        "employment_type": "Full time",
        "experience_level": "Junior",
        "reason": "Reason",
        "responsibilities": "Responsibilities",
    }
    create_response = client.post("/api/v1/recruitment-requests", json=payload)
    delete_response = client.delete("/api/v1/recruitment-requests/missing")
    submit_response = client.post("/api/v1/recruitment-requests/missing/submit", json={})
    posting_response = client.post("/api/v1/recruitment-requests/missing/job-posting")
    poster_response = client.post(
        "/api/v1/recruitment-requests/missing/poster",
        files={"poster": ("poster.png", b"poster", "image/png")},
    )

    assert create_response.status_code == 401
    assert delete_response.status_code == 401
    assert submit_response.status_code == 401
    assert posting_response.status_code == 401
    assert poster_response.status_code == 401


def test_recruitment_read_endpoints_require_bearer_auth(client: TestClient) -> None:
    list_response = client.get("/api/v1/recruitment-requests")
    detail_response = client.get("/api/v1/recruitment-requests/missing")
    poster_response = client.get("/api/v1/recruitment-requests/missing/poster")
    postings_response = client.get("/api/v1/job-postings")

    assert list_response.status_code == 401
    assert detail_response.status_code == 401
    assert poster_response.status_code == 401
    assert postings_response.status_code == 401


def test_employee_management_mutations_require_admin_role(client: TestClient) -> None:
    set_authenticated_actor(client, "EMPLOYEE")
    create_response = client.post(
        "/api/v1/employees",
        json={
            "employee_no": "NEW001",
            "name": "New Employee",
            "email": "new@example.test",
            "department_id": "dept-dev",
            "position": "Developer",
            "job_title": "Backend Developer",
        },
    )
    update_response = client.patch("/api/v1/employees/emp-ms0010", json={"name": "Changed"})
    delete_response = client.delete("/api/v1/employees/emp-ms0010")

    assert create_response.status_code == 403
    assert update_response.status_code == 403
    assert delete_response.status_code == 403


def test_hr_admin_can_update_employee(client: TestClient) -> None:
    set_authenticated_actor(client, "HR_ADMIN")

    response = client.patch("/api/v1/employees/emp-ms0010", json={"name": "Updated Name"})

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


def test_only_super_admin_can_change_employee_role(client: TestClient) -> None:
    set_authenticated_actor(client, "EMPLOYEE")
    employee_forbidden = client.patch(
        "/api/v1/employees/emp-ms0010/role", json={"role": "TEAM_ADMIN"}
    )
    set_authenticated_actor(client, "HR_ADMIN")
    hr_forbidden = client.patch("/api/v1/employees/emp-ms0010/role", json={"role": "TEAM_ADMIN"})
    set_authenticated_actor(client, "SUPER_ADMIN")
    allowed = client.patch("/api/v1/employees/emp-ms0010/role", json={"role": "TEAM_ADMIN"})

    assert employee_forbidden.status_code == 403
    assert hr_forbidden.status_code == 403
    assert allowed.status_code == 200
