from typing import Literal

from pydantic import BaseModel

Role = Literal[
    "EMPLOYEE",
    "DEPARTMENT_HEAD",
    "HR_MANAGER",
    "SALES_REP",
    "SALES_MANAGER",
    "ADMIN",
]


class DepartmentResponse(BaseModel):
    id: str
    code: str
    name: str


class EmployeeResponse(BaseModel):
    id: str
    employee_no: str
    name: str
    role: Role
    role_label: str
    position: str
    department_id: str
    department_name: str


class DashboardMetric(BaseModel):
    label: str
    value: int
    helper: str
    tone: Literal["navy", "blue", "amber", "green"]


class DashboardTask(BaseModel):
    id: str
    category: str
    title: str
    status: str
    owner: str
    href: str | None = None


class DashboardResponse(BaseModel):
    source: Literal["local", "supabase"]
    current_employee: EmployeeResponse
    accessible_modules: list[str]
    metrics: list[DashboardMetric]
    recent_tasks: list[DashboardTask]
