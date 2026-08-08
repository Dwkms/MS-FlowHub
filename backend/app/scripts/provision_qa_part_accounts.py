"""Provision the three QA part employee accounts without touching other users."""

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.scripts.seed_auth_accounts import _existing_auth_users, sync_selected_employee_accounts

MANAGED_EMPLOYEE_NOS = {"MS0012", "MS0013", "MS0014"}


def main() -> None:
    settings = get_settings()
    password = settings.auth_seed_default_password
    if not password:
        raise RuntimeError("AUTH_SEED_DEFAULT_PASSWORD must be configured.")
    with SessionLocal() as session:
        try:
            sync_selected_employee_accounts(
                session,
                MANAGED_EMPLOYEE_NOS,
                _existing_auth_users(),
                password,
            )
            session.commit()
        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    main()
