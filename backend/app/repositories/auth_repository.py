from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.auth import EmployeeAccount
from app.models.organization import Employee


class AuthRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_account_with_employee(
        self, auth_user_id: str
    ) -> tuple[EmployeeAccount, Employee] | None:
        return self.session.execute(
            select(EmployeeAccount, Employee)
            .join(Employee, EmployeeAccount.employee_id == Employee.id)
            .where(EmployeeAccount.auth_user_id == auth_user_id)
        ).one_or_none()
