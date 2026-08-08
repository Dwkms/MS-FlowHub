from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.api.dependencies import get_current_auth_user
from app.models.auth import EmployeeAccount
from app.models.organization import Employee
from app.scripts.seed_auth_accounts import sync_employee_accounts, sync_selected_employee_accounts


def test_inactive_linked_account_is_blocked(client: TestClient) -> None:
    session_factory = client.app.state.testing_session_factory
    with session_factory() as session:
        session.add(
            EmployeeAccount(
                id="account-inactive",
                auth_user_id="auth-inactive",
                employee_id="emp-ms0011",
                role="EMPLOYEE",
                is_active=False,
            )
        )
        session.commit()
    client.app.dependency_overrides[get_current_auth_user] = lambda: "auth-inactive"

    response = client.get("/api/v1/employees")

    assert response.status_code == 403


def test_auth_user_without_employee_account_is_blocked(client: TestClient) -> None:
    client.app.dependency_overrides[get_current_auth_user] = lambda: "auth-unlinked"

    response = client.get("/api/v1/employees")

    assert response.status_code == 403


def test_auth_seed_sync_is_idempotent(client: TestClient) -> None:
    session_factory = client.app.state.testing_session_factory
    with session_factory() as session:
        employees = session.scalars(select(Employee).order_by(Employee.employee_no)).all()
        auth_users = {employee.email: f"auth-{employee.id}" for employee in employees}

        sync_employee_accounts(session, auth_users, "test-password")
        session.commit()
        first_count = session.scalar(select(func.count()).select_from(EmployeeAccount))

        sync_employee_accounts(session, auth_users, "test-password")
        session.commit()
        second_count = session.scalar(select(func.count()).select_from(EmployeeAccount))
        super_admin = session.scalar(
            select(EmployeeAccount).where(EmployeeAccount.employee_id == "emp-ms0001")
        )

    assert first_count == len(employees)
    assert second_count == first_count
    assert super_admin is not None
    assert super_admin.role == "SUPER_ADMIN"


def test_selected_auth_sync_creates_qa_part_accounts(client: TestClient) -> None:
    session_factory = client.app.state.testing_session_factory
    employee_nos = {"MS0012", "MS0013", "MS0014"}
    with session_factory() as session:
        employees = session.scalars(
            select(Employee).where(Employee.employee_no.in_(employee_nos))
        ).all()
        auth_users = {employee.email: f"auth-{employee.id}" for employee in employees}

        sync_selected_employee_accounts(session, employee_nos, auth_users, "test-password")
        session.commit()
        employee_ids = [employee.id for employee in employees]
        accounts = session.scalars(
            select(EmployeeAccount).where(EmployeeAccount.employee_id.in_(employee_ids))
        ).all()

    assert len(accounts) == 3
    assert {account.role for account in accounts} == {"TEAM_ADMIN", "EMPLOYEE"}
    qa_part_lead = next(account for account in accounts if account.employee_id == "emp-ms0047")
    assert qa_part_lead.role == "TEAM_ADMIN"
