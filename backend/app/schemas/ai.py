"""생성형 AI Structured Output 스키마.

AI의 자유 텍스트를 그대로 믿지 않는다. 여기 정의한 스키마를 통과하지 못한 응답은
성공으로 처리하지 않는다(docs/AI_AUTOMATION_PLAN.md 12장).

길이 상한은 장식이 아니다. `title`은 `ApprovalDocument.title`·`JobPosting.title`이
`String(200)`이라 여기서 막지 않으면 DB 저장 시점에 터진다.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.approval import DocumentType

# 배열 항목 1개의 길이 상한. 항목 수 상한과 함께 걸어야 긴 출력이 포스터·폼을 깨지 않는다.
BulletItem = Annotated[str, Field(min_length=1, max_length=200)]


class AIOutputBaseModel(BaseModel):
    # 스키마에 없는 필드를 AI가 덧붙이면 성공으로 보지 않는다.
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class ApprovalDraftOutput(AIOutputBaseModel):
    """전자결재 초안. 최종 저장은 `ApprovalDocument.content` 한 덩어리이고,
    필드 단위 수정을 위해 조립은 프론트엔드가 한다."""

    title: str = Field(min_length=1, max_length=200)
    purpose: str = Field(min_length=1, max_length=500)
    details: str = Field(min_length=1, max_length=1500)
    expected_effect: str = Field(min_length=1, max_length=500)


class JobPostingDraftOutput(AIOutputBaseModel):
    """채용공고 초안. 업무·역량 항목은 이미 사용자가 쓴 텍스트를 다듬은 결과이지,
    없던 사실을 새로 만든 것이 아니다."""

    headline: str = Field(min_length=1, max_length=200)
    introduction: str = Field(min_length=1, max_length=600)
    responsibilities: list[BulletItem] = Field(default_factory=list, max_length=8)
    requirements: list[BulletItem] = Field(default_factory=list, max_length=8)
    preferred_qualifications: list[BulletItem] = Field(default_factory=list, max_length=6)
    team_or_recruitment_description: str = Field(default="", max_length=600)
    closing_message: str = Field(default="", max_length=300)


class AIRequestBaseModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class ApprovalDraftRequest(AIRequestBaseModel):
    """전자결재 초안 생성 입력.

    **DB 칼럼을 늘리지 않는다.** 여기 값들은 AI에게 맥락을 주기 위한 일회성 입력이고,
    보존은 `ai_generations.source_input`으로 충분하다. 결재 문서가 가져야 할 정보는
    최종 `content` 한 덩어리이지 이 필드들이 아니다.

    금액·수량을 숫자가 아니라 문자열로 받는다. "6,000,000원", "약 500만원"처럼 사용자가
    쓴 표현을 그대로 넘겨야 AI가 단위를 바꾸거나 반올림하지 않는다.
    """

    document_type: DocumentType
    purpose: str = Field(min_length=1, max_length=500)
    main_content: str = Field(min_length=1, max_length=2000)
    amount: str | None = Field(default=None, max_length=100)
    quantity: str | None = Field(default=None, max_length=100)
    desired_date: str | None = Field(default=None, max_length=100)
    extra_note: str | None = Field(default=None, max_length=1000)


class JobPostingDraftRequest(AIRequestBaseModel):
    """채용공고 초안 생성 입력.

    직무·인원·고용형태·경력·주요 업무·역량은 `RecruitmentRequest`에서 자동으로 가져오므로
    받지 않는다. 여기 있는 값들은 **DB에 없어서 사용자가 채워야 하는 것들**뿐이다.
    입력하지 않으면 Context에서 빠지고, AI가 근무지나 마감일을 지어낼 근거가 없어진다.
    """

    job_posting_id: str = Field(min_length=1)
    work_location: str | None = Field(default=None, max_length=200)
    application_deadline: str | None = Field(default=None, max_length=100)
    apply_method: str | None = Field(default=None, max_length=500)
    team_intro: str | None = Field(default=None, max_length=1000)
    salary: str | None = Field(default=None, max_length=200)


class JobPostingDraftResponse(BaseModel):
    generation_id: str
    success: bool
    provider: str
    is_sample: bool
    output: JobPostingDraftOutput | None = None
    error_message: str | None = None


class AIFinalOutputRequest(AIRequestBaseModel):
    """사용자가 수정해 실제로 적용한 최종본. 생성 원본은 덮어쓰지 않는다."""

    final_output: dict


class ApprovalDraftResponse(BaseModel):
    """실패도 200으로 내려간다. 초안 생성은 부가 기능이라 실패해도 직접 작성하면 된다.

    `is_sample`은 Mock Provider 결과임을 UI에 알린다. 샘플을 실제 LLM 결과로
    오인하는 것을 막는다(docs/AI_AUTOMATION_PLAN.md 15장).
    """

    generation_id: str
    success: bool
    provider: str
    is_sample: bool
    output: ApprovalDraftOutput | None = None
    error_message: str | None = None
