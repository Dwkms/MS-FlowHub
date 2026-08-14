from fastapi.testclient import TestClient

from app.api.dependencies import get_authenticated_actor
from app.security.identity import ActorContext


def set_authenticated_actor(client: TestClient, employee_id: str, role: str | None = None) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id=employee_id,
        role=role or ("SUPER_ADMIN" if employee_id == "emp-head" else "EMPLOYEE"),
        auth_user_id=f"auth-{employee_id}",
    )


def create_draft(
    client: TestClient, *, author_id: str = "emp-head", approver_id: str | None = None
) -> dict:
    set_authenticated_actor(client, author_id)
    response = client.post(
        "/api/v1/approvals",
        json={
            "title": "Laptop purchase request",
            "document_type": "GENERAL",
            "content": "Request a laptop for development work.",
            "department_id": "dept-product" if author_id == "emp-head" else "dept-hr",
            "approver_id": approver_id or ("emp-hr" if author_id == "emp-head" else "emp-head"),
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_uses_authenticated_employee_as_author(client: TestClient) -> None:
    draft = create_draft(client)

    assert draft["author_id"] == "emp-head"
    assert draft["histories"][-1]["actor_id"] == "emp-head"


def test_author_can_update_draft_without_actor_id(client: TestClient) -> None:
    draft = create_draft(client)

    response = client.patch(f"/api/v1/approvals/{draft['id']}", json={"title": "Updated request"})

    assert response.status_code == 200
    assert response.json()["title"] == "Updated request"
    assert response.json()["histories"][-1]["actor_id"] == "emp-head"


def test_general_employee_cannot_be_selected_as_approver(client: TestClient) -> None:
    set_authenticated_actor(client, "emp-head")

    response = client.post(
        "/api/v1/approvals",
        json={
            "title": "Invalid approver request",
            "document_type": "GENERAL",
            "content": "A general employee cannot approve this document.",
            "department_id": "dept-product",
            "approver_id": "emp-sales",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "결재자는 파트장급 이상만 지정할 수 있습니다."


def test_draft_cannot_change_approver_to_general_employee(client: TestClient) -> None:
    draft = create_draft(client)

    response = client.patch(f"/api/v1/approvals/{draft['id']}", json={"approver_id": "emp-sales"})

    assert response.status_code == 422


def test_non_author_cannot_update_draft(client: TestClient) -> None:
    draft = create_draft(client)
    set_authenticated_actor(client, "emp-hr")

    response = client.patch(
        f"/api/v1/approvals/{draft['id']}", json={"title": "Unauthorized update"}
    )

    assert response.status_code == 403


def test_non_admin_cannot_create_for_another_department(client: TestClient) -> None:
    set_authenticated_actor(client, "emp-hr")

    response = client.post(
        "/api/v1/approvals",
        json={
            "title": "Wrong department request",
            "document_type": "GENERAL",
            "content": "This must be rejected.",
            "department_id": "dept-sales",
            "approver_id": "emp-head",
        },
    )

    assert response.status_code == 400


def test_admin_can_create_for_another_department(client: TestClient) -> None:
    set_authenticated_actor(client, "emp-head")

    response = client.post(
        "/api/v1/approvals",
        json={
            "title": "Sales department request",
            "document_type": "GENERAL",
            "content": "A request created by an administrator.",
            "department_id": "dept-sales",
            "approver_id": "emp-hr",
        },
    )

    assert response.status_code == 201
    assert response.json()["author_id"] == "emp-head"
    assert response.json()["department_id"] == "dept-sales"


def test_list_is_scoped_to_authenticated_employee(client: TestClient) -> None:
    create_draft(client, author_id="emp-hr")
    set_authenticated_actor(client, "emp-sales-head")

    response = client.get("/api/v1/approvals")

    assert response.status_code == 200
    assert response.json() == []


def test_admin_lists_all_documents_without_employee_id(client: TestClient) -> None:
    create_draft(client, author_id="emp-hr")
    set_authenticated_actor(client, "emp-head")

    response = client.get("/api/v1/approvals")

    assert response.status_code == 200
    assert response.json()[0]["author_id"] == "emp-hr"


def test_admin_can_delete_document_without_actor_id(client: TestClient) -> None:
    draft = create_draft(client, author_id="emp-hr")
    set_authenticated_actor(client, "emp-head")

    response = client.delete(f"/api/v1/approvals/{draft['id']}")

    assert response.status_code == 204


def test_non_admin_cannot_delete_document(client: TestClient) -> None:
    draft = create_draft(client, author_id="emp-hr")

    response = client.delete(f"/api/v1/approvals/{draft['id']}")

    assert response.status_code == 403


def test_submit_and_approve_flow_uses_authenticated_actors(client: TestClient) -> None:
    draft = create_draft(client)
    submit_response = client.post(f"/api/v1/approvals/{draft['id']}/submit", json={})
    set_authenticated_actor(client, "emp-hr")
    approve_response = client.post(
        f"/api/v1/approvals/{draft['id']}/approve", json={"comment": "Approved"}
    )

    assert submit_response.status_code == 200
    assert approve_response.status_code == 200
    assert approve_response.json()["histories"][-1]["actor_id"] == "emp-hr"


def test_super_admin_can_approve_other_employees_document(client: TestClient) -> None:
    draft = create_draft(client, author_id="emp-hr", approver_id="emp-sales-head")
    submitted = client.post(f"/api/v1/approvals/{draft['id']}/submit", json={})
    set_authenticated_actor(client, "emp-head", role="SUPER_ADMIN")

    response = client.post(f"/api/v1/approvals/{draft['id']}/approve", json={})

    assert submitted.status_code == 200
    assert response.status_code == 200


def test_hr_admin_can_approve_assigned_document(client: TestClient) -> None:
    draft = create_draft(client, approver_id="emp-hr")
    submitted = client.post(f"/api/v1/approvals/{draft['id']}/submit", json={})
    set_authenticated_actor(client, "emp-hr", role="HR_ADMIN")

    response = client.post(f"/api/v1/approvals/{draft['id']}/approve", json={})

    assert submitted.status_code == 200
    assert response.status_code == 200


def test_team_admin_can_approve_same_team_document(client: TestClient) -> None:
    draft = create_draft(client, approver_id="emp-hr")
    submitted = client.post(f"/api/v1/approvals/{draft['id']}/submit", json={})
    set_authenticated_actor(client, "emp-product-head", role="TEAM_ADMIN")

    response = client.post(f"/api/v1/approvals/{draft['id']}/approve", json={})

    assert submitted.status_code == 200
    assert response.status_code == 200


def test_team_admin_without_team_can_approve_department_document(client: TestClient) -> None:
    """`team_id`가 비어 있는 팀장도 같은 부서 문서를 처리할 수 있어야 한다.

    이전에는 관리자 경로가 `team_id` 일치만 확인해서, `team_id`가 없는 팀장은
    지정 결재자로 걸린 문서 외에는 한 건도 처리할 수 없었다.
    """
    set_authenticated_actor(client, "emp-sales")
    created = client.post(
        "/api/v1/approvals",
        json={
            "title": "Sales laptop request",
            "document_type": "GENERAL",
            "content": "Request a laptop for the sales team.",
            "department_id": "dept-sales",
            "approver_id": "emp-head",
        },
    )
    assert created.status_code == 201
    draft = created.json()
    submitted = client.post(f"/api/v1/approvals/{draft['id']}/submit", json={})

    set_authenticated_actor(client, "emp-sales-head", role="TEAM_ADMIN")
    response = client.post(f"/api/v1/approvals/{draft['id']}/approve", json={})

    assert submitted.status_code == 200
    assert response.status_code == 200


def test_team_admin_cannot_approve_other_department_document(client: TestClient) -> None:
    draft = create_draft(client, approver_id="emp-hr")
    submitted = client.post(f"/api/v1/approvals/{draft['id']}/submit", json={})
    set_authenticated_actor(client, "emp-sales-head", role="TEAM_ADMIN")

    response = client.post(f"/api/v1/approvals/{draft['id']}/approve", json={})

    assert submitted.status_code == 200
    assert response.status_code == 403


def test_part_admin_can_approve_only_within_own_part(client: TestClient) -> None:
    """파트장은 같은 파트 문서만 처리한다. 부서가 같아도 파트가 다르면 막힌다."""
    same_part = create_draft(client, approver_id="emp-hr")
    client.post(f"/api/v1/approvals/{same_part['id']}/submit", json={})
    set_authenticated_actor(client, "emp-product-head", role="PART_ADMIN")
    allowed = client.post(f"/api/v1/approvals/{same_part['id']}/approve", json={})

    other_part = create_draft(client, approver_id="emp-hr")
    client.post(f"/api/v1/approvals/{other_part['id']}/submit", json={})
    set_authenticated_actor(client, "emp-sales-head", role="PART_ADMIN")
    denied = client.post(f"/api/v1/approvals/{other_part['id']}/approve", json={})

    assert allowed.status_code == 200
    assert denied.status_code == 403


def test_team_admin_can_reject_assigned_document(client: TestClient) -> None:
    draft = create_draft(client, approver_id="emp-sales-head")
    submitted = client.post(f"/api/v1/approvals/{draft['id']}/submit", json={})
    set_authenticated_actor(client, "emp-sales-head", role="TEAM_ADMIN")

    response = client.post(
        f"/api/v1/approvals/{draft['id']}/reject", json={"comment": "보완이 필요합니다."}
    )

    assert submitted.status_code == 200
    assert response.status_code == 200


def test_author_cannot_approve_own_document_even_as_super_admin(client: TestClient) -> None:
    draft = create_draft(client)
    submitted = client.post(f"/api/v1/approvals/{draft['id']}/submit", json={})

    response = client.post(f"/api/v1/approvals/{draft['id']}/approve", json={})

    assert submitted.status_code == 200
    assert response.status_code == 403


def test_unassigned_approver_cannot_approve_document(client: TestClient) -> None:
    draft = create_draft(client)
    submitted = client.post(f"/api/v1/approvals/{draft['id']}/submit", json={})
    set_authenticated_actor(client, "emp-sales")

    response = client.post(f"/api/v1/approvals/{draft['id']}/approve", json={})

    assert submitted.status_code == 200
    assert response.status_code == 403
