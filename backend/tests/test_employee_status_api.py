from fastapi.testclient import TestClient

from app.api.dependencies import get_authenticated_actor
from app.security.identity import ActorContext


def test_employee_filters_combine_employment_and_daily_work_status(client: TestClient) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0001", role="SUPER_ADMIN", auth_user_id="auth-admin"
    )
    response = client.get(
        "/api/v1/employees",
        params={"employment_status": "ACTIVE", "daily_work_status": "WORKING"},
    )

    assert response.status_code == 200
    assert all(item["employment_status"] == "ACTIVE" for item in response.json()["items"])
    assert all(item["daily_work_status"] == "WORKING" for item in response.json()["items"])


def test_sick_leave_requires_public_reason_and_redacts_private_note(client: TestClient) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0010", role="EMPLOYEE"
    )

    missing_reason = client.put(
        "/api/v1/employees/emp-ms0010/attendance",
        json={"work_status": "SICK_LEAVE"},
    )
    assert missing_reason.status_code == 422

    updated = client.put(
        "/api/v1/employees/emp-ms0010/attendance",
        json={
            "work_status": "SICK_LEAVE",
            "reason_category": "HEALTH",
            "reason_summary": "병원 진료",
            "private_note": "진단 상세",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["daily_work_reason"]["reason_summary"] == "병원 진료"
    assert updated.json()["daily_work_reason"]["private_note"] is None


def test_other_work_status_is_supported(client: TestClient) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0010", role="EMPLOYEE"
    )

    response = client.put(
        "/api/v1/employees/emp-ms0010/attendance",
        json={"work_status": "OTHER", "reason_summary": "기타 근무 상태"},
    )

    assert response.status_code == 200
    assert response.json()["daily_work_status"] == "OTHER"


def test_admin_can_view_private_reason_detail(client: TestClient) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0010", role="EMPLOYEE"
    )
    client.put(
        "/api/v1/employees/emp-ms0010/attendance",
        json={
            "work_status": "SICK_LEAVE",
            "reason_summary": "병원 진료",
            "private_note": "진단 상세",
        },
    )

    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0001", role="SUPER_ADMIN", auth_user_id="auth-admin"
    )
    response = client.get("/api/v1/employees/emp-ms0010")

    assert response.status_code == 200
    assert response.json()["daily_work_reason"]["private_note"] == "진단 상세"


def test_part_admin_can_update_own_part_but_not_other_part(client: TestClient) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0003", role="PART_ADMIN", auth_user_id="auth-sw-part-admin"
    )

    same_part = client.put(
        "/api/v1/employees/emp-ms0004/attendance",
        json={"work_status": "WORKING"},
    )
    other_part = client.put(
        "/api/v1/employees/emp-ms0008/attendance",
        json={"work_status": "WORKING"},
    )

    assert same_part.status_code == 200
    assert other_part.status_code == 403


def test_team_admin_can_update_any_part_in_the_department(client: TestClient) -> None:
    """팀장은 산하 파트를 가리지 않는다. 파트장이 막히는 DEV_HW도 처리할 수 있다."""
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0002", role="TEAM_ADMIN", auth_user_id="auth-dev-head"
    )

    sw_part = client.put(
        "/api/v1/employees/emp-ms0004/attendance",
        json={"work_status": "WORKING"},
    )
    hw_part = client.put(
        "/api/v1/employees/emp-ms0008/attendance",
        json={"work_status": "WORKING"},
    )

    assert sw_part.status_code == 200
    assert hw_part.status_code == 200


def test_team_admin_cannot_update_other_department(client: TestClient) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0002", role="TEAM_ADMIN", auth_user_id="auth-dev-head"
    )

    response = client.put(
        "/api/v1/employees/emp-ms0013/attendance",
        json={"work_status": "WORKING"},
    )

    assert response.status_code == 403


def test_part_admin_can_list_only_own_part_members(client: TestClient) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0003", role="PART_ADMIN", auth_user_id="auth-sw-part-admin"
    )

    response = client.get("/api/v1/employees")

    assert response.status_code == 200
    assert response.json()["items"]
    assert {item["team_code"] for item in response.json()["items"]} == {"DEV_SW"}


def test_attendance_change_history_records_only_actual_changes_and_redacts_private_note(
    client: TestClient,
) -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0010", role="EMPLOYEE"
    )
    payload = {
        "work_status": "SICK_LEAVE",
        "reason_category": "HEALTH",
        "reason_summary": "병원 진료",
        "private_note": "진단 상세",
        "work_date": "2030-01-02",
    }
    assert client.put("/api/v1/employees/emp-ms0010/attendance", json=payload).status_code == 200
    assert client.put("/api/v1/employees/emp-ms0010/attendance", json=payload).status_code == 200

    response = client.get(
        "/api/v1/employees/emp-ms0010/attendance-history", params={"work_date": "2030-01-02"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["before_work_status"] is None
    assert response.json()[0]["after_work_status"] == "SICK_LEAVE"
    assert response.json()[0]["after_private_note"] is None

    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0001", role="SUPER_ADMIN", auth_user_id="auth-admin"
    )
    admin_response = client.get(
        "/api/v1/employees/emp-ms0010/attendance-history", params={"work_date": "2030-01-02"}
    )

    assert admin_response.status_code == 200
    assert admin_response.json()[0]["after_private_note"] == "진단 상세"
