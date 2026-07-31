from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.approval import ApprovalDocument
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.approval import (
    ApprovalAction,
    ApprovalCreate,
    ApprovalReject,
    ApprovalResponse,
    ApprovalUpdate,
)
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
        self, *, employee_id: str | None, search: str | None, status_filter: str | None
    ) -> list[ApprovalResponse]:
        selected_employee_id = employee_id
        if employee_id is not None:
            employee = self._require_employee(employee_id)
            if employee.role == "ADMIN":
                selected_employee_id = None
        return self.approvals.list_documents(
            employee_id=selected_employee_id,
            search=search,
            status=status_filter,
        )

    def get(self, document_id: str) -> ApprovalResponse:
        return self.approvals.to_response(self._get_document(document_id))

    def create(self, payload: ApprovalCreate) -> ApprovalResponse:
        author = self._require_employee(payload.author_id)
        approver = self._require_employee(payload.approver_id)
        if self.organization.get_department(payload.department_id) is None:
            raise HTTPException(status_code=400, detail="기안 부서를 찾을 수 없습니다.")
        if author.role != "ADMIN" and author.department_id != payload.department_id:
            raise HTTPException(
                status_code=400, detail="기안자의 소속 부서와 기안 부서가 다릅니다."
            )
        if author.id == approver.id:
            raise HTTPException(status_code=400, detail="작성자와 결재자는 같을 수 없습니다.")

        document = self.approvals.create(**payload.model_dump())
        self.session.commit()
        self.session.refresh(document)
        return self.approvals.to_response(document)

    def update(self, document_id: str, payload: ApprovalUpdate) -> ApprovalResponse:
        document = self._get_document(document_id)
        self._require_status(document, "DRAFT", "임시 저장 문서만 수정할 수 있습니다.")
        if payload.actor_id != document.author_id:
            raise HTTPException(status_code=403, detail="작성자만 문서를 수정할 수 있습니다.")

        changes = payload.model_dump(exclude={"actor_id"}, exclude_none=True)
        if "department_id" in changes:
            actor = self._require_employee(payload.actor_id)
            if self.organization.get_department(changes["department_id"]) is None:
                raise HTTPException(status_code=400, detail="기안 부서를 찾을 수 없습니다.")
            if actor.role != "ADMIN" and actor.department_id != changes["department_id"]:
                raise HTTPException(
                    status_code=400, detail="기안자의 소속 부서만 선택할 수 있습니다."
                )
        if "approver_id" in changes:
            self._require_employee(changes["approver_id"])
            if changes["approver_id"] == document.author_id:
                raise HTTPException(status_code=400, detail="작성자와 결재자는 같을 수 없습니다.")
        for field, value in changes.items():
            setattr(document, field, value)
        self.approvals.add_history(
            document=document,
            actor_id=payload.actor_id,
            action="UPDATED",
            from_status="DRAFT",
            to_status="DRAFT",
        )
        self.session.commit()
        self.session.refresh(document)
        return self.approvals.to_response(document)

    def delete(self, document_id: str, actor_id: str) -> None:
        document = self._get_document(document_id)
        actor = self._require_employee(actor_id)
        if actor.role != "ADMIN":
            raise HTTPException(status_code=403, detail="관리자만 문서를 삭제할 수 있습니다.")

        self.approvals.delete(document)
        self.session.commit()

    def submit(self, document_id: str, payload: ApprovalAction) -> ApprovalResponse:
        document = self._get_document(document_id)
        self._require_status(document, "DRAFT", "임시 저장 문서만 상신할 수 있습니다.")
        if payload.actor_id != document.author_id:
            raise HTTPException(status_code=403, detail="작성자만 문서를 상신할 수 있습니다.")
        self.approvals.mark_submitted(document, payload.actor_id, payload.comment)
        self.session.commit()
        self.session.refresh(document)
        return self.approvals.to_response(document)

    def approve(self, document_id: str, payload: ApprovalAction) -> ApprovalResponse:
        document = self._get_document(document_id)
        self._require_decision_permission(document, payload.actor_id)
        self.approvals.mark_processed(
            document,
            actor_id=payload.actor_id,
            target_status="APPROVED",
            action="APPROVED",
            comment=payload.comment,
        )
        self.recruitment.process_approval(document, "APPROVED")
        self.session.commit()
        self.session.refresh(document)
        return self.approvals.to_response(document)

    def reject(self, document_id: str, payload: ApprovalReject) -> ApprovalResponse:
        document = self._get_document(document_id)
        self._require_decision_permission(document, payload.actor_id)
        self.approvals.mark_processed(
            document,
            actor_id=payload.actor_id,
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
    def _require_status(document: ApprovalDocument, expected: str, message: str) -> None:
        if document.status != expected:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)

    def _require_decision_permission(self, document: ApprovalDocument, actor_id: str) -> None:
        self._require_status(document, "PENDING", "결재 대기 문서만 처리할 수 있습니다.")
        actor = self._require_employee(actor_id)
        if actor.role != "ADMIN" and actor.id != document.approver_id:
            raise HTTPException(
                status_code=403, detail="지정된 결재자 또는 관리자만 처리할 수 있습니다."
            )
