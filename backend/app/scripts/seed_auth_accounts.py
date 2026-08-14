"""Create development Supabase Auth users and link them to employee accounts."""

import json
import os
from collections.abc import Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.auth import EmployeeAccount
from app.models.organization import Employee

# 직책과 역할을 1:1로 맞춘다. 팀장은 부서 전체(TEAM_ADMIN), 파트장은 자기 파트만
# (PART_ADMIN) 관리한다. 범위 판정은 app/domain/org_scope.py에 있다.
ROLE_BY_EMPLOYEE_NO = {
    "MS0001": "SUPER_ADMIN",  # 김민성 대표이사
    "MS0025": "HR_ADMIN",  # 이현정 인사팀장
    # 팀장 — 소속 부서 전체
    "MS0002": "TEAM_ADMIN",  # 박준혁 개발팀장
    "MS0015": "TEAM_ADMIN",  # 강수아 마케팅팀장
    "MS0035": "TEAM_ADMIN",  # 박서준 기획팀장
    "MS0045": "TEAM_ADMIN",  # 김태윤 CS팀장
    # 파트장 — 자기 파트만
    "MS0003": "PART_ADMIN",  # 이서진 SW파트장
    "MS0008": "PART_ADMIN",  # 김도윤 HW파트장
    "MS0012": "PART_ADMIN",  # 최다은 QA파트장
}


def _admin_request(
    path: str,
    payload: dict[str, object] | None = None,
    *,
    method: str | None = None,
) -> dict[str, object]:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SECRET_KEY must be configured.")
    request = Request(
        f"{settings.supabase_url.rstrip('/')}{path}",
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers={
            "apikey": settings.supabase_secret_key,
            "Authorization": f"Bearer {settings.supabase_secret_key}",
            "Content-Type": "application/json",
        },
        method=method or ("POST" if payload is not None else "GET"),
    )
    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError("Supabase Auth account creation failed.") from error


def _existing_auth_users() -> dict[str, str]:
    payload = _admin_request("/auth/v1/admin/users?page=1&per_page=1000")
    users = payload.get("users", [])
    return {
        item["email"]: item["id"]
        for item in users
        if isinstance(item, dict)
        and isinstance(item.get("email"), str)
        and isinstance(item.get("id"), str)
    }


def _create_auth_user(email: str, password: str) -> str:
    result = _admin_request(
        "/auth/v1/admin/users",
        {"email": email, "password": password, "email_confirm": True},
    )
    auth_user_id = result.get("id")
    if not isinstance(auth_user_id, str):
        raise RuntimeError("Supabase Auth did not return a user ID.")
    return auth_user_id


def _update_auth_user_password(auth_user_id: str, password: str) -> None:
    _admin_request(
        f"/auth/v1/admin/users/{auth_user_id}",
        {"password": password},
        method="PUT",
    )


def sync_employee_accounts(
    session: Session,
    auth_users: dict[str, str],
    password: str,
    create_auth_user: Callable[[str, str], str] = _create_auth_user,
) -> None:
    """Create missing Auth links and update existing account roles without duplicates."""
    employees = session.scalars(select(Employee).order_by(Employee.employee_no)).all()
    accounts_by_employee_id = {
        account.employee_id: account for account in session.scalars(select(EmployeeAccount)).all()
    }
    for employee in employees:
        auth_user_id = auth_users.get(employee.email)
        if auth_user_id is None:
            auth_user_id = create_auth_user(employee.email, password)
            auth_users[employee.email] = auth_user_id

        role = ROLE_BY_EMPLOYEE_NO.get(employee.employee_no, "EMPLOYEE")
        account = accounts_by_employee_id.get(employee.id)
        if account is None:
            account = EmployeeAccount(
                id=f"account-{employee.id}",
                auth_user_id=auth_user_id,
                employee_id=employee.id,
                role=role,
                is_active=employee.employment_status == "ACTIVE",
            )
            session.add(account)
            accounts_by_employee_id[employee.id] = account
            continue

        account.auth_user_id = auth_user_id
        account.role = role
        account.is_active = employee.employment_status == "ACTIVE"


def sync_selected_employee_accounts(
    session: Session,
    employee_nos: set[str],
    auth_users: dict[str, str],
    password: str,
    create_auth_user: Callable[[str, str], str] = _create_auth_user,
) -> None:
    """Create or update links only for explicitly selected employees.

    Existing Auth user passwords are never changed. This is safe for adding a
    small group to an environment that already has active employee accounts.
    """
    employees = session.scalars(
        select(Employee)
        .where(Employee.employee_no.in_(employee_nos))
        .order_by(Employee.employee_no)
    ).all()
    found_employee_nos = {employee.employee_no for employee in employees}
    missing_employee_nos = employee_nos - found_employee_nos
    if missing_employee_nos:
        raise RuntimeError(f"Employees not found: {', '.join(sorted(missing_employee_nos))}")

    employee_ids = [employee.id for employee in employees]
    accounts_by_employee_id = {
        account.employee_id: account
        for account in session.scalars(
            select(EmployeeAccount).where(EmployeeAccount.employee_id.in_(employee_ids))
        ).all()
    }
    accounts_by_auth_user_id = {
        account.auth_user_id: account for account in session.scalars(select(EmployeeAccount)).all()
    }
    for employee in employees:
        auth_user_id = auth_users.get(employee.email)
        if auth_user_id is None:
            auth_user_id = create_auth_user(employee.email, password)
            auth_users[employee.email] = auth_user_id

        linked_account = accounts_by_auth_user_id.get(auth_user_id)
        if linked_account is not None and linked_account.employee_id != employee.id:
            raise RuntimeError("The Auth user is already linked to another employee.")

        role = ROLE_BY_EMPLOYEE_NO.get(employee.employee_no, "EMPLOYEE")
        account = accounts_by_employee_id.get(employee.id)
        if account is None:
            session.add(
                EmployeeAccount(
                    id=f"account-{employee.id}",
                    auth_user_id=auth_user_id,
                    employee_id=employee.id,
                    role=role,
                    is_active=employee.employment_status == "ACTIVE",
                )
            )
            continue

        account.auth_user_id = auth_user_id
        account.role = role
        account.is_active = employee.employment_status == "ACTIVE"


def main() -> None:
    if os.getenv("APP_ENV", "development") == "production":
        raise RuntimeError("Auth seed is blocked in production.")
    settings = get_settings()
    password = settings.auth_seed_default_password
    if not password:
        raise RuntimeError("AUTH_SEED_DEFAULT_PASSWORD must be configured.")
    with SessionLocal() as session:
        sync_employee_accounts(session, _existing_auth_users(), password)
        session.commit()


if __name__ == "__main__":
    main()
