from fastapi.testclient import TestClient

from app.api.dependencies import get_authenticated_actor, get_database_health
from app.security.identity import ActorContext


def test_health_reports_supabase_database_source(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["data_source"] == "supabase"


def test_health_does_not_report_ok_when_database_connection_fails(client: TestClient) -> None:
    client.app.dependency_overrides[get_database_health] = lambda: False

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "error"
    assert response.json()["data_source"] == "supabase"


def test_local_frontend_origin_is_allowed(client: TestClient) -> None:
    response = client.options(
        "/api/v1/employees",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"


def test_list_employees_returns_paginated_organization_seed(client: TestClient) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0001", role="SUPER_ADMIN", auth_user_id="auth-admin"
    )
    response = client.get("/api/v1/employees")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 51
    assert payload["items"][0]["employee_no"] == "MS0001"


def test_list_departments_returns_organization_departments(client: TestClient) -> None:
    response = client.get("/api/v1/departments")

    assert response.status_code == 200
    assert {"EXEC", "DEV", "MKT", "HR", "PLAN", "QA"} <= {
        department["code"] for department in response.json()
    }


def test_dashboard_reflects_selected_employee_access(client: TestClient) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0001", role="SUPER_ADMIN", auth_user_id="auth-admin"
    )
    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_employee"]["role"] == "ADMIN"
    assert payload["metrics"][0]["value"] == 0


def test_dashboard_requires_bearer_auth(client: TestClient) -> None:
    response = client.get("/api/v1/dashboard")

    assert response.status_code == 401
