from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import AuthenticatedActor, get_manual_service
from app.schemas.manual import ManualFaqResponse
from app.services.manual_service import ManualService

router = APIRouter(prefix="/faqs", tags=["FAQ"])
ManualServiceDependency = Annotated[ManualService, Depends(get_manual_service)]


@router.get("", response_model=list[ManualFaqResponse])
def list_faqs(service: ManualServiceDependency, _: AuthenticatedActor) -> list[ManualFaqResponse]:
    """모든 인증된 직원이 공개 FAQ를 조회합니다."""
    return service.list_faqs()
