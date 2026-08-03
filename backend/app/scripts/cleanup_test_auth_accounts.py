"""Remove only the dedicated Auth and Playwright test accounts."""

import sys

from sqlalchemy import delete, or_, select

from app.db.session import SessionLocal
from app.models.approval import ApprovalDocument
from app.models.auth import EmployeeAccount
from app.models.organization import Employee
from app.scripts.seed_auth_accounts import _admin_request, _existing_auth_users

TEST_EMAILS = (
    "e2e-employee@msflowhub.test",
    "e2e-super-admin@msflowhub.test",
    "auth-test-inactive@msflowhub.test",
)
E2E_TEST_EMAILS = TEST_EMAILS[:2]


def cleanup_test_auth_accounts(
    target_emails: tuple[str, ...] = TEST_EMAILS,
) -> tuple[list[str], list[str]]:
    """Delete only known test employees and their related test Auth users."""
    with SessionLocal() as session:
        employees = session.scalars(select(Employee).where(Employee.email.in_(target_emails))).all()
        employee_ids = [employee.id for employee in employees]
        if employee_ids:
            session.execute(
                delete(ApprovalDocument).where(
                    or_(
                        ApprovalDocument.author_id.in_(employee_ids),
                        ApprovalDocument.approver_id.in_(employee_ids),
                    )
                )
            )
            session.execute(
                delete(EmployeeAccount).where(EmployeeAccount.employee_id.in_(employee_ids))
            )
            session.execute(delete(Employee).where(Employee.id.in_(employee_ids)))
            session.commit()

    deleted_auth_user_ids: list[str] = []
    auth_users_by_email = _existing_auth_users()
    for email in target_emails:
        auth_user_id = auth_users_by_email.get(email)
        if auth_user_id is None:
            continue
        _admin_request(f"/auth/v1/admin/users/{auth_user_id}", method="DELETE")
        deleted_auth_user_ids.append(auth_user_id)

    return [employee.email for employee in employees], deleted_auth_user_ids


def main() -> None:
    target_emails = E2E_TEST_EMAILS if "--e2e-only" in sys.argv else TEST_EMAILS
    emails, auth_user_ids = cleanup_test_auth_accounts(target_emails)
    print(f"Removed {len(emails)} test employees and {len(auth_user_ids)} Auth users.")


if __name__ == "__main__":
    main()
