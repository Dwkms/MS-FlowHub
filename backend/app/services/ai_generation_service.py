"""생성형 AI 조율 계층.

한도 확인 → Provider 호출 → 스키마 검증 → 기록 순서로 진행한다. **업무 테이블에는
쓰지 않는다.** 이 서비스가 건드리는 테이블은 `ai_generations` 하나뿐이고, 그래서
AI가 실패하든 성공하든 전자결재·채용 상태가 변할 수 없다
(docs/AI_AUTOMATION_PLAN.md 18장).
"""

from dataclasses import dataclass
from datetime import date
from uuid import uuid4

from fastapi import HTTPException
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.ai_context import build_approval_context
from app.domain.ai_provider import (
    APPROVAL_DRAFT,
    JOB_POSTING_DRAFT,
    AIProvider,
    AIProviderResult,
)
from app.models.ai_generation import AiGeneration
from app.repositories.ai_generation_repository import AiGenerationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.ai import (
    ApprovalDraftOutput,
    ApprovalDraftRequest,
    JobPostingDraftOutput,
)
from app.security.identity import ActorContext

LIMIT_MESSAGE = "오늘 AI 초안 생성 한도를 초과했습니다. 잠시 후 다시 시도해 주세요."
SCHEMA_ERROR_MESSAGE = "AI 응답이 지정한 형식을 만족하지 않습니다."
EMPTY_RESPONSE_MESSAGE = "AI 응답을 받지 못했습니다."

# 기능별 출력 스키마. 사용자가 수정해 적용한 최종본도 같은 스키마로 검증한다.
OUTPUT_SCHEMAS: dict[str, type[BaseModel]] = {
    APPROVAL_DRAFT: ApprovalDraftOutput,
    JOB_POSTING_DRAFT: JobPostingDraftOutput,
}


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
        organization_repository: OrganizationRepository,
        provider: AIProvider,
        settings: Settings,
    ) -> None:
        self.session = session
        self.repository = repository
        self.organization = organization_repository
        self.provider = provider
        self.settings = settings

    def generate_approval_draft(
        self, *, actor: ActorContext, payload: ApprovalDraftRequest
    ) -> AIGenerationOutcome:
        """DB 사실(작성자·부서·팀·직급)과 사용자 입력을 합쳐 초안을 만든다.

        `EmployeeDetail`을 통째로 넘기지 않고 필요한 필드만 뽑아 전달한다. 그 객체에는
        이메일·사번·근태 사유가 함께 들어 있고, Context Builder가 허용 목록 역할을 한다.
        """
        employee = self.organization.get_employee_detail(actor.employee_id)
        if employee is None:
            raise HTTPException(status_code=403, detail="직원 정보를 찾을 수 없습니다.")

        context = build_approval_context(
            author_name=employee.name,
            position=employee.position,
            job_title=employee.job_title,
            department_name=employee.department,
            team_name=employee.team,
            drafted_on=date.today(),
            document_type=payload.document_type,
            purpose=payload.purpose,
            main_content=payload.main_content,
            amount=payload.amount,
            quantity=payload.quantity,
            desired_date=payload.desired_date,
            extra_note=payload.extra_note,
        )
        return self.generate(
            feature_type=APPROVAL_DRAFT,
            context=context,
            output_schema=ApprovalDraftOutput,
            created_by_id=actor.employee_id,
        )

    def record_final_output(
        self, *, generation_id: str, final_output: dict, actor: ActorContext
    ) -> None:
        """사용자가 적용한 최종본을 기록한다. `generated_output`은 덮어쓰지 않는다.

        이 메서드도 업무 테이블을 건드리지 않는다. 전자결재 저장은 사용자가 작성 화면에서
        [임시 저장]/[결재 요청]을 눌렀을 때 기존 경로로만 일어난다.
        """
        record = self.repository.get(generation_id)
        if record is None:
            raise HTTPException(status_code=404, detail="생성 기록을 찾을 수 없습니다.")
        if record.created_by_id != actor.employee_id:
            raise HTTPException(status_code=403, detail="본인이 생성한 초안만 기록할 수 있습니다.")

        schema = OUTPUT_SCHEMAS.get(record.feature_type)
        if schema is None:
            raise HTTPException(status_code=400, detail="지원하지 않는 생성 유형입니다.")
        try:
            validated = schema.model_validate(final_output)
        except ValidationError as error:
            raise HTTPException(
                status_code=422, detail="적용한 내용이 형식을 만족하지 않습니다."
            ) from error

        record.final_output = validated.model_dump(mode="json")
        self.session.commit()

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
