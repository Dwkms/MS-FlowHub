from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EmployeeCreate(BaseModel):
    employee_no: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    department_id: str
    team_id: str | None = None
    position: str = Field(min_length=1, max_length=50)
    job_title: str = Field(min_length=1, max_length=200)
    job_description: str | None = None
    manager_id: str | None = None
    employment_type: str = "REGULAR"
    employment_status: str = "ACTIVE"
    hire_date: date | None = None
    phone_extension: str | None = None
    work_location: str = "서울 본사"
    profile_image_url: str | None = None


class EmployeeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    department_id: str | None = None
    team_id: str | None = None
    position: str | None = Field(default=None, min_length=1, max_length=50)
    job_title: str | None = Field(default=None, min_length=1, max_length=200)
    job_description: str | None = None
    manager_id: str | None = None
    employment_type: str | None = None
    employment_status: str | None = None
    employment_status_reason: str | None = Field(default=None, max_length=500)
    hire_date: date | None = None
    phone_extension: str | None = None
    work_location: str | None = None
    profile_image_url: str | None = None


class EmployeeRoleUpdate(BaseModel):
    role: Literal["SUPER_ADMIN", "HR_ADMIN", "TEAM_ADMIN", "EMPLOYEE"]


class EmployeeManagerSummary(BaseModel):
    id: str
    employee_no: str
    name: str
    position: str


class EmployeeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    employee_no: str
    name: str
    email: str
    department: str
    department_code: str
    team: str | None
    team_code: str | None
    position: str
    job_title: str
    manager: EmployeeManagerSummary | None
    employment_status: str
    daily_work_status: str | None
    check_in_at: datetime | None
    check_out_at: datetime | None
    work_location: str


class EmployeeDetail(EmployeeSummary):
    role: str
    team_id: str | None
    department_id: str
    job_description: str | None
    employment_type: str
    hire_date: date | None
    phone_extension: str | None
    profile_image_url: str | None
    employment_status_reason: "StatusReasonDetail | None"
    daily_work_reason: "StatusReasonDetail | None"


class StatusReasonDetail(BaseModel):
    reason_category: str | None
    reason_summary: str | None
    private_note: str | None
    period_start: date
    period_end: date | None
    registered_by_name: str | None
    registered_at: datetime | None


class AttendanceChangeHistoryItem(BaseModel):
    id: str
    work_date: date
    before_work_status: str | None
    after_work_status: str
    before_reason_category: str | None
    after_reason_category: str | None
    before_reason_summary: str | None
    after_reason_summary: str | None
    before_private_note: str | None
    after_private_note: str | None
    changed_by_name: str | None
    changed_at: datetime


class AttendanceStatusUpdate(BaseModel):
    work_status: str = Field(min_length=1, max_length=30)
    reason_category: str | None = Field(default=None, max_length=30)
    reason_summary: str | None = Field(default=None, max_length=200)
    private_note: str | None = Field(default=None, max_length=500)
    work_date: date | None = None


class EmploymentStatusReasonUpdate(BaseModel):
    reason_category: str | None = Field(default=None, max_length=30)
    reason_summary: str = Field(min_length=1, max_length=200)
    private_note: str | None = Field(default=None, max_length=500)
    effective_from: date | None = None


class DepartmentResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str | None


class OrganizationNode(BaseModel):
    id: str
    employee_no: str
    name: str
    position: str
    department: str
    children: list["OrganizationNode"] = []


class PaginatedEmployeeResponse(BaseModel):
    items: list[EmployeeSummary]
    page: int
    page_size: int
    total: int
    total_pages: int
