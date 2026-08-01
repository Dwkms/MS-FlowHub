from pydantic import BaseModel


class AuthMeResponse(BaseModel):
    auth_user_id: str
    employee_id: str
    employee_no: str
    name: str
    email: str
    department: str
    position: str
    role: str
    permissions: list[str]
