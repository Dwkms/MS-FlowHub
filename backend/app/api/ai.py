from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import AuthenticatedActor, get_ai_generation_service
from app.domain.ai_provider import MOCK
from app.schemas.ai import (
    AIFinalOutputRequest,
    ApprovalDraftOutput,
    ApprovalDraftRequest,
    ApprovalDraftResponse,
)
from app.services.ai_generation_service import AIGenerationService

router = APIRouter(prefix="/ai", tags=["AI"])
AIServiceDependency = Annotated[AIGenerationService, Depends(get_ai_generation_service)]


@router.post("/approval-drafts", response_model=ApprovalDraftResponse)
def create_approval_draft(
    payload: ApprovalDraftRequest, service: AIServiceDependency, actor: AuthenticatedActor
) -> ApprovalDraftResponse:
    """전자결재 초안을 생성합니다. 결재 문서를 만들거나 상태를 바꾸지 않습니다.

    생성 실패는 200 + `success: false`로 내려갑니다. 초안은 부가 기능이고, 실패해도
    사용자는 직접 작성하면 되므로 기존 작성 흐름을 5xx로 막지 않습니다.
    """
    outcome = service.generate_approval_draft(actor=actor, payload=payload)
    return ApprovalDraftResponse(
        generation_id=outcome.generation_id,
        success=outcome.success,
        provider=outcome.provider,
        is_sample=outcome.provider == MOCK,
        output=outcome.output if isinstance(outcome.output, ApprovalDraftOutput) else None,
        error_message=outcome.error_message,
    )


@router.patch("/generations/{generation_id}/final", status_code=status.HTTP_204_NO_CONTENT)
def record_final_output(
    generation_id: str,
    payload: AIFinalOutputRequest,
    service: AIServiceDependency,
    actor: AuthenticatedActor,
) -> None:
    """사용자가 수정해 실제로 적용한 최종본을 기록합니다.

    AI 최초 결과(`generated_output`)는 덮어쓰지 않습니다. 이 호출도 업무 데이터를
    저장하지 않으며, 전자결재 저장은 작성 화면의 기존 버튼으로만 일어납니다.
    """
    service.record_final_output(
        generation_id=generation_id, final_output=payload.final_output, actor=actor
    )
