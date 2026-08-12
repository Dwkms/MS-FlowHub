"""Provider 경계 테스트. 네트워크를 타지 않는다."""

import pytest

from app.api.dependencies import _create_ai_provider
from app.domain.ai_provider import (
    APPROVAL_DRAFT,
    JOB_POSTING_DRAFT,
    MOCK,
    MockAIProvider,
)
from app.schemas.ai import ApprovalDraftOutput, JobPostingDraftOutput


@pytest.fixture(autouse=True)
def clear_provider_cache():
    _create_ai_provider.cache_clear()
    yield
    _create_ai_provider.cache_clear()


def test_mock_approval_draft_satisfies_schema():
    context = {
        "author_name": "김민성",
        "department_name": "개발팀",
        "purpose": "노트북 교체 요청",
        "main_content": "개발용 노트북 3대가 내구연한을 초과했습니다.",
        "amount": "6,000,000원",
    }

    result = MockAIProvider().generate(APPROVAL_DRAFT, context, ApprovalDraftOutput)

    assert result.success is True
    assert result.provider == MOCK
    draft = ApprovalDraftOutput.model_validate_json(result.content)
    assert "노트북 교체 요청" in draft.title
    assert "6,000,000원" in draft.details


def test_mock_does_not_invent_amount_when_context_has_none():
    """Mock도 '주어지지 않은 사실을 만들지 않는다'를 지킨다.

    Mock이 이 규칙을 어기면 그 위에서 도는 방지 테스트가 전부 무의미해진다.
    """
    context = {
        "department_name": "인사팀",
        "purpose": "교육 참가",
        "main_content": "외부 세미나 참가",
    }

    result = MockAIProvider().generate(APPROVAL_DRAFT, context, ApprovalDraftOutput)

    draft = ApprovalDraftOutput.model_validate_json(result.content)
    assert "금액" not in draft.details
    assert "원" not in draft.details


def test_mock_job_posting_draft_splits_bullet_text():
    context = {
        "department_name": "개발팀",
        "position_title": "백엔드 개발자",
        "reason": "서비스 확장에 따른 충원",
        "responsibilities": "API 설계\n데이터 모델링",
        "required_skills": "Python 3년 이상",
        "application_deadline": "2026-09-30",
    }

    result = MockAIProvider().generate(JOB_POSTING_DRAFT, context, JobPostingDraftOutput)

    draft = JobPostingDraftOutput.model_validate_json(result.content)
    assert draft.responsibilities == ["API 설계", "데이터 모델링"]
    assert draft.requirements == ["Python 3년 이상"]
    assert draft.preferred_qualifications == []
    assert "2026-09-30" in draft.closing_message


def test_mock_rejects_unknown_feature_type():
    result = MockAIProvider().generate("UNKNOWN_FEATURE", {}, ApprovalDraftOutput)

    assert result.success is False
    assert result.content is None
    assert "UNKNOWN_FEATURE" in result.error_message


def test_factory_returns_mock_by_default():
    provider = _create_ai_provider(MOCK, None, None, 8000, 15.0)

    assert isinstance(provider, MockAIProvider)


def test_factory_rejects_unknown_provider_name():
    with pytest.raises(RuntimeError, match="지원하지 않는 AI_PROVIDER"):
        _create_ai_provider("gemini", "key", None, 8000, 15.0)


def test_factory_rejects_real_provider_without_api_key():
    """키가 없다고 조용히 Mock으로 떨어뜨리지 않는다. 샘플을 실제 결과로 오인하면 안 된다."""
    with pytest.raises(RuntimeError, match="AI_API_KEY"):
        _create_ai_provider("claude", None, None, 8000, 15.0)


def test_claude_provider_fails_cleanly_without_network():
    """실제 Provider는 API 키가 없어 호출까지 검증할 수 없다.

    다만 모듈 import·생성자·실패 반환 경로는 네트워크 없이 확인할 수 있다. 지원하지 않는
    생성 유형은 프롬프트 조립 단계에서 막히므로 SDK를 부르지 않는다.
    """
    from app.domain.claude_provider import DEFAULT_MODEL, ClaudeProvider

    provider = ClaudeProvider(api_key="test-key-not-used")
    result = provider.generate("UNKNOWN_FEATURE", {}, ApprovalDraftOutput)

    assert result.success is False
    assert result.provider == "claude"
    assert result.model_name == DEFAULT_MODEL
    assert DEFAULT_MODEL == "claude-opus-5"


def test_system_prompt_forbids_inventing_facts():
    """프롬프트가 1차 방어선이다. 금지 문구가 사라지면 나머지 방어가 뒤로 밀린다."""
    from app.domain.ai_prompts import build_system_prompt

    prompt = build_system_prompt(APPROVAL_DRAFT)

    assert "만들어내지 않는다" in prompt
    assert "주어진 사실만 사용한다" in prompt

    with pytest.raises(ValueError, match="지원하지 않는"):
        build_system_prompt("UNKNOWN_FEATURE")
