from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import AuthMeResponse


class AuthService:
    def __init__(self, session: Session, repository: AuthRepository) -> None:
        self.session = session
        self.repository = repository

    def current_user(self, auth_user_id: str) -> AuthMeResponse:
        row = self.repository.get_account_with_employee(auth_user_id)
        if row is None:
            raise HTTPException(status_code=403, detail="직원 계정 연결이 필요합니다.")
        account, employee = row
        if not account.is_active or not employee.is_active:
            raise HTTPException(status_code=403, detail="비활성화된 계정입니다.")
        account.last_login_at = datetime.now(UTC)
        self.session.commit()
        return AuthMeResponse(
            auth_user_id=account.auth_user_id,
            employee_id=employee.id,
            employee_no=employee.employee_no,
            name=employee.name,
            email=employee.email,
            department=employee.department_id,
            position=employee.position,
            role=account.role,
            permissions=[],
        )
