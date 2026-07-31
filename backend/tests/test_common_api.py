from fastapi.testclient import TestClient

import app.main as main_module


def test_health_uses_local_without_database_url(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["data_source"] == "local"


def test_health_does_not_report_ok_when_database_connection_fails(client, monkeypatch) -> None:
    monkeypatch.setattr(main_module, "check_database_connection", lambda: False)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "error"
    assert response.json()["data_source"] == "local"


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


def test_list_employees_returns_sample_roles(client: TestClient) -> None:
    response = client.get("/api/v1/employees")

    assert response.status_code == 200
    roles = {employee["role"] for employee in response.json()}
    assert {"ADMIN", "HR_MANAGER", "SALES_REP", "SALES_MANAGER"} <= roles


def test_list_departments_returns_five_sample_departments(client: TestClient) -> None:
    response = client.get("/api/v1/departments")

    assert response.status_code == 200
    assert {department["code"] for department in response.json()} == {
        "DEV",
        "FINANCE",
        "HR",
        "PRODUCT",
        "SALES",
    }


def test_dashboard_reflects_selected_employee_access(client: TestClient) -> None:
    response = client.get("/api/v1/dashboard", params={"employee_id": "emp-sales"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_employee"]["role"] == "SALES_REP"
    assert payload["accessible_modules"] == ["전자결재", "CRM Lite"]
    assert payload["metrics"][0]["value"] == 0


def test_dashboard_rejects_unknown_employee(client: TestClient) -> None:
    response = client.get("/api/v1/dashboard", params={"employee_id": "missing"})

    assert response.status_code == 404
