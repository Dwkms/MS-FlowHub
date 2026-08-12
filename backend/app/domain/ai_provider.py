"""생성형 AI Provider 경계.

Provider는 업무 모델을 모른다. 정리된 Context와 출력 스키마만 받아 원시 문자열을
돌려주는 역할만 한다. DB 조회·권한 판단·기록은 Service의 몫이다.
설계 근거는 docs/AI_AUTOMATION_PLAN.md 4장·10장 참조.
"""

import json
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel

APPROVAL_DRAFT = "APPROVAL_DRAFT"
JOB_POSTING_DRAFT = "JOB_POSTING_DRAFT"

MOCK = "mock"
CLAUDE = "claude"
MOCK_MODEL_NAME = "mock-sample-v1"

# 배열 항목 상한. Structured Output 스키마와 같은 값을 쓴다.
MAX_LIST_ITEMS = 8
MAX_PREFERRED_ITEMS = 6


@dataclass
class AIProviderResult:
    """Provider 호출 1회의 결과. 성공과 실패를 같은 형태로 표현한다.

    `content`는 **원시 문자열**이다. 스키마 검증은 Service가 한다. Provider가 검증까지
    맡으면 Mock과 실제 Provider의 계약이 갈라지고, 실패를 기록할 원본이 사라진다.
    """

    provider: str
    success: bool
    content: str | None = None
    model_name: str | None = None
    error_message: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class AIProvider(Protocol):
    def generate(
        self, feature_type: str, context: dict, output_schema: type[BaseModel]
    ) -> AIProviderResult: ...


def _lines(value: object, limit: int) -> list[str]:
    """개조식 텍스트를 항목 배열로 나눈다. 없는 값에서 항목을 만들지 않는다."""
    if not value:
        return []
    items = [line.strip(" -•\t") for line in str(value).splitlines()]
    return [item for item in items if item][:limit]


def _mock_approval_draft(context: dict) -> dict:
    """Context에 있는 사실만 문장에 넣는다. 없는 값은 문장 자체를 만들지 않는다."""
    purpose = context.get("purpose", "")
    department = context.get("department_name", "")

    details: list[str] = []
    if context.get("main_content"):
        details.append(str(context["main_content"]))
    for label, key in (("금액", "amount"), ("수량", "quantity"), ("희망 시점", "desired_date")):
        value = context.get(key)
        if value:
            details.append(f"{label}: {value}")
    if context.get("extra_note"):
        details.append(str(context["extra_note"]))

    title = f"{department} {purpose}".strip() or "품의 기안"
    return {
        "title": title[:200],
        "purpose": purpose or "요청 목적이 입력되지 않았습니다.",
        "details": "\n".join(details) or "주요 내용이 입력되지 않았습니다.",
        "expected_effect": "승인 후 위 내용을 계획대로 진행할 수 있습니다.",
    }


def _mock_job_posting_draft(context: dict) -> dict:
    position = context.get("position_title", "")
    department = context.get("department_name", "")

    intro: list[str] = []
    if department:
        intro.append(f"{department}에서 함께 일할 동료를 찾습니다.")
    if context.get("reason"):
        intro.append(str(context["reason"]))

    closing: list[str] = []
    if context.get("application_deadline"):
        closing.append(f"지원 마감: {context['application_deadline']}")
    if context.get("apply_method"):
        closing.append(f"지원 방법: {context['apply_method']}")

    return {
        "headline": (f"{department} {position} 채용".strip() or "채용 공고")[:200],
        "introduction": "\n".join(intro) or "채용 사유가 입력되지 않았습니다.",
        "responsibilities": _lines(context.get("responsibilities"), MAX_LIST_ITEMS),
        "requirements": _lines(context.get("required_skills"), MAX_LIST_ITEMS),
        "preferred_qualifications": _lines(context.get("preferred_skills"), MAX_PREFERRED_ITEMS),
        "team_or_recruitment_description": str(context.get("team_intro") or "")[:600],
        "closing_message": "\n".join(closing) or "지원 관련 문의는 인사팀으로 연락 바랍니다.",
    }


_MOCK_BUILDERS = {
    APPROVAL_DRAFT: _mock_approval_draft,
    JOB_POSTING_DRAFT: _mock_job_posting_draft,
}


class MockAIProvider:
    """API 키 없이 전체 흐름을 개발·시연하기 위한 Provider.

    실제 Provider와 **같은 계약**(스키마를 만족하는 JSON 문자열)을 돌려준다. 그래야
    Provider를 바꿔도 Service·검증·기록 경로가 그대로 동작한다.

    Mock도 "사실을 지어내지 않는다"는 원칙을 지킨다. Context에 금액이 없으면 금액 문장을
    만들지 않는다. 이 규칙을 Mock이 어기면 그 위에서 도는 방지 테스트가 무의미해진다.
    """

    def generate(
        self, feature_type: str, context: dict, output_schema: type[BaseModel]
    ) -> AIProviderResult:
        builder = _MOCK_BUILDERS.get(feature_type)
        if builder is None:
            return AIProviderResult(
                provider=MOCK,
                success=False,
                error_message=f"지원하지 않는 생성 유형입니다: {feature_type}",
            )
        return AIProviderResult(
            provider=MOCK,
            success=True,
            content=json.dumps(builder(context), ensure_ascii=False),
            model_name=MOCK_MODEL_NAME,
        )
