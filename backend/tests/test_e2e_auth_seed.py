from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.models.auth import EmployeeAccount
from app.models.organization import Employee
from app.scripts.seed_e2e_auth_accounts import E2E_ACCOUNTS, sync_e2e_auth_accounts


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
