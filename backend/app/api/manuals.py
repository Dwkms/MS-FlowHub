from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    AuthenticatedActor,
    get_manual_service,
    require_employee_management_permission,
)
from app.schemas.manual import (
    ManualCategoryCreate,
    ManualCategoryResponse,
    ManualCategoryUpdate,
    ManualCreate,
    ManualDetail,
    ManualListItem,
    ManualUpdate,
)
from app.security.identity import ActorContext
from app.services.manual_service import ManualService

router = APIRouter(prefix="/manuals", tags=["Manuals"])
ManualServiceDependency = Annotated[ManualService, Depends(get_manual_service)]
ManualManager = Annotated[ActorContext, Depends(require_employee_management_permission)]


@router.get("/categories", response_model=list[ManualCategoryResponse])
def list_categories(
    service: ManualServiceDependency, _: AuthenticatedActor
) -> list[ManualCategoryResponse]:
    return service.list_categories()


@router.post(
    "/categories", response_model=ManualCategoryResponse, status_code=status.HTTP_201_CREATED
)
def create_category(
    payload: ManualCategoryCreate, service: ManualServiceDependency, _: ManualManager
) -> ManualCategoryResponse:
    return service.create_category(payload)


@router.patch("/categories/{category_id}", response_model=ManualCategoryResponse)
def update_category(
    category_id: str,
    payload: ManualCategoryUpdate,
    service: ManualServiceDependency,
    _: ManualManager,
) -> ManualCategoryResponse:
    return service.update_category(category_id, payload)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: str, service: ManualServiceDependency, _: ManualManager) -> None:
    service.delete_category(category_id)


@router.get("", response_model=list[ManualListItem])
def list_manuals(
    service: ManualServiceDependency,
    actor: AuthenticatedActor,
    search: str | None = None,
    category_id: str | None = Query(default=None),
) -> list[ManualListItem]:
    return service.list_manuals(actor, search, category_id)


@router.get("/{slug}", response_model=ManualDetail)
def get_manual(
    slug: str, service: ManualServiceDependency, actor: AuthenticatedActor
) -> ManualDetail:
    return service.get_manual(slug, actor)


@router.post("", response_model=ManualDetail, status_code=status.HTTP_201_CREATED)
def create_manual(
    payload: ManualCreate, service: ManualServiceDependency, actor: ManualManager
) -> ManualDetail:
    return service.create_manual(payload, actor)


@router.patch("/{slug}", response_model=ManualDetail)
def update_manual(
    slug: str, payload: ManualUpdate, service: ManualServiceDependency, actor: ManualManager
) -> ManualDetail:
    return service.update_manual(slug, payload, actor)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_manual(slug: str, service: ManualServiceDependency, _: ManualManager) -> None:
    service.delete_manual(slug)
