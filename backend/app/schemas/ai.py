"""생성형 AI Structured Output 스키마.

AI의 자유 텍스트를 그대로 믿지 않는다. 여기 정의한 스키마를 통과하지 못한 응답은
성공으로 처리하지 않는다(docs/AI_AUTOMATION_PLAN.md 12장).

길이 상한은 장식이 아니다. `title`은 `ApprovalDocument.title`·`JobPosting.title`이
`String(200)`이라 여기서 막지 않으면 DB 저장 시점에 터진다.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

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
