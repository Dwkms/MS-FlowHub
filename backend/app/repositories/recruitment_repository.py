from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.domain.recruitment_options import describe_experience
from app.models.organization import Department, Employee
from app.models.recruitment import Applicant, ApplicantStageHistory, JobPosting, RecruitmentRequest
from app.schemas.common import DashboardBreakdownItem, DashboardTask
from app.schemas.recruitment import (
    ApplicantResponse,
    ApplicantStageHistoryResponse,
    JobPostingResponse,
    RecruitmentRequestResponse,
)


class RecruitmentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_request(self, **values: object) -> RecruitmentRequest:
        request = RecruitmentRequest(id=str(uuid4()), status="DRAFT", **values)
        self.session.add(request)
        self.session.flush()
        return request

    def get_request(self, request_id: str) -> RecruitmentRequest | None:
        return self.session.get(RecruitmentRequest, request_id)

    def delete_request(self, request: RecruitmentRequest) -> None:
        self.session.delete(request)

    def delete_posting(self, posting: JobPosting) -> None:
        self.session.delete(posting)

    def get_request_by_approval(self, approval_document_id: str) -> RecruitmentRequest | None:
        return self.session.scalar(
            select(RecruitmentRequest).where(
                RecruitmentRequest.approval_document_id == approval_document_id
            )
        )

    def list_requests(self, employee_id: str | None) -> list[RecruitmentRequest]:
        statement = select(RecruitmentRequest).order_by(RecruitmentRequest.created_at.desc())
        if employee_id:
            statement = statement.where(
                or_(
                    RecruitmentRequest.requester_id == employee_id,
                    RecruitmentRequest.approver_id == employee_id,
                )
            )
        return list(self.session.scalars(statement))

    def get_posting_by_request(self, request_id: str) -> JobPosting | None:
        return self.session.scalar(
            select(JobPosting).where(JobPosting.recruitment_request_id == request_id)
        )

    def create_posting(
        self, *, request: RecruitmentRequest, title: str, content: str
    ) -> JobPosting:
        posting = JobPosting(
            id=str(uuid4()),
            recruitment_request_id=request.id,
            title=title,
            content=content,
            status="DRAFT",
        )
        self.session.add(posting)
        self.session.flush()
        return posting

    def list_postings(self) -> list[JobPosting]:
        statement = select(JobPosting).order_by(JobPosting.created_at.desc())
        return list(self.session.scalars(statement))

    def get_posting(self, posting_id: str) -> JobPosting | None:
        return self.session.get(JobPosting, posting_id)

    def get_request_for_posting(self, posting_id: str) -> RecruitmentRequest | None:
        statement = (
            select(RecruitmentRequest)
            .join(JobPosting, JobPosting.recruitment_request_id == RecruitmentRequest.id)
            .where(JobPosting.id == posting_id)
        )
        return self.session.scalar(statement)

    def create_applicant(self, **values: object) -> Applicant:
        applicant = Applicant(id=str(uuid4()), stage="APPLIED", **values)
        self.session.add(applicant)
        self.session.flush()
        return applicant

    def get_applicant(self, applicant_id: str) -> Applicant | None:
        return self.session.get(Applicant, applicant_id)

    def delete_applicant(self, applicant: Applicant) -> None:
        self.session.delete(applicant)

    def list_applicants(
        self,
        *,
        job_posting_id: str | None,
        stage: str | None,
        search: str | None,
        department_id: str | None,
    ) -> list[Applicant]:
        statement = (
            select(Applicant)
            .join(JobPosting, JobPosting.id == Applicant.job_posting_id)
            .join(RecruitmentRequest, RecruitmentRequest.id == JobPosting.recruitment_request_id)
            .order_by(Applicant.updated_at.desc(), Applicant.created_at.desc())
        )
        if job_posting_id:
            statement = statement.where(Applicant.job_posting_id == job_posting_id)
        if stage:
            statement = statement.where(Applicant.stage == stage)
        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                or_(Applicant.name.ilike(pattern), Applicant.email.ilike(pattern))
            )
        if department_id:
            statement = statement.where(RecruitmentRequest.request_department_id == department_id)
        return list(self.session.scalars(statement))

    def list_stage_histories(self, applicant_id: str) -> list[ApplicantStageHistory]:
        statement = (
            select(ApplicantStageHistory)
            .where(ApplicantStageHistory.applicant_id == applicant_id)
            .order_by(ApplicantStageHistory.created_at.desc())
        )
        return list(self.session.scalars(statement))

    def create_stage_history(self, **values: object) -> ApplicantStageHistory:
        history = ApplicantStageHistory(
            id=str(uuid4()),
            created_at=datetime.now(UTC),
            **values,
        )
        self.session.add(history)
        self.session.flush()
        return history

    def count_postings(self) -> int:
        statement = select(func.count()).select_from(JobPosting)
        return self.session.scalar(statement) or 0

    def get_applicant_stage_breakdown(self) -> list[DashboardBreakdownItem]:
        statement = (
            select(Applicant.stage, func.count())
            .group_by(Applicant.stage)
            .order_by(Applicant.stage)
        )
        return [
            DashboardBreakdownItem(label=stage, value=count)
            for stage, count in self.session.execute(statement)
        ]

    def count_recruitment_requests(self) -> int:
        statement = select(func.count()).select_from(RecruitmentRequest)
        return self.session.scalar(statement) or 0

    def list_recent_tasks(self, employee_id: str, limit: int = 2) -> list[DashboardTask]:
        statement = (
            select(RecruitmentRequest, Employee)
            .join(Employee, Employee.id == RecruitmentRequest.requester_id)
            .where(
                or_(
                    RecruitmentRequest.requester_id == employee_id,
                    RecruitmentRequest.approver_id == employee_id,
                )
            )
            .order_by(RecruitmentRequest.updated_at.desc())
            .limit(limit)
        )
        labels = {
            "DRAFT": "임시 저장",
            "PENDING_APPROVAL": "결재 대기",
            "APPROVED": "승인",
            "REJECTED": "반려",
            "POSTING_CREATED": "공고 생성",
        }
        return [
            DashboardTask(
                id=request.id,
                category="채용 요청",
                title=f"{request.position_title} 채용 요청",
                status=labels[request.status],
                owner=requester.name,
                href=f"/recruitment-requests/{request.id}",
            )
            for request, requester in self.session.execute(statement)
        ]

    def to_request_response(self, request: RecruitmentRequest) -> RecruitmentRequestResponse:
        department = self.session.get(Department, request.request_department_id)
        requester = self.session.get(Employee, request.requester_id)
        approver = self.session.get(Employee, request.approver_id)
        posting = self.get_posting_by_request(request.id)
        return RecruitmentRequestResponse(
            id=request.id,
            request_department_id=request.request_department_id,
            request_department_name=department.name,
            requester_id=request.requester_id,
            requester_name=requester.name,
            approver_id=request.approver_id,
            approver_name=approver.name,
            position_title=request.position_title,
            headcount=request.headcount,
            employment_type=request.employment_type,
            experience_level=request.experience_level,
            experience_years_min=request.experience_years_min,
            experience_label=describe_experience(
                request.experience_level, request.experience_years_min
            ),
            education_level=request.education_level,
            work_location=request.work_location,
            salary=request.salary,
            application_deadline=request.application_deadline,
            apply_method=request.apply_method,
            reason=request.reason,
            responsibilities=request.responsibilities,
            required_skills=request.required_skills,
            preferred_skills=request.preferred_skills,
            desired_start_date=request.desired_start_date,
            poster_original_name=request.poster_original_name,
            poster_content_type=request.poster_content_type,
            poster_size=request.poster_size,
            status=request.status,
            approval_document_id=request.approval_document_id,
            job_posting_id=posting.id if posting else None,
            created_at=request.created_at,
            updated_at=request.updated_at,
        )

    def to_posting_response(self, posting: JobPosting) -> JobPostingResponse:
        request = self.get_request(posting.recruitment_request_id)
        department = self.session.get(Department, request.request_department_id)
        requester = self.session.get(Employee, request.requester_id)
        return JobPostingResponse(
            id=posting.id,
            recruitment_request_id=posting.recruitment_request_id,
            request_department_name=department.name,
            requester_name=requester.name,
            title=posting.title,
            content=posting.content,
            headcount=request.headcount,
            employment_type=request.employment_type,
            experience_level=request.experience_level,
            experience_label=describe_experience(
                request.experience_level, request.experience_years_min
            ),
            education_level=request.education_level,
            work_location=request.work_location,
            salary=request.salary,
            application_deadline=request.application_deadline,
            apply_method=request.apply_method,
            responsibilities=request.responsibilities,
            required_skills=request.required_skills,
            preferred_skills=request.preferred_skills,
            desired_start_date=request.desired_start_date,
            poster_original_name=request.poster_original_name,
            poster_content_type=request.poster_content_type,
            poster_size=request.poster_size,
            status=posting.status,
            created_at=posting.created_at,
            updated_at=posting.updated_at,
        )

    def to_applicant_response(
        self, applicant: Applicant, *, include_histories: bool = False
    ) -> ApplicantResponse:
        posting = self.get_posting(applicant.job_posting_id)
        if posting is None:
            raise RuntimeError("지원자가 연결된 채용공고를 찾을 수 없습니다.")
        request = self.get_request(posting.recruitment_request_id)
        if request is None:
            raise RuntimeError("채용공고가 연결된 채용 요청을 찾을 수 없습니다.")
        department = self.session.get(Department, request.request_department_id)
        creator = self.session.get(Employee, applicant.created_by_id)
        histories = self.list_stage_histories(applicant.id) if include_histories else []
        return ApplicantResponse(
            id=applicant.id,
            job_posting_id=posting.id,
            job_posting_title=posting.title,
            request_department_id=request.request_department_id,
            request_department_name=department.name,
            name=applicant.name,
            email=applicant.email,
            phone=applicant.phone,
            career_summary=applicant.career_summary,
            stage=applicant.stage,
            created_by_id=applicant.created_by_id,
            created_by_name=creator.name,
            created_at=applicant.created_at,
            updated_at=applicant.updated_at,
            stage_histories=[self.to_stage_history_response(item) for item in histories],
        )

    def to_stage_history_response(
        self, history: ApplicantStageHistory
    ) -> ApplicantStageHistoryResponse:
        actor = self.session.get(Employee, history.actor_id)
        return ApplicantStageHistoryResponse(
            id=history.id,
            from_stage=history.from_stage,
            to_stage=history.to_stage,
            note=history.note,
            actor_id=history.actor_id,
            actor_name=actor.name,
            created_at=history.created_at,
        )
