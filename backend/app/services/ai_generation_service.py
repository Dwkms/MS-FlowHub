"""생성형 AI 조율 계층.

한도 확인 → Provider 호출 → 스키마 검증 → 기록 순서로 진행한다. **업무 테이블에는
쓰지 않는다.** 이 서비스가 건드리는 테이블은 `ai_generations` 하나뿐이고, 그래서
AI가 실패하든 성공하든 전자결재·채용 상태가 변할 수 없다
(docs/AI_AUTOMATION_PLAN.md 18장).
"""

from dataclasses import dataclass
from uuid import uuid4

from fastapi import HTTPException
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.ai_provider import AIProvider, AIProviderResult
from app.models.ai_generation import AiGeneration
from app.repositories.ai_generation_repository import AiGenerationRepository

LIMIT_MESSAGE = "오늘 AI 초안 생성 한도를 초과했습니다. 잠시 후 다시 시도해 주세요."
SCHEMA_ERROR_MESSAGE = "AI 응답이 지정한 형식을 만족하지 않습니다."
EMPTY_RESPONSE_MESSAGE = "AI 응답을 받지 못했습니다."


@dataclass
class AIGenerationOutcome:
    """생성 1건의 결과. 실패도 200으로 돌려주기 위해 성공 여부를 값으로 담는다."""

    generation_id: str
    success: bool
    provider: str
    output: BaseModel | None = None
    error_message: str | None = None


class AIGenerationService:
    def __init__(
        self,
        *,
        session: Session,
        repository: AiGenerationRepository,
        provider: AIProvider,
        settings: Settings,
    ) -> None:
        self.session = session
        self.repository = repository
        self.provider = provider
        self.settings = settings

    def generate(
        self,
        *,
        feature_type: str,
        context: dict,
        output_schema: type[BaseModel],
        created_by_id: str,
        related_type: str | None = None,
        related_id: str | None = None,
    ) -> AIGenerationOutcome:
        self._enforce_limits(created_by_id)

        result = self.provider.generate(feature_type, context, output_schema)
        output, error_message = self._validate(result, output_schema)

        record = AiGeneration(
            id=f"ai-gen-{uuid4().hex}",
            feature_type=feature_type,
            related_type=related_type,
            related_id=related_id,
            source_input=context,
            generated_output=output.model_dump(mode="json") if output is not None else None,
            provider=result.provider,
            model_name=result.model_name,
            success=output is not None,
            error_message=error_message,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            created_by_id=created_by_id,
        )
        self.repository.add(record)
        self.session.commit()

        return AIGenerationOutcome(
            generation_id=record.id,
            success=output is not None,
            provider=result.provider,
            output=output,
            error_message=error_message,
        )

    def _enforce_limits(self, created_by_id: str) -> None:
        """Provider를 부르기 **전에** 막는다. 한도 초과는 호출도 기록도 하지 않는다.

        전역 한도를 먼저 본다. 사용자당 한도만 두면 계정 수만큼 곱해져 열린다.
        """
        if self.repository.count_recent() >= self.settings.ai_daily_limit_global:
            raise HTTPException(status_code=429, detail=LIMIT_MESSAGE)
        if (
            self.repository.count_recent(created_by_id=created_by_id)
            >= self.settings.ai_daily_limit_per_user
        ):
            raise HTTPException(status_code=429, detail=LIMIT_MESSAGE)

    @staticmethod
    def _validate(
        result: AIProviderResult, output_schema: type[BaseModel]
    ) -> tuple[BaseModel | None, str | None]:
        """스키마를 통과하지 못한 응답은 성공으로 처리하지 않는다.

        검증 실패 시 원시 응답을 저장하지 않는다. 무엇이 왔는지 남기면 편하지만,
        AI 응답에는 Context가 되비쳐 나오므로 최소 저장 원칙(19장)을 지킨다.
        """
        if not result.success or result.content is None:
            return None, result.error_message or EMPTY_RESPONSE_MESSAGE
        try:
            return output_schema.model_validate_json(result.content), None
        except ValidationError:
            return None, SCHEMA_ERROR_MESSAGE
