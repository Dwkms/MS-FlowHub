from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import AuthenticatedActor, get_ax_service
from app.schemas.ax import AxChatRequest, AxChatResponse
from app.services.ax_service import AxService

router = APIRouter(prefix="/ax", tags=["AX"])
AxServiceDependency = Annotated[AxService, Depends(get_ax_service)]


@router.post("/chat", response_model=AxChatResponse)
def chat(
    payload: AxChatRequest, service: AxServiceDependency, actor: AuthenticatedActor
) -> AxChatResponse:
    """등록된 매뉴얼·FAQ에서 질문에 맞는 문서를 찾아 안내합니다.

    역할에 따라 볼 수 있는 매뉴얼만 검색 후보가 되며, 업무 데이터는 변경하지 않습니다.
    """
    return service.answer(payload.question, actor.role)
