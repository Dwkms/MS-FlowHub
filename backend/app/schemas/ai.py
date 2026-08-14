"""생성형 AI Structured Output 스키마.

AI의 자유 텍스트를 그대로 믿지 않는다. 여기 정의한 스키마를 통과하지 못한 응답은
성공으로 처리하지 않는다(docs/archive/AI_AUTOMATION_PLAN.md 12장).

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
    # 근거가 없으면 비울 수 있어야 한다. 프롬프트는 "쓸 근거가 없으면 빈 문자열로 둔다"고
    # 지시하는데 여기서 필수로 막으면, AI가 규칙을 지킨 응답이 검증에서 떨어진다.
    # 기대 효과를 억지로 지어내게 하는 것보다 비워두고 사용자가 채우는 편이 낫다.
    expected_effect: str = Field(default="", max_length=500)


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
    # 최소 길이를 둔다. "ㅇㅇ" 같은 입력은 AI가 쓸 근거가 없어 결국 검증에서 떨어지는데,
    # 그때는 이미 API 호출 비용이 나간 뒤다. 여기서 막으면 호출 자체가 발생하지 않는다.
    purpose: str = Field(min_length=4, max_length=500)
    main_content: str = Field(min_length=10, max_length=2000)
    amount: str | None = Field(default=None, max_length=100)
    quantity: str | None = Field(default=None, max_length=100)
    desired_date: str | None = Field(default=None, max_length=100)
    extra_note: str | None = Field(default=None, max_length=1000)


class JobPostingDraftRequest(AIRequestBaseModel):
    """채용공고 초안 생성 입력.

    직무·인원·고용형태·경력·학력·주요 업무·역량은 `RecruitmentRequest`에서 자동으로 가져오므로
    받지 않는다.

    근무지·급여·마감일·지원방법도 이제 채용 요청 단계에서 받아 DB에 있다. **서버가 DB 값을
    우선 쓰고**, 여기 남은 필드는 그 칼럼들이 없던 시절의 요청을 위한 보완 경로다. 결재자가
    보고 승인한 근무지를 AI 패널에서 조용히 갈아끼울 수 없다.

    `team_intro`만 DB에 없어 항상 사용자 입력이다. 입력하지 않으면 Context에서 빠지고,
    AI가 팀 소개를 지어낼 근거가 없어진다.
    """

    job_posting_id: str = Field(min_length=1)
    # 전부 선택 항목이다. 다만 값을 넣었다면 최소 길이를 요구한다. 여기 적은 값은 공고에
    # 그대로 실리므로, "ㅇㅇ" 같은 입력은 공고를 오염시키거나 AI가 조용히 버린다.
    work_location: str | None = Field(default=None, min_length=2, max_length=200)
    application_deadline: str | None = Field(default=None, min_length=4, max_length=100)
    apply_method: str | None = Field(default=None, min_length=5, max_length=500)
    team_intro: str | None = Field(default=None, min_length=10, max_length=1000)
    salary: str | None = Field(default=None, min_length=2, max_length=200)


class JobPostingDraftResponse(BaseModel):
    generation_id: str
    success: bool
    provider: str
    is_sample: bool
    output: JobPostingDraftOutput | None = None
    error_message: str | None = None


class JobPosterGenerateRequest(AIRequestBaseModel):
    """승인 후 생성된 공고를 포스터 이미지로 표현하기 위한 요청."""

    job_posting_id: str = Field(min_length=1)
    design_direction: str | None = Field(default=None, min_length=4, max_length=500)


class JobPosterGenerateResponse(BaseModel):
    generation_id: str
    success: bool
    provider: str
    model_name: str | None = None
    image_base64: str | None = None
    content_type: str | None = None
    error_message: str | None = None


class AIFinalOutputRequest(AIRequestBaseModel):
    """사용자가 수정해 실제로 적용한 최종본. 생성 원본은 덮어쓰지 않는다."""

    final_output: dict


class ApprovalDraftResponse(BaseModel):
    """실패도 200으로 내려간다. 초안 생성은 부가 기능이라 실패해도 직접 작성하면 된다.

    `is_sample`은 Mock Provider 결과임을 UI에 알린다. 샘플을 실제 LLM 결과로
    오인하는 것을 막는다(docs/archive/AI_AUTOMATION_PLAN.md 15장).
    """

    generation_id: str
    success: bool
    provider: str
    is_sample: bool
    output: ApprovalDraftOutput | None = None
    error_message: str | None = None
