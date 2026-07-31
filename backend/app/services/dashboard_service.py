from fastapi import HTTPException, status

from app.core.config import Settings
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.common import (
    DashboardMetric,
    DashboardResponse,
    DashboardTask,
    DepartmentResponse,
    EmployeeResponse,
)

_MODULE_ACCESS = {
    "EMPLOYEE": ["전자결재"],
    "DEPARTMENT_HEAD": ["전자결재", "ATS Lite"],
    "HR_MANAGER": ["전자결재", "ATS Lite"],
    "SALES_REP": ["전자결재", "CRM Lite"],
    "SALES_MANAGER": ["전자결재", "CRM Lite"],
    "ADMIN": ["전자결재", "ATS Lite", "CRM Lite", "관리"],
}


class DashboardService:
    def __init__(
        self,
        organization_repository: OrganizationRepository,
        approval_repository: ApprovalRepository,
        settings: Settings,
    ) -> None:
        self.organization = organization_repository
        self.approvals = approval_repository
        self.settings = settings

    def list_departments(self) -> list[DepartmentResponse]:
        return self.organization.list_departments()

    def list_employees(self) -> list[EmployeeResponse]:
        return self.organization.list_employees()

    def get_dashboard(self, employee_id: str) -> DashboardResponse:
        employee = self.organization.get_employee(employee_id)
        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="선택한 직원을 찾을 수 없습니다.",
            )

        return DashboardResponse(
            source=self.settings.data_source,
            current_employee=employee,
            accessible_modules=_MODULE_ACCESS[employee.role],
            metrics=[
                DashboardMetric(
                    label="내 결재 대기",
                    value=self.approvals.count_pending_for_approver(employee_id),
                    helper="오늘 확인할 문서",
                    tone="navy",
                ),
                DashboardMetric(
                    label="진행 중 채용",
                    value=3,
                    helper="공고 2 · 지원자 4",
                    tone="blue",
                ),
                DashboardMetric(
                    label="승인 필요 견적",
                    value=1,
                    helper="할인 기준 초과",
                    tone="amber",
                ),
                DashboardMetric(
                    label="읽지 않은 알림",
                    value=4,
                    helper="최근 24시간",
                    tone="green",
                ),
            ],
            recent_tasks=[
                *self.approvals.list_recent_tasks(employee_id, limit=3),
                DashboardTask(
                    id="task-ats-001",
                    category="ATS Lite",
                    title="Backend 개발자 채용공고 초안",
                    status="작성 중",
                    owner="박지우",
                ),
                DashboardTask(
                    id="task-crm-001",
                    category="CRM Lite",
                    title="한빛상사 12% 할인 견적",
                    status="승인 필요",
                    owner="이도윤",
                ),
            ][:5],
        )
