from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.upload_storage import get_poster_path
from app.domain.recruitment_policy import (
    is_recruitment_approver,
    is_requestable_recruitment_department,
)
from app.models.approval import ApprovalDocument
from app.models.recruitment import JobPosting, RecruitmentRequest
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.recruitment_repository import RecruitmentRepository
from app.schemas.recruitment import (
    JobPostingResponse,
    RecruitmentRequestCreate,
    RecruitmentRequestResponse,
    RecruitmentSubmit,
)
from app.security.identity import ActorContext

_FULL_ACCESS_ROLES = {"SUPER_ADMIN", "HR_ADMIN", "ADMIN", "HR_MANAGER"}
_POSTER_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
_POSTER_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
_MAX_POSTER_SIZE = 5 * 1024 * 1024


class RecruitmentService:
    def __init__(
        self,
        *,
        session: Session,
        recruitment_repository: RecruitmentRepository,
        approval_repository: ApprovalRepository,
        organization_repository: OrganizationRepository,
        notification_repository: NotificationRepository,
    ) -> None:
        self.session = session
        self.recruitment = recruitment_repository
        self.approvals = approval_repository
        self.organization = organization_repository
        self.notifications = notification_repository

    def list_requests(self, actor: ActorContext) -> list[RecruitmentRequestResponse]:
        visible_employee_id = None if actor.role in _FULL_ACCESS_ROLES else actor.employee_id
        return [
            self.recruitment.to_request_response(item)
            for item in self.recruitment.list_requests(visible_employee_id)
        ]

    def get_request(self, request_id: str, actor: ActorContext) -> RecruitmentRequestResponse:
        request = self._get_request(request_id)
        if actor.role not in _FULL_ACCESS_ROLES and actor.employee_id not in {
            request.requester_id,
            request.approver_id,
        }:
            raise HTTPException(status_code=403, detail="채용 요청을 조회할 권한이 없습니다.")
        return self.recruitment.to_request_response(request)

    def create_request(
        self, payload: RecruitmentRequestCreate, actor: ActorContext
    ) -> RecruitmentRequestResponse:
        requester = self._require_employee(actor.employee_id)
        if self.organization.get_department(payload.request_department_id) is None:
            raise HTTPException(status_code=400, detail="기안 부서를 찾을 수 없습니다.")
        approver = self._require_employee(payload.approver_id)
        department = self.organization.get_department_model(payload.request_department_id)
        if department and not is_requestable_recruitment_department(department.code):
            raise HTTPException(
                status_code=422, detail="경영진 부서는 채용 요청 부서로 선택할 수 없습니다."
            )
        if not is_recruitment_approver(approver.position):
            raise HTTPException(
                status_code=422, detail="채용 요청 결재자는 팀장급 이상만 지정할 수 있습니다."
            )
        if approver.id == requester.id:
            raise HTTPException(status_code=400, detail="요청자와 결재자는 같을 수 없습니다.")

        request = self.recruitment.create_request(
            **payload.model_dump(), requester_id=actor.employee_id
        )
        self.session.commit()
        self.session.refresh(request)
        return self.recruitment.to_request_response(request)

    async def upload_poster(
        self, request_id: str, actor: ActorContext, poster: UploadFile
    ) -> RecruitmentRequestResponse:
        request = self._get_request(request_id)
        if actor.role not in {"SUPER_ADMIN", "ADMIN"} and actor.employee_id != request.requester_id:
            raise HTTPException(
                status_code=403, detail="요청 작성자 또는 관리자만 포스터를 첨부할 수 있습니다."
            )
        self._require_status(
            request, "DRAFT", "임시 저장 상태의 채용 요청에만 포스터를 첨부할 수 있습니다."
        )

        original_name = Path(poster.filename or "").name
        suffix = Path(original_name).suffix.lower()
        if poster.content_type not in _POSTER_CONTENT_TYPES or suffix not in _POSTER_SUFFIXES:
            raise HTTPException(
                status_code=400,
                detail="채용 포스터는 JPG, PNG, WEBP 또는 PDF 파일만 첨부할 수 있습니다.",
            )
        content = await poster.read(_MAX_POSTER_SIZE + 1)
        if not content:
            raise HTTPException(status_code=400, detail="비어 있는 파일은 첨부할 수 없습니다.")
        if len(content) > _MAX_POSTER_SIZE:
            raise HTTPException(
                status_code=400, detail="채용 포스터는 5MB 이하만 첨부할 수 있습니다."
            )

        stored_name = f"{uuid4()}{suffix}"
        destination = get_poster_path(stored_name)
        previous_stored_name = request.poster_stored_name
        try:
            destination.write_bytes(content)
            request.poster_original_name = original_name
            request.poster_stored_name = stored_name
            request.poster_content_type = poster.content_type
            request.poster_size = len(content)
            self.session.commit()
            self.session.refresh(request)
        except Exception:
            self.session.rollback()
            destination.unlink(missing_ok=True)
            raise
        if previous_stored_name:
            get_poster_path(previous_stored_name).unlink(missing_ok=True)
        return self.recruitment.to_request_response(request)

    def get_poster_file(self, request_id: str, actor: ActorContext) -> tuple[Path, str, str]:
        request = self._get_request(request_id)
        self._require_view_permission(request, actor)
        if not request.poster_stored_name or not request.poster_original_name:
            raise HTTPException(status_code=404, detail="첨부된 채용 포스터가 없습니다.")
        path = get_poster_path(request.poster_stored_name)
        if not path.is_file():
            raise HTTPException(status_code=404, detail="첨부 파일을 찾을 수 없습니다.")
        return (
            path,
            request.poster_original_name,
            request.poster_content_type or "application/octet-stream",
        )

    def delete_request(self, request_id: str, actor: ActorContext) -> None:
        if actor.role not in {"SUPER_ADMIN", "ADMIN"}:
            raise HTTPException(status_code=403, detail="관리자만 채용 요청을 삭제할 수 있습니다.")

        request = self._get_request(request_id)
        approval_document_id = request.approval_document_id
        poster_stored_name = request.poster_stored_name
        posting = self.recruitment.get_posting_by_request(request.id)

        self.notifications.delete_related(
            related_type="RECRUITMENT_REQUEST",
            related_id=request.id,
        )
        if posting is not None:
            self.notifications.delete_related(related_type="JOB_POSTING", related_id=posting.id)
            self.recruitment.delete_posting(posting)
        self.recruitment.delete_request(request)
        self.session.flush()

        if approval_document_id is not None:
            self.notifications.delete_related(
                related_type="APPROVAL_DOCUMENT",
                related_id=approval_document_id,
            )
            document = self.approvals.get(approval_document_id)
            if document is not None:
                self.approvals.delete(document)
        self.session.commit()
        if poster_stored_name:
            get_poster_path(poster_stored_name).unlink(missing_ok=True)

    def submit_request(
        self, request_id: str, payload: RecruitmentSubmit, actor: ActorContext
    ) -> RecruitmentRequestResponse:
        request = self._get_request(request_id)
        self._require_status(request, "DRAFT", "임시 저장 상태의 채용 요청만 상신할 수 있습니다.")
        if actor.employee_id != request.requester_id:
            raise HTTPException(status_code=403, detail="요청자만 채용 요청을 상신할 수 있습니다.")

        document = self.approvals.create(
            document_type="RECRUITMENT_REQUEST",
            title=f"{request.position_title} 채용 요청",
            content=self._build_approval_content(request),
            department_id=request.request_department_id,
            author_id=request.requester_id,
            approver_id=request.approver_id,
            related_type="RECRUITMENT_REQUEST",
            related_id=request.id,
        )
        self.approvals.mark_submitted(document, actor.employee_id, payload.comment)
        request.approval_document_id = document.id
        request.status = "PENDING_APPROVAL"
        self.notifications.create(
            recipient_id=request.approver_id,
            message=f"{request.position_title} 채용 요청 결재가 도착했습니다.",
            related_type="APPROVAL_DOCUMENT",
            related_id=document.id,
        )
        self.session.commit()
        self.session.refresh(request)
        return self.recruitment.to_request_response(request)

    def process_approval(self, document: ApprovalDocument, target_status: str) -> None:
        if document.related_type != "RECRUITMENT_REQUEST":
            return
        request = self.recruitment.get_request_by_approval(document.id)
        if request is None:
            raise RuntimeError("채용 요청과 전자결재 문서 연결을 찾을 수 없습니다.")
        self._require_status(
            request, "PENDING_APPROVAL", "대기 중인 채용 요청만 처리할 수 있습니다."
        )

        if target_status == "APPROVED":
            request.status = "APPROVED"
            posting = self._create_posting(request)
            request.status = "POSTING_CREATED"
            approval_message = (
                f"{request.position_title} 채용 요청이 승인되어 채용공고 초안이 생성되었습니다."
            )
            self.notifications.create(
                recipient_id=request.requester_id,
                message=approval_message,
                related_type="JOB_POSTING",
                related_id=posting.id,
            )
            return

        if target_status == "REJECTED":
            request.status = "REJECTED"
            self.notifications.create(
                recipient_id=request.requester_id,
                message=f"{request.position_title} 채용 요청이 반려되었습니다.",
                related_type="RECRUITMENT_REQUEST",
                related_id=request.id,
            )
            return
        raise RuntimeError("지원하지 않는 채용 요청 결재 결과입니다.")

    def create_posting(self, request_id: str, actor: ActorContext) -> JobPostingResponse:
        if actor.role not in {"SUPER_ADMIN", "HR_ADMIN", "ADMIN", "HR_MANAGER"}:
            raise HTTPException(
                status_code=403, detail="인사 담당자 또는 관리자만 채용공고를 생성할 수 있습니다."
            )
        request = self._get_request(request_id)
        if self.recruitment.get_posting_by_request(request.id) is not None:
            raise HTTPException(status_code=409, detail="이미 생성된 채용공고가 있습니다.")
        self._require_status(request, "APPROVED", "승인된 채용 요청만 채용공고로 만들 수 있습니다.")
        posting = self._create_posting(request)
        request.status = "POSTING_CREATED"
        self.session.commit()
        self.session.refresh(posting)
        return self.recruitment.to_posting_response(posting)

    def list_postings(self, actor: ActorContext) -> list[JobPostingResponse]:
        return [
            self.recruitment.to_posting_response(item) for item in self.recruitment.list_postings()
        ]

    def _create_posting(self, request: RecruitmentRequest) -> JobPosting:
        if self.recruitment.get_posting_by_request(request.id) is not None:
            raise HTTPException(status_code=409, detail="이미 생성된 채용공고가 있습니다.")
        return self.recruitment.create_posting(
            request=request,
            title=request.position_title,
            content=self._build_posting_content(request),
        )

    @staticmethod
    def _build_approval_content(request: RecruitmentRequest) -> str:
        return f"채용 사유\n{request.reason}\n\n주요 업무\n{request.responsibilities}"

    @staticmethod
    def _build_posting_content(request: RecruitmentRequest) -> str:
        return "\n\n".join(
            [
                f"모집 부문: {request.position_title}",
                (
                    f"모집 인원: {request.headcount}명\n"
                    f"고용 형태: {request.employment_type}\n"
                    f"경력: {request.experience_level}"
                ),
                f"주요 업무\n{request.responsibilities}",
                f"필수 역량\n{request.required_skills or '채용 요청 내용을 바탕으로 협의 예정'}",
                f"우대 사항\n{request.preferred_skills or '없음'}",
            ]
        )

    def _get_request(self, request_id: str) -> RecruitmentRequest:
        request = self.recruitment.get_request(request_id)
        if request is None:
            raise HTTPException(status_code=404, detail="채용 요청을 찾을 수 없습니다.")
        return request

    def _require_employee(self, employee_id: str):
        employee = self.organization.get_employee(employee_id)
        if employee is None:
            raise HTTPException(status_code=400, detail="직원을 찾을 수 없습니다.")
        return employee

    @staticmethod
    def _require_view_permission(request: RecruitmentRequest, actor: ActorContext) -> None:
        if actor.role not in _FULL_ACCESS_ROLES and actor.employee_id not in {
            request.requester_id,
            request.approver_id,
        }:
            raise HTTPException(status_code=403, detail="채용 요청을 조회할 권한이 없습니다.")

    @staticmethod
    def _require_status(request: RecruitmentRequest, expected: str, message: str) -> None:
        if request.status != expected:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)
