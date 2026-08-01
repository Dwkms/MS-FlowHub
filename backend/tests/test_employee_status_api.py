from fastapi.testclient import TestClient

from app.api.dependencies import get_current_actor
from app.security.identity import ActorContext


def test_employee_filters_combine_employment_and_daily_work_status(client: TestClient) -> None:
    response = client.get(
        "/api/v1/employees",
        params={"employment_status": "ACTIVE", "daily_work_status": "WORKING"},
    )

    assert response.status_code == 200
    assert all(item["employment_status"] == "ACTIVE" for item in response.json()["items"])
    assert all(item["daily_work_status"] == "WORKING" for item in response.json()["items"])


def test_sick_leave_requires_public_reason_and_redacts_private_note(client: TestClient) -> None:
    client.app.dependency_overrides[get_current_actor] = lambda: ActorContext(
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


def test_admin_can_view_private_reason_detail(client: TestClient) -> None:
    client.app.dependency_overrides[get_current_actor] = lambda: ActorContext(
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

    response = client.get("/api/v1/employees/emp-ms0010", params={"actor_id": "emp-ms0001"})

    assert response.status_code == 200
    assert response.json()["daily_work_reason"]["private_note"] == "진단 상세"
