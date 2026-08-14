"""대시보드 지표 집계.

두 종류를 만듭니다.
- **개인 지표**: 로그인한 사람 기준. 내 결재 대기, 내가 상신한 결재, 진행 중 채용
- **관리자 분석**: 전사 기준. 결재 상태 분포, 평균 처리시간, 지원자 단계 분포 등

관리자 분석은 `_ANALYTICS_ROLES`에 든 역할에게만 내려갑니다. 전사 결재 처리시간을
사원이 볼 이유가 없기 때문입니다.

**E2E 테스트 계정은 집계에서 뺍니다.** 테스트가 만든 직원이 섞이면 인원수와 지표가 틀립니다.

`_MODULE_ACCESS`는 역할별로 화면에 표시할 메뉴 목록입니다. 화면 표시용이고
실제 접근 차단은 각 API의 의존성과 Service가 다시 합니다.
"""

from fastapi import HTTPException, status

from app.core.config import Settings
from app.domain.test_accounts import E2E_EMPLOYEE_ID_PREFIX, is_e2e_employee
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.recruitment_repository import RecruitmentRepository
from app.schemas.common import (
    DashboardAnalytics,
    DashboardMetric,
    DashboardResponse,
    DepartmentResponse,
    EmployeeResponse,
)
from app.security.identity import ActorContext

_MODULE_ACCESS = {
    "EMPLOYEE": ["전자결재", "직원 매뉴얼"],
    "TEAM_ADMIN": ["전자결재", "ATS Lite", "직원·조직 관리", "직원 매뉴얼"],
    # 파트장은 지원자(ATS) 정보를 다루지 않는다. 채용은 팀장·인사 소관이다.
    "PART_ADMIN": ["전자결재", "직원·조직 관리", "직원 매뉴얼"],
    "HR_ADMIN": ["전자결재", "ATS Lite", "직원·조직 관리", "직원 매뉴얼"],
    "SUPER_ADMIN": ["전자결재", "ATS Lite", "직원·조직 관리", "직원 매뉴얼"],
}
_ANALYTICS_ROLES = {"SUPER_ADMIN", "HR_ADMIN"}


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

    def list_employees(self, actor: ActorContext) -> list[EmployeeResponse]:
        return self.organization.list_employees(
            exclude_employee_id_prefix=(
                None if is_e2e_employee(actor.employee_id) else E2E_EMPLOYEE_ID_PREFIX
            )
        )

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
            analytics=self._get_analytics() if role in _ANALYTICS_ROLES else None,
        )

    def _get_analytics(self) -> DashboardAnalytics:
        return DashboardAnalytics(
            approval_by_status=self.approvals.get_status_breakdown(),
            average_approval_processing_hours=self.approvals.get_average_processing_hours(),
            applicant_by_stage=self.recruitment.get_applicant_stage_breakdown(),
            recruitment_request_count=self.recruitment.count_recruitment_requests(),
            attendance_by_status=self.organization.get_today_attendance_breakdown(),
            today_attendance_unregistered_count=self.organization.count_today_attendance_unregistered(),
        )
