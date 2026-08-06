import logging
from collections.abc import Sequence
from datetime import UTC, date, datetime, time

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.employee_status import (
    CHECK_IN_WORK_STATUSES,
    DAILY_WORK_STATUSES,
    NORMAL_WORK_STATUSES,
    requires_employment_reason,
    requires_reason,
    supports_daily_work_status,
)
from app.models.auth import EmployeeAccount
from app.models.organization import Department, Employee, Team
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.employee import (
    AttendanceChangeHistoryItem,
    AttendanceStatusUpdate,
    EmployeeCreate,
    EmployeeDetail,
    EmployeeRoleUpdate,
    EmployeeUpdate,
    EmploymentStatusReasonUpdate,
    PaginatedEmployeeResponse,
)
from app.security.authorization import can_view_private_status_reasons
from app.security.identity import ActorContext
from app.security.permissions import HR_ADMIN, SUPER_ADMIN, TEAM_ADMIN

logger = logging.getLogger(__name__)


class EmployeeService:
    def __init__(self, session: Session, repository: OrganizationRepository) -> None:
        self.session = session
        self.repository = repository

    def list(self, actor: ActorContext, **filters: object) -> PaginatedEmployeeResponse:
        if actor.role not in {SUPER_ADMIN, HR_ADMIN, "ADMIN", "HR_MANAGER"}:
            if actor.role == TEAM_ADMIN:
                team_id = self._require_employee(actor.employee_id).team_id
                if team_id is None:
                    raise HTTPException(
                        status_code=403, detail="팀 관리자에게 연결된 팀이 없습니다."
                    )
                filters["visible_team_id"] = team_id
            else:
                filters["visible_employee_id"] = actor.employee_id
        return self.repository.list_employee_page(**filters)

    def organization_tree(self):
        return self.repository.organization_tree()

    def detail(self, employee_id: str, viewer: ActorContext | None = None) -> EmployeeDetail:
        item = self.repository.get_employee_detail(employee_id)
        if item is None:
            raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.")
        if viewer is not None and viewer.role not in {SUPER_ADMIN, HR_ADMIN, "ADMIN", "HR_MANAGER"}:
            if viewer.role == TEAM_ADMIN:
                viewer_employee = self._require_employee(viewer.employee_id)
                if viewer_employee.team_id is None or viewer_employee.team_id != item.team_id:
                    raise HTTPException(
                        status_code=403, detail="다른 팀 직원 조회 권한이 없습니다."
                    )
            elif viewer.employee_id != item.id:
                raise HTTPException(status_code=403, detail="본인 정보만 조회할 수 있습니다.")
        if not can_view_private_status_reasons(viewer):
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

    def update_role(
        self, employee_id: str, payload: EmployeeRoleUpdate, actor: ActorContext
    ) -> EmployeeDetail:
        employee = self._require_employee(employee_id)
        account = self.session.scalar(
            select(EmployeeAccount).where(EmployeeAccount.employee_id == employee.id)
        )
        if account is None:
            raise HTTPException(status_code=404, detail="연결된 Auth 계정을 찾을 수 없습니다.")
        previous_role = account.role
        account.role = payload.role
        self.session.commit()
        logger.info(
            "employee role changed actor_employee_id=%s target_employee_id=%s "
            "from_role=%s to_role=%s",
            actor.employee_id,
            employee.id,
            previous_role,
            payload.role,
        )
        return self.detail(employee.id)

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
        self, employee_id: str, actor: ActorContext, payload: AttendanceStatusUpdate
    ) -> EmployeeDetail:
        employee = self._require_employee(employee_id)
        self._require_status_update_permission(actor, employee)
        if not supports_daily_work_status(employee.employment_status):
            raise HTTPException(
                status_code=409, detail="재직 중인 직원만 근무 상태를 변경할 수 있습니다."
            )
        if payload.work_status not in DAILY_WORK_STATUSES:
            raise HTTPException(status_code=422, detail="지원하지 않는 근무 상태입니다.")
        reason_summary = self._clean_text(payload.reason_summary)
        private_note = self._clean_text(payload.private_note)
        reason_category = self._clean_text(payload.reason_category)
        if requires_reason(payload.work_status) and not reason_summary:
            raise HTTPException(
                status_code=422, detail="병가와 결근에는 공개 사유를 입력해야 합니다."
            )
        work_date = payload.work_date or date.today()
        record = self.repository.get_attendance_record(employee.id, work_date)
        before_values = (
            record.work_status if record else None,
            record.reason_category if record else None,
            record.reason_summary if record else None,
            record.private_note if record else None,
        )
        if record is None:
            record = self.repository.create_attendance_record(
                employee.id, work_date, payload.work_status
            )
        else:
            record.work_status = payload.work_status
        if payload.work_status in NORMAL_WORK_STATUSES:
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
                record.reason_registered_by_id = actor.employee_id
                record.reason_registered_at = datetime.now(UTC)
            else:
                record.reason_registered_by_id = None
                record.reason_registered_at = None
        if payload.work_status in CHECK_IN_WORK_STATUSES:
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
        after_values = (
            record.work_status,
            record.reason_category,
            record.reason_summary,
            record.private_note,
        )
        if before_values != after_values:
            # A newly created attendance record must exist before its audit row is inserted.
            # The ORM models intentionally have no relationship collection, so flush ordering
            # cannot be inferred from the two pending objects alone.
            self.session.flush([record])
            self.repository.create_attendance_change_history(
                record,
                before_work_status=before_values[0],
                before_reason_category=before_values[1],
                before_reason_summary=before_values[2],
                before_private_note=before_values[3],
                changed_by_id=actor.employee_id,
            )
        self._commit()
        return self.detail(employee_id, actor)

    def attendance_change_history(
        self, employee_id: str, actor: ActorContext, work_date: date | None = None
    ) -> Sequence[AttendanceChangeHistoryItem]:
        self.detail(employee_id, actor)
        items = self.repository.list_attendance_change_history(
            employee_id, work_date or date.today()
        )
        if can_view_private_status_reasons(actor):
            return items
        return [
            item.model_copy(update={"before_private_note": None, "after_private_note": None})
            for item in items
        ]

    def update_employment_status_reason(
        self, employee_id: str, actor: ActorContext, payload: EmploymentStatusReasonUpdate
    ) -> EmployeeDetail:
        employee = self._require_employee(employee_id)
        self._require_status_update_permission(actor, employee)
        if not requires_employment_reason(employee.employment_status):
            raise HTTPException(
                status_code=409, detail="휴직 상태에서만 휴직 사유를 작성할 수 있습니다."
            )
        employee.employment_status_reason = payload.reason_summary.strip()
        employee.employment_status_reason_category = self._clean_text(payload.reason_category)
        employee.employment_status_reason_summary = payload.reason_summary.strip()
        employee.employment_status_private_note = self._clean_text(payload.private_note)
        employee.employment_status_reason_registered_by_id = actor.employee_id
        employee.employment_status_reason_registered_at = datetime.now(UTC)
        employee.employment_status_effective_from = payload.effective_from or date.today()
        self._commit()
        return self.detail(employee_id, actor)

    def _require_employee(self, employee_id: str) -> Employee:
        employee = self.repository.get_employee_model(employee_id)
        if employee is None:
            raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.")
        return employee

    def _require_status_update_permission(self, actor: ActorContext, employee: Employee) -> None:
        if actor.employee_id == employee.id or actor.role in {SUPER_ADMIN, HR_ADMIN, "ADMIN"}:
            return
        if actor.role == TEAM_ADMIN:
            actor_employee = self._require_employee(actor.employee_id)
            if actor_employee.team_id and actor_employee.team_id == employee.team_id:
                return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인, 같은 팀 관리자 또는 권한 있는 관리자만 상태를 변경할 수 있습니다.",
        )

    def _can_view_private_status_reasons(self, viewer_id: str | None) -> bool:
        viewer = self.repository.get_employee_model(viewer_id) if viewer_id else None
        return bool(
            viewer
            and can_view_private_status_reasons(
                ActorContext(employee_id=viewer.id, role=viewer.role)
            )
        )

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
