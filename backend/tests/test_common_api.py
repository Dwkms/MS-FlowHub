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
    assert payload["total"] == 54
    assert payload["items"][0]["employee_no"] == "MS0001"


def test_list_departments_returns_organization_departments(client: TestClient) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0003", role="EMPLOYEE", auth_user_id="auth-employee"
    )

    response = client.get("/api/v1/departments")

    assert response.status_code == 200
    assert {"DEV", "MKT", "HR", "PLAN", "CS"} <= {
        department["code"] for department in response.json()
    }


def test_department_manager_can_list_entire_department(client: TestClient) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0002", role="TEAM_ADMIN", auth_user_id="auth-dev-manager"
    )

    response = client.get("/api/v1/employees?page_size=100")

    assert response.status_code == 200
    assert response.json()["total"] == 13
    assert {item["team_code"] for item in response.json()["items"]} >= {
        "DEV_SW",
        "DEV_HW",
        "DEV_QA",
    }


def test_part_admin_can_list_only_own_part(client: TestClient) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0047", role="PART_ADMIN", auth_user_id="auth-qa-manager"
    )

    response = client.get("/api/v1/employees?page_size=100")

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert {item["team_code"] for item in response.json()["items"]} == {"DEV_QA"}


def test_part_admins_are_confined_to_their_own_part(client: TestClient) -> None:
    part_scopes = (
        ("emp-ms0012", "MKT_1", 5),
        ("emp-ms0032", "PLAN_1", 5),
        ("emp-ms0042", "CS_1", 5),
    )
    for employee_id, team_code, expected_total in part_scopes:
        client.app.dependency_overrides[get_authenticated_actor] = lambda employee_id=employee_id: (
            ActorContext(
                employee_id=employee_id,
                role="PART_ADMIN",
                auth_user_id=f"auth-{employee_id}",
            )
        )

        response = client.get("/api/v1/employees?page_size=100")

        assert response.status_code == 200
        assert response.json()["total"] == expected_total
        assert {item["team_code"] for item in response.json()["items"]} == {team_code}


def test_team_admin_lists_the_whole_department_across_parts(client: TestClient) -> None:
    """팀장은 산하 모든 파트를 본다. 파트장(`PART_ADMIN`)과 갈리는 지점이다."""
    department_scopes = (
        # (팀장 사번, 부서 코드, 부서 인원, 부서에 속한 파트 코드)
        ("emp-ms0012", "MKT", 10, {"MKT_1", "MKT_2"}),
        ("emp-ms0032", "PLAN", 10, {"PLAN_1", "PLAN_2"}),
    )
    for employee_id, department_code, expected_total, team_codes in department_scopes:
        client.app.dependency_overrides[get_authenticated_actor] = lambda employee_id=employee_id: (
            ActorContext(
                employee_id=employee_id,
                role="TEAM_ADMIN",
                auth_user_id=f"auth-{employee_id}",
            )
        )

        response = client.get("/api/v1/employees?page_size=100")

        assert response.status_code == 200
        assert response.json()["total"] == expected_total
        assert {item["department_code"] for item in response.json()["items"]} == {department_code}
        assert {item["team_code"] for item in response.json()["items"]} == team_codes


def test_team_admin_without_part_still_sees_the_department(client: TestClient) -> None:
    """`team_id`가 비어 있는 팀장도 부서 전체를 본다.

    범위 기준이 역할에 고정돼 있으므로 `team_id` 유무가 결과를 바꾸지 않는다.
    """
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0002", role="TEAM_ADMIN", auth_user_id="auth-dev-head"
    )

    response = client.get("/api/v1/employees?page_size=100")

    assert response.status_code == 200
    assert {item["department_code"] for item in response.json()["items"]} == {"DEV"}
    assert {item["team_code"] for item in response.json()["items"]} == {
        None,
        "DEV_SW",
        "DEV_HW",
        "DEV_QA",
    }


def test_part_admin_without_part_sees_only_self(client: TestClient) -> None:
    """파트가 지정되지 않은 파트장은 부서 전체로 넓어지지 않는다."""
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0002", role="PART_ADMIN", auth_user_id="auth-dev-head"
    )

    response = client.get("/api/v1/employees?page_size=100")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == ["emp-ms0002"]


def test_dashboard_reflects_selected_employee_access(client: TestClient) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0001", role="SUPER_ADMIN", auth_user_id="auth-admin"
    )
    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_employee"]["role"] == "ADMIN"
    assert payload["metrics"][0]["value"] == 0
    assert [metric["label"] for metric in payload["metrics"]] == [
        "내 결재 대기",
        "내가 상신한 결재",
        "진행 중 채용",
    ]
    assert "CRM Lite" not in payload["accessible_modules"]
    assert payload["analytics"]["approval_by_status"] == []
    assert payload["analytics"]["applicant_by_stage"] == []
    assert payload["analytics"]["recruitment_request_count"] == 0
    assert payload["analytics"]["average_approval_processing_hours"] is None
    assert payload["analytics"]["attendance_by_status"]
    assert payload["analytics"]["today_attendance_unregistered_count"] == 5


def test_dashboard_hides_organization_analytics_from_employee(client: TestClient) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0003", role="EMPLOYEE", auth_user_id="auth-employee"
    )

    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    assert response.json()["analytics"] is None


def test_dashboard_requires_bearer_auth(client: TestClient) -> None:
    response = client.get("/api/v1/dashboard")

    assert response.status_code == 401


def test_list_departments_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/departments")

    assert response.status_code == 401
