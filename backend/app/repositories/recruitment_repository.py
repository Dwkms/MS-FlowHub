from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.organization import Department, Employee
from app.models.recruitment import JobPosting, RecruitmentRequest
from app.schemas.recruitment import JobPostingResponse, RecruitmentRequestResponse


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
