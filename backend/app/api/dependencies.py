from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db_session
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.recruitment_repository import RecruitmentRepository
from app.services.approval_service import ApprovalService
from app.services.dashboard_service import DashboardService
from app.services.recruitment_service import RecruitmentService

DatabaseSession = Annotated[Session, Depends(get_db_session)]


def get_dashboard_service(session: DatabaseSession) -> DashboardService:
    return DashboardService(
        organization_repository=OrganizationRepository(session),
        approval_repository=ApprovalRepository(session),
        settings=get_settings(),
    )


def get_approval_service(session: DatabaseSession) -> ApprovalService:
    recruitment_service = _build_recruitment_service(session)
    return ApprovalService(
        session=session,
        approval_repository=ApprovalRepository(session),
        organization_repository=OrganizationRepository(session),
        recruitment_service=recruitment_service,
    )


def get_recruitment_service(session: DatabaseSession) -> RecruitmentService:
    return _build_recruitment_service(session)


def _build_recruitment_service(session: Session) -> RecruitmentService:
    return RecruitmentService(
        session=session,
        recruitment_repository=RecruitmentRepository(session),
        approval_repository=ApprovalRepository(session),
        organization_repository=OrganizationRepository(session),
        notification_repository=NotificationRepository(session),
    )
