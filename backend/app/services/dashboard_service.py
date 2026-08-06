from fastapi import HTTPException, status

from app.core.config import Settings
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.recruitment_repository import RecruitmentRepository
from app.schemas.common import (
    DashboardMetric,
    DashboardResponse,
    DepartmentResponse,
    EmployeeResponse,
)

_MODULE_ACCESS = {
    "EMPLOYEE": ["전자결재", "직원 매뉴얼"],
    "TEAM_ADMIN": ["전자결재", "ATS Lite", "직원·조직 관리", "직원 매뉴얼"],
    "HR_ADMIN": ["전자결재", "ATS Lite", "직원·조직 관리", "직원 매뉴얼"],
    "SUPER_ADMIN": ["전자결재", "ATS Lite", "직원·조직 관리", "직원 매뉴얼"],
}


class DashboardService:
    def __init__(
        self,
        organization_repository: OrganizationRepository,
        approval_repository: ApprovalRepository,
        recruitment_repository: RecruitmentRepository,
        settings: Settings,
    ) -> None:
        self.organization = organization_repository
        self.approvals = approval_repository
        self.recruitment = recruitment_repository
        self.settings = settings

    def list_departments(self) -> list[DepartmentResponse]:
        return self.organization.list_departments()

    def list_employees(self) -> list[EmployeeResponse]:
        return self.organization.list_employees()

    def get_dashboard(self, employee_id: str, role: str) -> DashboardResponse:
        employee = self.organization.get_employee(employee_id)
        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="선택한 직원을 찾을 수 없습니다.",
            )

        return DashboardResponse(
            source=self.settings.data_source,
            current_employee=employee,
            accessible_modules=_MODULE_ACCESS.get(role, []),
            metrics=[
                DashboardMetric(
                    label="내 결재 대기",
                    value=self.approvals.count_pending_for_approver(employee_id),
                    helper="오늘 확인할 문서",
                    tone="navy",
                ),
                DashboardMetric(
                    label="내가 상신한 결재",
                    value=self.approvals.count_pending_for_author(employee_id),
                    helper="처리를 기다리는 문서",
                    tone="blue",
                ),
                DashboardMetric(
                    label="진행 중 채용",
                    value=self.recruitment.count_postings(),
                    helper="승인 후 생성된 채용공고",
                    tone="amber",
                ),
            ],
            recent_tasks=[
                *self.approvals.list_recent_tasks(employee_id, limit=3),
                *self.recruitment.list_recent_tasks(employee_id, limit=2),
            ][:5],
        )
