from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.approval import ApprovalDocument, ApprovalHistory
from app.models.organization import Department, Employee
from app.schemas.approval import (
    ApprovalHistoryResponse,
    ApprovalResponse,
)
from app.schemas.common import DashboardBreakdownItem, DashboardTask


class ApprovalRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_documents(
        self,
        *,
        employee_id: str | None = None,
        search: str | None = None,
        status: str | None = None,
    ) -> list[ApprovalResponse]:
        statement = select(ApprovalDocument).order_by(ApprovalDocument.created_at.desc())
        if employee_id:
            statement = statement.where(
                or_(
                    ApprovalDocument.author_id == employee_id,
                    ApprovalDocument.approver_id == employee_id,
                )
            )
        if search:
            statement = statement.where(ApprovalDocument.title.ilike(f"%{search}%"))
        if status:
            statement = statement.where(ApprovalDocument.status == status)
        documents = self.session.scalars(statement).all()
        return [self.to_response(document) for document in documents]

    def get(self, document_id: str) -> ApprovalDocument | None:
        return self.session.get(ApprovalDocument, document_id)

    def delete(self, document: ApprovalDocument) -> None:
        self.session.delete(document)

    def create(
        self,
        *,
        document_type: str,
        title: str,
        content: str,
        department_id: str,
        author_id: str,
        approver_id: str,
        related_type: str | None = None,
        related_id: str | None = None,
    ) -> ApprovalDocument:
        document = ApprovalDocument(
            id=str(uuid4()),
            document_type=document_type,
            title=title,
            content=content,
            department_id=department_id,
            author_id=author_id,
            approver_id=approver_id,
            status="DRAFT",
            related_type=related_type,
            related_id=related_id,
        )
        self.session.add(document)
        self.session.flush()
        self.add_history(
            document=document,
            actor_id=author_id,
            action="CREATED",
            from_status=None,
            to_status="DRAFT",
        )
        return document

    def add_history(
        self,
        *,
        document: ApprovalDocument,
        actor_id: str,
        action: str,
        from_status: str | None,
        to_status: str,
        comment: str | None = None,
    ) -> None:
        self.session.add(
            ApprovalHistory(
                id=str(uuid4()),
                approval_document_id=document.id,
                actor_id=actor_id,
                action=action,
                from_status=from_status,
                to_status=to_status,
                comment=comment,
            )
        )

    def mark_submitted(
        self, document: ApprovalDocument, actor_id: str, comment: str | None
    ) -> None:
        document.status = "PENDING"
        document.submitted_at = datetime.now(UTC)
        self.add_history(
            document=document,
            actor_id=actor_id,
            action="SUBMITTED",
            from_status="DRAFT",
            to_status="PENDING",
            comment=comment,
        )

    def mark_processed(
        self,
        document: ApprovalDocument,
        *,
        actor_id: str,
        target_status: str,
        action: str,
        comment: str | None,
    ) -> None:
        document.status = target_status
        document.decision_comment = comment
        document.processed_at = datetime.now(UTC)
        self.add_history(
            document=document,
            actor_id=actor_id,
            action=action,
            from_status="PENDING",
            to_status=target_status,
            comment=comment,
        )

    def count_pending_for_approver(self, employee_id: str) -> int:
        statement = (
            select(func.count())
            .select_from(ApprovalDocument)
            .where(
                ApprovalDocument.approver_id == employee_id,
                ApprovalDocument.status == "PENDING",
            )
        )
        return self.session.scalar(statement) or 0

    def count_pending_for_author(self, employee_id: str) -> int:
        statement = (
            select(func.count())
            .select_from(ApprovalDocument)
            .where(
                ApprovalDocument.author_id == employee_id,
                ApprovalDocument.status == "PENDING",
            )
        )
        return self.session.scalar(statement) or 0

    def get_status_breakdown(self) -> list[DashboardBreakdownItem]:
        statement = (
            select(ApprovalDocument.status, func.count())
            .group_by(ApprovalDocument.status)
            .order_by(ApprovalDocument.status)
        )
        return [
            DashboardBreakdownItem(label=status, value=count)
            for status, count in self.session.execute(statement)
        ]

    def get_average_processing_hours(self) -> float | None:
        statement = select(ApprovalDocument.submitted_at, ApprovalDocument.processed_at).where(
            ApprovalDocument.submitted_at.is_not(None),
            ApprovalDocument.processed_at.is_not(None),
        )
        durations = [
            (processed_at - submitted_at).total_seconds() / 3600
            for submitted_at, processed_at in self.session.execute(statement)
        ]
        if not durations:
            return None
        return round(sum(durations) / len(durations), 1)

    def list_recent_tasks(self, employee_id: str, limit: int = 3) -> list[DashboardTask]:
        statement = (
            select(ApprovalDocument, Employee)
            .join(Employee, Employee.id == ApprovalDocument.author_id)
            .where(
                or_(
                    ApprovalDocument.author_id == employee_id,
                    ApprovalDocument.approver_id == employee_id,
                )
            )
            .order_by(ApprovalDocument.updated_at.desc())
            .limit(limit)
        )
        labels = {
            "DRAFT": "임시 저장",
            "PENDING": "결재 대기",
            "APPROVED": "승인",
            "REJECTED": "반려",
            "CANCELLED": "취소",
        }
        return [
            DashboardTask(
                id=document.id,
                category="전자결재",
                title=document.title,
                status=labels[document.status],
                owner=author.name,
                href=f"/approvals/{document.id}",
            )
            for document, author in self.session.execute(statement)
        ]

    def to_response(self, document: ApprovalDocument) -> ApprovalResponse:
        department = self.session.get(Department, document.department_id)
        author = self.session.get(Employee, document.author_id)
        approver = self.session.get(Employee, document.approver_id)
        history_statement = (
            select(ApprovalHistory, Employee)
            .join(Employee, Employee.id == ApprovalHistory.actor_id)
            .where(ApprovalHistory.approval_document_id == document.id)
            .order_by(ApprovalHistory.created_at)
        )
        histories = [
            ApprovalHistoryResponse(
                id=history.id,
                actor_id=history.actor_id,
                actor_name=actor.name,
                action=history.action,
                from_status=history.from_status,
                to_status=history.to_status,
                comment=history.comment,
                created_at=history.created_at,
            )
            for history, actor in self.session.execute(history_statement)
        ]
        return ApprovalResponse(
            id=document.id,
            document_type=document.document_type,
            title=document.title,
            content=document.content,
            department_id=document.department_id,
            department_name=department.name,
            author_id=document.author_id,
            author_name=author.name,
            approver_id=document.approver_id,
            approver_name=approver.name,
            status=document.status,
            decision_comment=document.decision_comment,
            submitted_at=document.submitted_at,
            processed_at=document.processed_at,
            related_type=document.related_type,
            related_id=document.related_id,
            created_at=document.created_at,
            updated_at=document.updated_at,
            histories=histories,
        )
