"""전자결재 업무 규칙.

이 프로젝트의 **핵심 엔진**입니다. 채용 요청도 이 엔진을 타고 승인됩니다.

Service가 하는 일과 하지 않는 일을 구분해 두면 코드를 읽기 쉽습니다.
- **한다**: 상태 전이 판정, 권한 판정, 트랜잭션 경계 잡기
- **안 한다**: HTTP 응답 만들기(Router 담당), SQL 쓰기(Repository 담당)

기억할 규칙 셋:

1. **작성자는 요청 본문에서 받지 않습니다.** 인증된 `ActorContext`에서 가져옵니다.
2. **작성자는 본인 문서를 승인할 수 없습니다.** 관리자가 채용 요청을 처리할 때만 예외입니다.
3. **결재 처리 권한은 세 갈래**입니다 — 지정된 결재자 본인, 관리자,
   그리고 관리 범위 안에 작성자가 들어오는 팀장·파트장.

상태 전이와 권한 규칙 전체는 docs/DOMAIN.md의 전자결재 절에 있습니다.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.org_scope import is_org_scoped_role, is_within_scope
from app.domain.recruitment_policy import is_recruitment_approver
from app.models.approval import ApprovalDocument
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.approval import (
    ApprovalAction,
    ApprovalCreate,
    ApprovalReject,
    ApprovalResponse,
    ApprovalSubmit,
    ApprovalUpdate,
)
from app.security.identity import ActorContext
from app.services.recruitment_service import RecruitmentService


class ApprovalService:
    def __init__(
        self,
        session: Session,
        approval_repository: ApprovalRepository,
        organization_repository: OrganizationRepository,
        recruitment_service: RecruitmentService,
    ) -> None:
        self.session = session
        self.approvals = approval_repository
        self.organization = organization_repository
        self.recruitment = recruitment_service

    def list(
        self, *, actor: ActorContext, search: str | None, status_filter: str | None
    ) -> list[ApprovalResponse]:
        selected_employee_id = None if actor.role in {"SUPER_ADMIN", "ADMIN"} else actor.employee_id
        return self.approvals.list_documents(
            employee_id=selected_employee_id,
            search=search,
            status=status_filter,
        )

    def get(self, document_id: str, actor: ActorContext) -> ApprovalResponse:
        document = self._get_document(document_id)
        self._require_view_permission(document, actor)
        return self.approvals.to_response(document)

    def create(self, payload: ApprovalCreate, actor: ActorContext) -> ApprovalResponse:
        author = self._require_employee(actor.employee_id)
        approver = self._require_employee(payload.approver_id)
        self._require_manager_level_approver(approver.position)
        if self.organization.get_department(payload.department_id) is None:
            raise HTTPException(status_code=400, detail="기안 부서를 찾을 수 없습니다.")
        if (
            actor.role not in {"SUPER_ADMIN", "ADMIN"}
            and author.department_id != payload.department_id
        ):
            raise HTTPException(
                status_code=400, detail="기안자의 소속 부서와 기안 부서가 다릅니다."
            )
        if author.id == approver.id:
            raise HTTPException(status_code=400, detail="작성자와 결재자는 같을 수 없습니다.")

        document = self.approvals.create(**payload.model_dump(), author_id=actor.employee_id)
        self.session.commit()
        self.session.refresh(document)
        return self.approvals.to_response(document)

    def update(
        self, document_id: str, payload: ApprovalUpdate, actor: ActorContext
    ) -> ApprovalResponse:
        document = self._get_document(document_id)
        self._require_status(document, "DRAFT", "임시 저장 문서만 수정할 수 있습니다.")
        if actor.employee_id != document.author_id:
            raise HTTPException(status_code=403, detail="작성자만 문서를 수정할 수 있습니다.")

        changes = payload.model_dump(exclude_none=True)
        if "department_id" in changes:
            if self.organization.get_department(changes["department_id"]) is None:
                raise HTTPException(status_code=400, detail="기안 부서를 찾을 수 없습니다.")
            if (
                actor.role not in {"SUPER_ADMIN", "ADMIN"}
                and self._require_employee(actor.employee_id).department_id
                != changes["department_id"]
            ):
                raise HTTPException(
                    status_code=400, detail="기안자의 소속 부서만 선택할 수 있습니다."
                )
        if "approver_id" in changes:
            approver = self._require_employee(changes["approver_id"])
            self._require_manager_level_approver(approver.position)
            if changes["approver_id"] == document.author_id:
                raise HTTPException(status_code=400, detail="작성자와 결재자는 같을 수 없습니다.")
        for field, value in changes.items():
            setattr(document, field, value)
        self.approvals.add_history(
            document=document,
            actor_id=actor.employee_id,
            action="UPDATED",
            from_status="DRAFT",
            to_status="DRAFT",
        )
        self.session.commit()
        self.session.refresh(document)
        return self.approvals.to_response(document)

    def delete(self, document_id: str, actor: ActorContext) -> None:
        document = self._get_document(document_id)
        if actor.role not in {"SUPER_ADMIN", "ADMIN"}:
            raise HTTPException(status_code=403, detail="관리자만 문서를 삭제할 수 있습니다.")

        if document.related_type == "RECRUITMENT_REQUEST" and document.related_id:
            self.recruitment.delete_request(document.related_id, actor)
            return

        self.approvals.delete(document)
        self.session.commit()

    def submit(
        self, document_id: str, actor: ActorContext, payload: ApprovalSubmit
    ) -> ApprovalResponse:
        document = self._get_document(document_id)
        self._require_status(document, "DRAFT", "임시 저장 문서만 상신할 수 있습니다.")
        if actor.employee_id != document.author_id:
            raise HTTPException(status_code=403, detail="작성자만 문서를 상신할 수 있습니다.")
        self.approvals.mark_submitted(document, actor.employee_id, payload.comment)
        self.session.commit()
        self.session.refresh(document)
        return self.approvals.to_response(document)

    def approve(
        self, document_id: str, actor: ActorContext, payload: ApprovalAction
    ) -> ApprovalResponse:
        document = self._get_document(document_id)
        self._require_decision_permission(document, actor)
        self.approvals.mark_processed(
            document,
            actor_id=actor.employee_id,
            target_status="APPROVED",
            action="APPROVED",
            comment=payload.comment,
        )
        self.recruitment.process_approval(document, "APPROVED")
        self.session.commit()
        self.session.refresh(document)
        return self.approvals.to_response(document)

    def reject(
        self, document_id: str, actor: ActorContext, payload: ApprovalReject
    ) -> ApprovalResponse:
        document = self._get_document(document_id)
        self._require_decision_permission(document, actor)
        self.approvals.mark_processed(
            document,
            actor_id=actor.employee_id,
            target_status="REJECTED",
            action="REJECTED",
            comment=payload.comment.strip(),
        )
        self.recruitment.process_approval(document, "REJECTED")
        self.session.commit()
        self.session.refresh(document)
        return self.approvals.to_response(document)

    def _get_document(self, document_id: str) -> ApprovalDocument:
        document = self.approvals.get(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="결재문서를 찾을 수 없습니다.")
        return document

    def _require_employee(self, employee_id: str):
        employee = self.organization.get_employee(employee_id)
        if employee is None:
            raise HTTPException(status_code=400, detail="직원을 찾을 수 없습니다.")
        return employee

    @staticmethod
    def _require_manager_level_approver(position: str) -> None:
        if not is_recruitment_approver(position):
            raise HTTPException(
                status_code=422, detail="결재자는 파트장급 이상만 지정할 수 있습니다."
            )

    @staticmethod
    def _require_status(document: ApprovalDocument, expected: str, message: str) -> None:
        if document.status != expected:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)

    def _require_view_permission(self, document: ApprovalDocument, actor: ActorContext) -> None:
        """`list`와 같은 범위를 상세 조회에도 적용합니다.

        목록은 관리자가 아니면 본인이 기안했거나 결재자로 지정된 문서만 돌려줍니다.
        상세만 열려 있으면 문서 ID를 아는 사람이 남의 결재문서를 그대로 읽을 수 있습니다.
        결재 처리와 마찬가지로 관리 범위 안 직원의 문서는 팀장·파트장도 볼 수 있습니다.
        """
        if actor.role in {"SUPER_ADMIN", "ADMIN"}:
            return
        if actor.employee_id in {document.author_id, document.approver_id}:
            return
        if is_org_scoped_role(actor.role) and self._is_within_manage_scope(
            actor.role, actor.employee_id, document.author_id
        ):
            return
        raise HTTPException(
            status_code=403, detail="본인 문서 또는 관리 범위의 문서만 조회할 수 있습니다."
        )

    def _require_decision_permission(self, document: ApprovalDocument, actor: ActorContext) -> None:
        self._require_status(document, "PENDING", "결재 대기 문서만 처리할 수 있습니다.")
        if actor.employee_id == document.author_id:
            if (
                actor.role in {"SUPER_ADMIN", "ADMIN"}
                and document.related_type == "RECRUITMENT_REQUEST"
            ):
                return
            raise HTTPException(
                status_code=403, detail="작성자는 본인 문서를 승인하거나 반려할 수 없습니다."
            )
        if actor.role in {"SUPER_ADMIN", "ADMIN"}:
            return
        if is_org_scoped_role(actor.role) and self._is_within_manage_scope(
            actor.role, actor.employee_id, document.author_id
        ):
            return
        if actor.employee_id != document.approver_id:
            raise HTTPException(
                status_code=403, detail="지정된 결재자 또는 관리자만 처리할 수 있습니다."
            )

    def _is_within_manage_scope(
        self, role: str, manager_employee_id: str, target_employee_id: str
    ) -> bool:
        manager = self.organization.get_employee_model(manager_employee_id)
        target = self.organization.get_employee_model(target_employee_id)
        if manager is None or target is None:
            return False
        return is_within_scope(role, manager, target)
