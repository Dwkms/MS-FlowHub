"""Create development Supabase Auth users and link them to employee accounts."""

import json
import os
from datetime import UTC, datetime
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.auth import EmployeeAccount
from app.models.organization import Employee

ROLE_BY_EMPLOYEE_NO = {
    "MS0001": "SUPER_ADMIN",
    "MS0022": "HR_ADMIN",
    "MS0002": "TEAM_ADMIN",
    "MS0012": "TEAM_ADMIN",
    "MS0032": "TEAM_ADMIN",
    "MS0042": "TEAM_ADMIN",
}


def _admin_request(path: str, payload: dict[str, object] | None = None) -> dict[str, object]:
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
        method="POST" if payload is not None else "GET",
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
        if isinstance(item, dict) and isinstance(item.get("email"), str) and isinstance(item.get("id"), str)
    }


def main() -> None:
    if os.getenv("APP_ENV", "development") == "production":
        raise RuntimeError("Auth seed is blocked in production.")
    settings = get_settings()
    password = settings.auth_seed_default_password
    if not password:
        raise RuntimeError("AUTH_SEED_DEFAULT_PASSWORD must be configured.")
    with SessionLocal() as session:
        auth_users = _existing_auth_users()
        employees = session.scalars(select(Employee).order_by(Employee.employee_no)).all()
        for employee in employees:
            account = session.scalar(
                select(EmployeeAccount).where(EmployeeAccount.employee_id == employee.id)
            )
            if account is None:
                auth_user_id = auth_users.get(employee.email)
                if auth_user_id is None:
                    result = _admin_request(
                        "/auth/v1/admin/users",
                        {
                            "email": employee.email,
                            "password": password,
                            "email_confirm": True,
                        },
                    )
                    auth_user_id = result.get("id")
                if not isinstance(auth_user_id, str):
                    raise RuntimeError("Supabase Auth did not return a user ID.")
                account = EmployeeAccount(
                    id=f"account-{employee.id}",
                    auth_user_id=auth_user_id,
                    employee_id=employee.id,
                    role=ROLE_BY_EMPLOYEE_NO.get(employee.employee_no, "EMPLOYEE"),
                    is_active=employee.employment_status == "ACTIVE",
                    last_login_at=datetime.now(UTC),
                )
                session.add(account)
        session.commit()


if __name__ == "__main__":
    main()
