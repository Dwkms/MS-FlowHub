from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core import supabase_storage
from app.core.supabase_storage import POSTER_BUCKET, StorageObjectNotFoundError
from app.domain.recruitment_options import describe_experience
from app.domain.recruitment_policy import (
    is_recruitment_approver,
    is_requestable_recruitment_department,
)
from app.models.approval import ApprovalDocument
from app.models.recruitment import Applicant, JobPosting, RecruitmentRequest
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.recruitment_repository import RecruitmentRepository
from app.schemas.recruitment import (
    ApplicantCreate,
    ApplicantResponse,
    ApplicantStageUpdate,
    ApplicantUpdate,
    JobPostingResponse,
    JobPostingUpdate,
    RecruitmentRequestCreate,
    RecruitmentRequestResponse,
    RecruitmentSubmit,
)
from app.security.identity import ActorContext

_FULL_ACCESS_ROLES = {"SUPER_ADMIN", "HR_ADMIN", "ADMIN", "HR_MANAGER"}
_POSTER_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
_POSTER_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
_MAX_POSTER_SIZE = 5 * 1024 * 1024
_ATS_WRITE_ROLES = {"SUPER_ADMIN", "HR_ADMIN", "ADMIN", "HR_MANAGER"}
_ATS_VIEW_ROLES = _ATS_WRITE_ROLES | {"TEAM_ADMIN"}
_TERMINAL_APPLICANT_STAGES = {"HIRED", "REJECTED"}


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
        is_super_admin_self_approver = approver.id == requester.id and actor.role in {
            "SUPER_ADMIN",
            "ADMIN",
        }
        if not is_recruitment_approver(approver.position) and not is_super_admin_self_approver:
            raise HTTPException(
                status_code=422, detail="채용 요청 결재자는 팀장급 이상만 지정할 수 있습니다."
            )
        if approver.id == requester.id and not is_super_admin_self_approver:
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
        previous_stored_name = request.poster_stored_name
        supabase_storage.upload_object(POSTER_BUCKET, stored_name, content, poster.content_type)
        try:
            request.poster_original_name = original_name
            request.poster_stored_name = stored_name
            request.poster_content_type = poster.content_type
            request.poster_size = len(content)
            self.session.commit()
            self.session.refresh(request)
        except Exception:
            self.session.rollback()
            supabase_storage.delete_object(POSTER_BUCKET, stored_name)
            raise
        if previous_stored_name:
            supabase_storage.delete_object(POSTER_BUCKET, previous_stored_name)
        return self.recruitment.to_request_response(request)

    def get_poster_file(self, request_id: str, actor: ActorContext) -> tuple[bytes, str, str]:
        request = self._get_request(request_id)
        self._require_view_permission(request, actor)
        if not request.poster_stored_name or not request.poster_original_name:
            raise HTTPException(status_code=404, detail="첨부된 채용 포스터가 없습니다.")
        try:
            content = supabase_storage.download_object(POSTER_BUCKET, request.poster_stored_name)
        except StorageObjectNotFoundError as error:
            raise HTTPException(status_code=404, detail="첨부 파일을 찾을 수 없습니다.") from error
        return (
            content,
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
            supabase_storage.delete_object(POSTER_BUCKET, poster_stored_name)

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

    def update_posting(
        self, posting_id: str, payload: JobPostingUpdate, actor: ActorContext
    ) -> JobPostingResponse:
        """공고 제목·본문을 수정한다.

        승인 시 자동 생성된 공고를 이후에 손볼 방법이 없었다. AI 초안을 공고에 반영하려면
        수정 경로가 필요해서 신설했지만, AI 전용이 아니라 원래 비어 있던 기능이다.

        `status`는 받지 않는다. 공고 게시 여부는 사람이 판단할 사항이고, 이 경로가
        AI 흐름에서도 호출되기 때문이다.
        """
        if actor.role not in _FULL_ACCESS_ROLES:
            raise HTTPException(
                status_code=403, detail="인사 담당자 또는 관리자만 채용공고를 수정할 수 있습니다."
            )
        posting = self._get_posting(posting_id)
        if payload.title is not None:
            posting.title = payload.title
        if payload.content is not None:
            posting.content = payload.content
        self.session.commit()
        self.session.refresh(posting)
        return self.recruitment.to_posting_response(posting)

    def list_postings(self, actor: ActorContext) -> list[JobPostingResponse]:
        return [
            self.recruitment.to_posting_response(item) for item in self.recruitment.list_postings()
        ]

    def list_applicants(
        self,
        *,
        job_posting_id: str | None,
        stage: str | None,
        search: str | None,
        actor: ActorContext,
    ) -> list[ApplicantResponse]:
        department_id = self._get_ats_department_scope(actor)
        items = self.recruitment.list_applicants(
            job_posting_id=job_posting_id,
            stage=stage,
            search=search,
            department_id=department_id,
        )
        return [self.recruitment.to_applicant_response(item) for item in items]

    def create_applicant(
        self, posting_id: str, payload: ApplicantCreate, actor: ActorContext
    ) -> ApplicantResponse:
        self._require_ats_write_permission(actor)
        self._get_posting(posting_id)
        normalized_email = payload.email.lower()
        existing = self.recruitment.list_applicants(
            job_posting_id=posting_id,
            stage=None,
            search=normalized_email,
            department_id=None,
        )
        if any(item.email == normalized_email for item in existing):
            raise HTTPException(status_code=409, detail="같은 채용공고에 등록된 이메일입니다.")
        applicant = self.recruitment.create_applicant(
            job_posting_id=posting_id,
            name=payload.name,
            email=normalized_email,
            phone=payload.phone,
            career_summary=payload.career_summary,
            created_by_id=actor.employee_id,
        )
        self.recruitment.create_stage_history(
            applicant_id=applicant.id,
            from_stage=None,
            to_stage="APPLIED",
            note="지원자 등록",
            actor_id=actor.employee_id,
        )
        self.session.commit()
        self.session.refresh(applicant)
        return self.recruitment.to_applicant_response(applicant, include_histories=True)

    def get_applicant(self, applicant_id: str, actor: ActorContext) -> ApplicantResponse:
        applicant = self._get_applicant(applicant_id)
        self._require_ats_view_permission(applicant, actor)
        return self.recruitment.to_applicant_response(applicant, include_histories=True)

    def update_applicant(
        self, applicant_id: str, payload: ApplicantUpdate, actor: ActorContext
    ) -> ApplicantResponse:
        self._require_ats_write_permission(actor)
        applicant = self._get_applicant(applicant_id)
        values = payload.model_dump(exclude_unset=True)
        if "email" in values and values["email"] is not None:
            values["email"] = values["email"].lower()
            existing = self.recruitment.list_applicants(
                job_posting_id=applicant.job_posting_id,
                stage=None,
                search=values["email"],
                department_id=None,
            )
            if any(item.id != applicant.id and item.email == values["email"] for item in existing):
                raise HTTPException(status_code=409, detail="같은 채용공고에 등록된 이메일입니다.")
        for key, value in values.items():
            setattr(applicant, key, value)
        self.session.commit()
        self.session.refresh(applicant)
        return self.recruitment.to_applicant_response(applicant, include_histories=True)

    def change_applicant_stage(
        self, applicant_id: str, payload: ApplicantStageUpdate, actor: ActorContext
    ) -> ApplicantResponse:
        self._require_ats_write_permission(actor)
        applicant = self._get_applicant(applicant_id)
        if applicant.stage in _TERMINAL_APPLICANT_STAGES:
            raise HTTPException(
                status_code=409, detail="종료된 지원자는 단계를 변경할 수 없습니다."
            )
        if applicant.stage == payload.stage:
            raise HTTPException(
                status_code=409, detail="현재 단계와 같은 단계로 변경할 수 없습니다."
            )
        if payload.stage == "REJECTED" and not payload.note:
            raise HTTPException(
                status_code=422,
                detail="불합격 처리에는 사유 메모가 필요합니다.",
            )
        before_stage = applicant.stage
        applicant.stage = payload.stage
        self.recruitment.create_stage_history(
            applicant_id=applicant.id,
            from_stage=before_stage,
            to_stage=payload.stage,
            note=payload.note,
            actor_id=actor.employee_id,
        )
        self.session.commit()
        self.session.refresh(applicant)
        return self.recruitment.to_applicant_response(applicant, include_histories=True)

    def delete_applicant(self, applicant_id: str, actor: ActorContext) -> None:
        self._require_ats_write_permission(actor)
        applicant = self._get_applicant(applicant_id)
        self.recruitment.delete_applicant(applicant)
        self.session.commit()

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
        # 채용 요청에 없으면 줄 자체를 넣지 않는다. "근무지: 미정"은 공고에서 안 쓴 것만 못하다.
        summary = [
            f"모집 인원: {request.headcount}명",
            f"고용 형태: {request.employment_type}",
            f"경력: {describe_experience(request.experience_level, request.experience_years_min)}",
        ]
        optional_lines = (
            ("학력", request.education_level),
            ("근무지", request.work_location),
            ("급여", request.salary),
            (
                "모집 마감",
                request.application_deadline.isoformat() if request.application_deadline else None,
            ),
            ("지원 방법", request.apply_method),
        )
        summary.extend(f"{label}: {value}" for label, value in optional_lines if value)
        return "\n\n".join(
            [
                f"모집 부문: {request.position_title}",
                "\n".join(summary),
            ]
        )

    def _get_request(self, request_id: str) -> RecruitmentRequest:
        request = self.recruitment.get_request(request_id)
        if request is None:
            raise HTTPException(status_code=404, detail="채용 요청을 찾을 수 없습니다.")
        return request

    def _get_posting(self, posting_id: str) -> JobPosting:
        posting = self.recruitment.get_posting(posting_id)
        if posting is None:
            raise HTTPException(status_code=404, detail="채용공고를 찾을 수 없습니다.")
        return posting

    def _get_applicant(self, applicant_id: str) -> Applicant:
        applicant = self.recruitment.get_applicant(applicant_id)
        if applicant is None:
            raise HTTPException(status_code=404, detail="지원자를 찾을 수 없습니다.")
        return applicant

    def _get_ats_department_scope(self, actor: ActorContext) -> str | None:
        if actor.role in _ATS_WRITE_ROLES:
            return None
        if actor.role != "TEAM_ADMIN":
            raise HTTPException(status_code=403, detail="지원자 정보를 조회할 권한이 없습니다.")
        employee = self.organization.get_employee_model(actor.employee_id)
        if employee is None:
            raise HTTPException(status_code=403, detail="직원 정보를 찾을 수 없습니다.")
        return employee.department_id

    def _require_ats_view_permission(self, applicant: Applicant, actor: ActorContext) -> None:
        department_id = self._get_ats_department_scope(actor)
        if department_id is None:
            return
        request = self.recruitment.get_request_for_posting(applicant.job_posting_id)
        if request is None or request.request_department_id != department_id:
            raise HTTPException(status_code=403, detail="해당 지원자를 조회할 권한이 없습니다.")

    @staticmethod
    def _require_ats_write_permission(actor: ActorContext) -> None:
        if actor.role not in _ATS_WRITE_ROLES:
            raise HTTPException(
                status_code=403,
                detail="인사 담당자 또는 관리자만 지원자를 수정할 수 있습니다.",
            )

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
