from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.api.dependencies import get_authenticated_actor
from app.models.auth import EmployeeAccount
from app.models.organization import Employee
from app.scripts.seed_e2e_auth_accounts import E2E_ACCOUNTS, sync_e2e_auth_accounts
from app.security.identity import ActorContext


def test_e2e_auth_seed_is_idempotent(client: TestClient) -> None:
    session_factory = client.app.state.testing_session_factory
    passwords = {spec["id"]: "test-password" for spec in E2E_ACCOUNTS}
    auth_users = {spec["email"]: f"auth-{spec['id']}" for spec in E2E_ACCOUNTS}

    with session_factory() as session:
        sync_e2e_auth_accounts(session, auth_users, passwords, lambda _user_id, _password: None)
        session.commit()
        first_count = session.scalar(
            select(func.count())
            .select_from(EmployeeAccount)
            .where(EmployeeAccount.employee_id.in_([spec["id"] for spec in E2E_ACCOUNTS]))
        )

        sync_e2e_auth_accounts(session, auth_users, passwords, lambda _user_id, _password: None)
        session.commit()
        second_count = session.scalar(
            select(func.count())
            .select_from(EmployeeAccount)
            .where(EmployeeAccount.employee_id.in_([spec["id"] for spec in E2E_ACCOUNTS]))
        )
        super_admin = session.get(EmployeeAccount, "account-emp-e2e-super-admin")
        employees = session.scalars(
            select(Employee).where(Employee.id.in_([spec["id"] for spec in E2E_ACCOUNTS]))
        ).all()

    assert first_count == len(E2E_ACCOUNTS)
    assert second_count == first_count
    assert len(employees) == len(E2E_ACCOUNTS)
    assert super_admin is not None
    assert super_admin.role == "SUPER_ADMIN"


def test_e2e_accounts_are_hidden_from_regular_employee_views(client: TestClient) -> None:
    session_factory = client.app.state.testing_session_factory
    passwords = {spec["id"]: "test-password" for spec in E2E_ACCOUNTS}
    auth_users = {spec["email"]: f"auth-{spec['id']}" for spec in E2E_ACCOUNTS}
    with session_factory() as session:
        sync_e2e_auth_accounts(session, auth_users, passwords, lambda _user_id, _password: None)
        session.commit()

    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-ms0001", role="SUPER_ADMIN", auth_user_id="auth-admin"
    )
    employee_page = client.get("/api/v1/employees", params={"page_size": 100})
    employee_options = client.get("/api/v1/employee-options")

    assert employee_page.status_code == 200
    assert employee_options.status_code == 200
    assert all(not item["id"].startswith("emp-e2e-") for item in employee_page.json()["items"])
    assert all(not item["id"].startswith("emp-e2e-") for item in employee_options.json())


def test_e2e_accounts_remain_visible_to_e2e_login(client: TestClient) -> None:
    session_factory = client.app.state.testing_session_factory
    passwords = {spec["id"]: "test-password" for spec in E2E_ACCOUNTS}
    auth_users = {spec["email"]: f"auth-{spec['id']}" for spec in E2E_ACCOUNTS}
    with session_factory() as session:
        sync_e2e_auth_accounts(session, auth_users, passwords, lambda _user_id, _password: None)
        session.commit()

    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-e2e-super-admin",
        role="SUPER_ADMIN",
        auth_user_id="auth-emp-e2e-super-admin",
    )
    employee_page = client.get("/api/v1/employees", params={"page_size": 100})
    employee_options = client.get("/api/v1/employee-options")
    expected_ids = {spec["id"] for spec in E2E_ACCOUNTS}

    assert expected_ids <= {item["id"] for item in employee_page.json()["items"]}
    assert expected_ids <= {item["id"] for item in employee_options.json()}
