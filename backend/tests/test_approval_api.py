from fastapi.testclient import TestClient

from app.api.dependencies import get_authenticated_actor
from app.security.identity import ActorContext


def set_authenticated_actor(client: TestClient, employee_id: str) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id=employee_id,
        role="SUPER_ADMIN" if employee_id == "emp-head" else "EMPLOYEE",
        auth_user_id=f"auth-{employee_id}",
    )


def create_draft(client: TestClient, *, author_id: str = "emp-head") -> dict:
    set_authenticated_actor(client, author_id)
    response = client.post(
        "/api/v1/approvals",
        json={
            "title": "Laptop purchase request",
            "document_type": "GENERAL",
            "content": "Request a laptop for development work.",
            "department_id": "dept-product" if author_id == "emp-head" else "dept-hr",
            "approver_id": "emp-hr" if author_id == "emp-head" else "emp-sales",
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
