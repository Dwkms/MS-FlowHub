from datetime import UTC, date, datetime, time

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.organization import Department, Employee, Team
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.employee import (
    AttendanceStatusUpdate,
    EmployeeCreate,
    EmployeeDetail,
    EmployeeUpdate,
    EmploymentStatusReasonUpdate,
    PaginatedEmployeeResponse,
)

_DAILY_WORK_STATUSES = {
    "WORKING",
    "REMOTE_WORK",
    "OUT_OF_OFFICE",
    "BUSINESS_TRIP",
    "ANNUAL_LEAVE",
    "MORNING_HALF",
    "AFTERNOON_HALF",
    "SICK_LEAVE",
    "TRAINING",
    "OFF_WORK",
    "ABSENT",
}
_REASON_REQUIRED_WORK_STATUSES = {"SICK_LEAVE", "ABSENT"}
_CHECK_IN_WORK_STATUSES = {"WORKING", "REMOTE_WORK", "OUT_OF_OFFICE", "BUSINESS_TRIP"}
_NORMAL_WORK_STATUSES = {"WORKING", "OFF_WORK"}
_PRIVATE_REASON_VIEWER_ROLES = {"ADMIN", "HR_MANAGER"}


class EmployeeService:
    def __init__(self, session: Session, repository: OrganizationRepository) -> None:
        self.session = session
        self.repository = repository

    def list(self, **filters: object) -> PaginatedEmployeeResponse:
        return self.repository.list_employee_page(**filters)

    def detail(self, employee_id: str, viewer_id: str | None = None) -> EmployeeDetail:
        item = self.repository.get_employee_detail(employee_id)
        if item is None:
            raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.")
        if not self._can_view_private_status_reasons(viewer_id):
            item = item.model_copy(
                update={
                    "employment_status_reason": self._without_private_note(
                        item.employment_status_reason
                    ),
                    "daily_work_reason": self._without_private_note(item.daily_work_reason),
                }
            )
        return item

    def create(self, payload: EmployeeCreate) -> EmployeeDetail:
        self._validate_refs(payload.department_id, payload.team_id, payload.manager_id)
        employee = Employee(
            id=f"emp-{payload.employee_no.lower()}",
            role="EMPLOYEE",
            is_active=payload.employment_status == "ACTIVE",
            **payload.model_dump(),
        )
        self.session.add(employee)
        self._commit()
        return self.detail(employee.id)

    def update(self, employee_id: str, payload: EmployeeUpdate) -> EmployeeDetail:
        employee = self.session.get(Employee, employee_id)
        if employee is None:
            raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.")
        values = payload.model_dump(exclude_unset=True)
        self._validate_refs(
            values.get("department_id", employee.department_id),
            values.get("team_id", employee.team_id),
            values.get("manager_id", employee.manager_id),
            employee_id,
        )
        for field, value in values.items():
            setattr(employee, field, value)
        if "employment_status" in values:
            employee.is_active = values["employment_status"] == "ACTIVE"
        self._commit()
        return self.detail(employee_id)

    def deactivate(self, employee_id: str) -> None:
        employee = self.session.get(Employee, employee_id)
        if employee is None:
            raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.")
        if employee.manager_id is None:
            raise HTTPException(status_code=409, detail="최상위 직원은 비활성화할 수 없습니다.")
        has_reports = self.session.scalar(
            select(Employee.id).where(
                Employee.manager_id == employee_id, Employee.employment_status == "ACTIVE"
            )
        )
        if has_reports:
            raise HTTPException(status_code=409, detail="하위 직원의 관리자를 먼저 변경해 주세요.")
        employee.employment_status, employee.is_active = "INACTIVE", False
        self._commit()

    def update_attendance_status(
        self, employee_id: str, actor_id: str, payload: AttendanceStatusUpdate
    ) -> EmployeeDetail:
        employee = self._require_employee(employee_id)
        self._require_self_or_admin(actor_id, employee)
        if employee.employment_status != "ACTIVE":
            raise HTTPException(
                status_code=409, detail="재직 중인 직원만 근무 상태를 변경할 수 있습니다."
            )
        if payload.work_status not in _DAILY_WORK_STATUSES:
            raise HTTPException(status_code=422, detail="지원하지 않는 근무 상태입니다.")
        reason_summary = self._clean_text(payload.reason_summary)
        private_note = self._clean_text(payload.private_note)
        reason_category = self._clean_text(payload.reason_category)
        if payload.work_status in _REASON_REQUIRED_WORK_STATUSES and not reason_summary:
            raise HTTPException(
                status_code=422, detail="병가와 결근에는 공개 사유를 입력해야 합니다."
            )
        work_date = payload.work_date or date.today()
        record = self.repository.get_attendance_record(employee.id, work_date)
        if record is None:
            record = self.repository.create_attendance_record(
                employee.id, work_date, payload.work_status
            )
        else:
            record.work_status = payload.work_status
        if payload.work_status in _NORMAL_WORK_STATUSES:
            record.note = None
            record.reason_category = None
            record.reason_summary = None
            record.private_note = None
            record.reason_registered_by_id = None
            record.reason_registered_at = None
        else:
            record.note = reason_summary
            record.reason_category = reason_category
            record.reason_summary = reason_summary
            record.private_note = private_note
            if reason_summary or private_note:
                record.reason_registered_by_id = actor_id
                record.reason_registered_at = datetime.now(UTC)
            else:
                record.reason_registered_by_id = None
                record.reason_registered_at = None
        if payload.work_status in _CHECK_IN_WORK_STATUSES:
            record.check_in_at = datetime.combine(work_date, time(9, 0), tzinfo=UTC)
            record.check_out_at = None
        elif payload.work_status == "OFF_WORK":
            record.check_in_at = record.check_in_at or datetime.combine(
                work_date, time(9, 0), tzinfo=UTC
            )
            record.check_out_at = datetime.combine(work_date, time(18, 0), tzinfo=UTC)
        else:
            record.check_in_at = None
            record.check_out_at = None
        self._commit()
        return self.detail(employee_id, actor_id)

    def update_employment_status_reason(
        self, employee_id: str, actor_id: str, payload: EmploymentStatusReasonUpdate
    ) -> EmployeeDetail:
        employee = self._require_employee(employee_id)
        self._require_self_or_admin(actor_id, employee)
        if employee.employment_status != "ON_LEAVE":
            raise HTTPException(
                status_code=409, detail="휴직 상태에서만 휴직 사유를 작성할 수 있습니다."
            )
        employee.employment_status_reason = payload.reason_summary.strip()
        employee.employment_status_reason_category = self._clean_text(payload.reason_category)
        employee.employment_status_reason_summary = payload.reason_summary.strip()
        employee.employment_status_private_note = self._clean_text(payload.private_note)
        employee.employment_status_reason_registered_by_id = actor_id
        employee.employment_status_reason_registered_at = datetime.now(UTC)
        employee.employment_status_effective_from = payload.effective_from or date.today()
        self._commit()
        return self.detail(employee_id, actor_id)

    def _require_employee(self, employee_id: str) -> Employee:
        employee = self.repository.get_employee_model(employee_id)
        if employee is None:
            raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.")
        return employee

    def _require_self_or_admin(self, actor_id: str, employee: Employee) -> None:
        actor = self._require_employee(actor_id)
        if actor.id != employee.id and actor.role != "ADMIN":
            raise HTTPException(
                status_code=403, detail="본인 또는 관리자만 상태 사유를 변경할 수 있습니다."
            )

    def _can_view_private_status_reasons(self, viewer_id: str | None) -> bool:
        viewer = self.repository.get_employee_model(viewer_id) if viewer_id else None
        return bool(viewer and viewer.role in _PRIVATE_REASON_VIEWER_ROLES)

    @staticmethod
    def _clean_text(value: str | None) -> str | None:
        return value.strip() if value and value.strip() else None

    @staticmethod
    def _without_private_note(item):
        return item.model_copy(update={"private_note": None}) if item else None

    def _validate_refs(
        self,
        department_id: str,
        team_id: str | None,
        manager_id: str | None,
        employee_id: str | None = None,
    ) -> None:
        if self.session.get(Department, department_id) is None:
            raise HTTPException(status_code=422, detail="유효하지 않은 부서입니다.")
        if team_id:
            team = self.session.get(Team, team_id)
            if team is None or team.department_id != department_id:
                raise HTTPException(status_code=422, detail="부서에 속하지 않는 팀입니다.")
        if manager_id:
            if manager_id == employee_id or self.session.get(Employee, manager_id) is None:
                raise HTTPException(status_code=422, detail="유효하지 않은 관리자입니다.")

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="중복된 사번 또는 이메일입니다."
            ) from error
