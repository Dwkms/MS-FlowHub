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
from app.domain.ai_context import build_approval_context, build_job_posting_context
from app.domain.ai_provider import (
    APPROVAL_DRAFT,
    JOB_POSTING_DRAFT,
    AIProvider,
    AIProviderResult,
)
from app.models.ai_generation import AiGeneration
from app.repositories.ai_generation_repository import AiGenerationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.recruitment_repository import RecruitmentRepository
from app.schemas.ai import (
    ApprovalDraftOutput,
    ApprovalDraftRequest,
    JobPostingDraftOutput,
    JobPostingDraftRequest,
)
from app.security.identity import ActorContext

# 사용자당 한도만 면제한다. 전역 한도는 그대로 적용된다. 전역 쪽이 비용 상한을
# 만드는 실제 방어선이라, 여기까지 면제하면 한도를 둔 의미가 사라진다.
PER_USER_LIMIT_EXEMPT_ROLES = {"SUPER_ADMIN"}
SCHEMA_ERROR_MESSAGE = "AI 응답이 지정한 형식을 만족하지 않습니다."
EMPTY_RESPONSE_MESSAGE = "AI 응답을 받지 못했습니다."

# 공고 초안을 만들 수 있는 역할. 적용(PATCH /job-postings/{id})과 같은 범위로 맞춘다.
# 적용할 수 없는 사람이 초안만 뽑는 것은 의미가 없다.
JOB_POSTING_DRAFT_ROLES = {"SUPER_ADMIN", "HR_ADMIN", "ADMIN", "HR_MANAGER"}

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
        recruitment_repository: RecruitmentRepository,
        provider: AIProvider,
        settings: Settings,
    ) -> None:
        self.session = session
        self.repository = repository
        self.organization = organization_repository
        self.recruitment = recruitment_repository
        self.provider = provider
        self.settings = settings

    def generate_job_posting_draft(
        self, *, actor: ActorContext, payload: JobPostingDraftRequest
    ) -> AIGenerationOutcome:
        """채용 요청의 사실을 바탕으로 공고 문장을 다듬는다.

        주요 업무·필수 역량·우대 사항은 **이미 담당자가 쓴 텍스트**다. AI는 없는 것을
        만드는 게 아니라 공고 문장으로 옮긴다. 근무지·마감일·지원 방법처럼 DB에 없는 값은
        사용자가 입력했을 때만 Context에 들어간다.
        """
        if actor.role not in JOB_POSTING_DRAFT_ROLES:
            raise HTTPException(
                status_code=403,
                detail="인사 담당자 또는 관리자만 채용공고 초안을 생성할 수 있습니다.",
            )

        posting = self.recruitment.get_posting(payload.job_posting_id)
        if posting is None:
            raise HTTPException(status_code=404, detail="채용공고를 찾을 수 없습니다.")
        request = self.recruitment.get_request(posting.recruitment_request_id)
        if request is None:
            raise HTTPException(status_code=404, detail="연결된 채용 요청을 찾을 수 없습니다.")
        summary = self.recruitment.to_posting_response(posting)

        context = build_job_posting_context(
            position_title=request.position_title,
            headcount=request.headcount,
            employment_type=request.employment_type,
            experience_level=request.experience_level,
            department_name=summary.request_department_name,
            requester_name=summary.requester_name,
            reason=request.reason,
            responsibilities=request.responsibilities,
            required_skills=request.required_skills,
            preferred_skills=request.preferred_skills,
            desired_start_date=(
                request.desired_start_date.isoformat() if request.desired_start_date else None
            ),
            work_location=payload.work_location,
            application_deadline=payload.application_deadline,
            apply_method=payload.apply_method,
            team_intro=payload.team_intro,
            salary=payload.salary,
        )
        return self.generate(
            feature_type=JOB_POSTING_DRAFT,
            context=context,
            output_schema=JobPostingDraftOutput,
            actor=actor,
            related_type="JOB_POSTING",
            related_id=posting.id,
        )

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
            actor=actor,
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
        actor: ActorContext,
        related_type: str | None = None,
        related_id: str | None = None,
    ) -> AIGenerationOutcome:
        # 한도 판정에 역할이 필요해 created_by_id 대신 actor를 받는다.
        self._enforce_limits(actor)

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
            created_by_id=actor.employee_id,
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

    def _enforce_limits(self, actor: ActorContext) -> None:
        """Provider를 부르기 **전에** 막는다. 한도 초과는 호출도 기록도 하지 않는다.

        전역 한도를 먼저, 그리고 역할과 무관하게 본다. 사용자당 한도만 두면 계정 수만큼
        곱해져 열리므로 전역 쪽이 실제 비용 상한이다.

        메시지에 실제 한도 값을 담는다. "잠시 후 다시 시도"만 쓰면 최대 24시간을 기다려야
        하는 상황에서 사용자를 오도한다.
        """
        global_limit = self.settings.ai_daily_limit_global
        if self.repository.count_recent() >= global_limit:
            raise HTTPException(
                status_code=429,
                detail=f"전체 AI 초안 생성 한도에 도달했습니다. (최근 24시간 {global_limit}회)",
            )

        if actor.role in PER_USER_LIMIT_EXEMPT_ROLES:
            return

        per_user_limit = self.settings.ai_daily_limit_per_user
        if self.repository.count_recent(created_by_id=actor.employee_id) >= per_user_limit:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"AI 초안 생성은 최근 24시간 기준 {per_user_limit}회까지 가능합니다. "
                    "한도는 가장 오래된 생성 시각으로부터 24시간 뒤에 다시 열립니다."
                ),
            )

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
