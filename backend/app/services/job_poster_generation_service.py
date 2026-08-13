"""승인된 채용공고를 바탕으로 포스터 미리보기를 생성한다."""

import base64
import binascii
from dataclasses import dataclass
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.image_ai_provider import ImageAIProvider
from app.domain.job_poster_prompt import build_job_poster_context, build_job_poster_prompt
from app.domain.recruitment_options import describe_experience
from app.models.ai_generation import AiGeneration
from app.repositories.ai_generation_repository import AiGenerationRepository
from app.repositories.recruitment_repository import RecruitmentRepository
from app.schemas.ai import JobPosterGenerateRequest
from app.security.identity import ActorContext
from app.services.ai_generation_service import JOB_POSTING_DRAFT_ROLES, enforce_ai_limits

JOB_POSTER = "JOB_POSTER"
MAX_GENERATED_IMAGE_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class JobPosterGenerationOutcome:
    generation_id: str
    success: bool
    provider: str
    model_name: str | None = None
    image_base64: str | None = None
    content_type: str | None = None
    error_message: str | None = None


class JobPosterGenerationService:
    def __init__(
        self,
        *,
        session: Session,
        repository: AiGenerationRepository,
        recruitment_repository: RecruitmentRepository,
        provider: ImageAIProvider,
        settings: Settings,
    ) -> None:
        self.session = session
        self.repository = repository
        self.recruitment = recruitment_repository
        self.provider = provider
        self.settings = settings

    def generate(
        self, *, actor: ActorContext, payload: JobPosterGenerateRequest
    ) -> JobPosterGenerationOutcome:
        if actor.role not in JOB_POSTING_DRAFT_ROLES:
            raise HTTPException(
                status_code=403,
                detail="인사 담당자 또는 관리자만 채용 포스터를 생성할 수 있습니다.",
            )

        posting = self.recruitment.get_posting(payload.job_posting_id)
        if posting is None:
            raise HTTPException(status_code=404, detail="채용공고를 찾을 수 없습니다.")
        request = self.recruitment.get_request(posting.recruitment_request_id)
        if request is None:
            raise HTTPException(status_code=404, detail="연결된 채용 요청을 찾을 수 없습니다.")
        posting_summary = self.recruitment.to_posting_response(posting)

        context = build_job_poster_context(
            posting_title=posting.title,
            posting_content=posting.content,
            department_name=posting_summary.request_department_name,
            position_title=request.position_title,
            headcount=request.headcount,
            employment_type=request.employment_type,
            experience_label=describe_experience(
                request.experience_level, request.experience_years_min
            ),
            education_level=request.education_level,
            work_location=request.work_location,
            salary=request.salary,
            application_deadline=request.application_deadline,
            apply_method=request.apply_method,
            responsibilities=request.responsibilities,
            required_skills=request.required_skills,
            preferred_skills=request.preferred_skills,
            design_direction=payload.design_direction,
        )

        enforce_ai_limits(
            repository=self.repository,
            actor=actor,
            per_user_limit=self.settings.image_ai_daily_limit_per_user,
            global_limit=self.settings.image_ai_daily_limit_global,
            feature_type=JOB_POSTER,
            label="채용 포스터 이미지 생성",
        )
        result = self.provider.generate(build_job_poster_prompt(context))
        if result.success:
            image_bytes, error_message = self._decode_image(
                result.image_base64, result.error_message
            )
        else:
            image_bytes = None
            error_message = result.error_message or "이미지 생성에 실패했습니다."
        success = image_bytes is not None

        generated_output = None
        if success:
            generated_output = {
                "content_type": result.content_type or "image/png",
                "size_bytes": len(image_bytes),
                "delivery": "preview_only",
            }

        record = AiGeneration(
            id=f"ai-gen-{uuid4().hex}",
            feature_type=JOB_POSTER,
            related_type="JOB_POSTING",
            related_id=posting.id,
            source_input=context,
            generated_output=generated_output,
            provider=result.provider,
            model_name=result.model_name,
            success=success,
            error_message=None if success else error_message,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            created_by_id=actor.employee_id,
        )
        self.repository.add(record)
        self.session.commit()

        return JobPosterGenerationOutcome(
            generation_id=record.id,
            success=success,
            provider=result.provider,
            model_name=result.model_name,
            image_base64=result.image_base64 if success else None,
            content_type=(result.content_type or "image/png") if success else None,
            error_message=None if success else error_message,
        )

    @staticmethod
    def _decode_image(
        image_base64: str | None, provider_error: str | None
    ) -> tuple[bytes | None, str | None]:
        if image_base64 is None:
            return None, provider_error or "이미지 데이터를 받지 못했습니다."
        if len(image_base64) > ((MAX_GENERATED_IMAGE_BYTES * 4) // 3) + 8:
            return None, "생성된 이미지가 5MB 제한을 초과했습니다."
        try:
            content = base64.b64decode(image_base64, validate=True)
        except (binascii.Error, ValueError):
            return None, "AI 이미지 데이터의 형식이 올바르지 않습니다."
        if not content:
            return None, "AI 이미지 데이터가 비어 있습니다."
        if len(content) > MAX_GENERATED_IMAGE_BYTES:
            return None, "생성된 이미지가 5MB 제한을 초과했습니다."
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            return None, "AI 이미지가 PNG 형식이 아닙니다."
        return content, None
