from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import AuthenticatedActor, get_approval_service
from app.schemas.approval import (
    ApprovalAction,
    ApprovalCreate,
    ApprovalReject,
    ApprovalResponse,
    ApprovalStatus,
    ApprovalSubmit,
    ApprovalUpdate,
)
from app.services.approval_service import ApprovalService

router = APIRouter(prefix="/approvals", tags=["Approvals"])
ApprovalServiceDependency = Annotated[ApprovalService, Depends(get_approval_service)]


@router.get("", response_model=list[ApprovalResponse])
def list_approvals(
    service: ApprovalServiceDependency,
    actor: AuthenticatedActor,
    search: str | None = None,
    status_filter: Annotated[ApprovalStatus | None, Query(alias="status")] = None,
) -> list[ApprovalResponse]:
    return service.list(
        actor=actor,
        search=search,
        status_filter=status_filter,
    )


@router.get("/{document_id}", response_model=ApprovalResponse)
def get_approval(
    document_id: str, service: ApprovalServiceDependency, actor: AuthenticatedActor
) -> ApprovalResponse:
    return service.get(document_id, actor)


@router.post("", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED)
def create_approval(
    payload: ApprovalCreate, service: ApprovalServiceDependency, actor: AuthenticatedActor
) -> ApprovalResponse:
    return service.create(payload, actor)


@router.patch("/{document_id}", response_model=ApprovalResponse)
def update_approval(
    document_id: str,
    payload: ApprovalUpdate,
    service: ApprovalServiceDependency,
    actor: AuthenticatedActor,
) -> ApprovalResponse:
    return service.update(document_id, payload, actor)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_approval(
    document_id: str,
    service: ApprovalServiceDependency,
    actor: AuthenticatedActor,
) -> None:
    service.delete(document_id, actor)


@router.post("/{document_id}/submit", response_model=ApprovalResponse)
def submit_approval(
    document_id: str,
    payload: ApprovalSubmit,
    service: ApprovalServiceDependency,
    actor: AuthenticatedActor,
) -> ApprovalResponse:
    return service.submit(document_id, actor, payload)


@router.post("/{document_id}/approve", response_model=ApprovalResponse)
def approve_approval(
    document_id: str,
    payload: ApprovalAction,
    service: ApprovalServiceDependency,
    actor: AuthenticatedActor,
) -> ApprovalResponse:
    return service.approve(document_id, actor, payload)


@router.post("/{document_id}/reject", response_model=ApprovalResponse)
def reject_approval(
    document_id: str,
    payload: ApprovalReject,
    service: ApprovalServiceDependency,
    actor: AuthenticatedActor,
) -> ApprovalResponse:
    return service.reject(document_id, actor, payload)
