"""Create idempotent, test-only Supabase Auth accounts for Playwright E2E."""

import os
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.auth import EmployeeAccount
from app.models.organization import Department, Employee
from app.scripts.seed_auth_accounts import (
    _create_auth_user,
    _existing_auth_users,
    _update_auth_user_password,
)

E2E_ACCOUNTS = (
    {
        "id": "emp-e2e-employee",
        "employee_no": "E2E0001",
        "name": "E2E 일반직원",
        "email": "e2e-employee@msflowhub.test",
        "employee_role": "EMPLOYEE",
        "account_role": "EMPLOYEE",
        "password_setting": "e2e_auth_employee_password",
    },
    {
        "id": "emp-e2e-super-admin",
        "employee_no": "E2E0002",
        "name": "E2E 최고관리자",
        "email": "e2e-super-admin@msflowhub.test",
        "employee_role": "ADMIN",
        "account_role": "SUPER_ADMIN",
        "position": "대표",
        "password_setting": "e2e_auth_super_admin_password",
    },
)


def sync_e2e_auth_accounts(
    session: Session,
    auth_users: dict[str, str],
    passwords: dict[str, str],
    update_auth_user_password: Callable[[str, str], None] = _update_auth_user_password,
) -> None:
    """Create or update only the dedicated E2E employees and Auth links."""
    department = session.scalar(select(Department).order_by(Department.display_order).limit(1))
    if department is None:
        raise RuntimeError("Run the organization seed before creating E2E Auth accounts.")

    for spec in E2E_ACCOUNTS:
        employee = session.get(Employee, spec["id"])
        if employee is None:
            employee = Employee(
                id=spec["id"],
                employee_no=spec["employee_no"],
                name=spec["name"],
                email=spec["email"],
                role=spec["employee_role"],
                department_id=department.id,
                position=spec.get("position", "E2E 테스트"),
                job_title="Playwright 자동화 테스트",
            )
            session.add(employee)
            session.flush()
        else:
            employee.name = spec["name"]
            employee.email = spec["email"]
            employee.role = spec["employee_role"]
            employee.department_id = department.id
            employee.team_id = None
            employee.position = spec.get("position", "E2E 테스트")
            employee.is_active = True
            employee.employment_status = "ACTIVE"

        auth_user_id = auth_users.get(spec["email"])
        if auth_user_id is None:
            auth_user_id = _create_auth_user(spec["email"], passwords[spec["id"]])
            auth_users[spec["email"]] = auth_user_id
        else:
            update_auth_user_password(auth_user_id, passwords[spec["id"]])

        account = session.scalar(
            select(EmployeeAccount).where(EmployeeAccount.employee_id == employee.id)
        )
        if account is None:
            account = EmployeeAccount(
                id=f"account-{employee.id}",
                auth_user_id=auth_user_id,
                employee_id=employee.id,
                role=spec["account_role"],
                is_active=True,
            )
            session.add(account)
            continue
        account.auth_user_id = auth_user_id
        account.role = spec["account_role"]
        account.is_active = True


def main() -> None:
    if os.getenv("APP_ENV", "development") == "production":
        raise RuntimeError("E2E Auth seed is blocked in production.")
    settings = get_settings()
    employee_password = settings.e2e_auth_employee_password
    super_admin_password = settings.e2e_auth_super_admin_password
    if not employee_password or not super_admin_password:
        raise RuntimeError("E2E Auth seed passwords must be configured.")
    passwords = {
        "emp-e2e-employee": employee_password,
        "emp-e2e-super-admin": super_admin_password,
    }
    with SessionLocal() as session:
        sync_e2e_auth_accounts(session, _existing_auth_users(), passwords)
        session.commit()
    print("E2E Auth accounts synced.")


if __name__ == "__main__":
    main()
