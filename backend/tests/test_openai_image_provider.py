"""OpenAI 이미지 SDK 경계 테스트. 실제 네트워크와 API 키를 사용하지 않는다."""

from types import SimpleNamespace

import pytest

from app.api.dependencies import _create_image_ai_provider
from app.domain.image_ai_provider import DisabledImageAIProvider
from app.domain.openai_image_provider import OpenAIImageProvider


class FakeImages:
    def __init__(self, response=None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.kwargs = None

    def generate(self, **kwargs):
        self.kwargs = kwargs
        if self.error is not None:
            raise self.error
        return self.response


class APITimeoutError(Exception):
    pass


@pytest.fixture(autouse=True)
def clear_provider_cache():
    _create_image_ai_provider.cache_clear()
    yield
    _create_image_ai_provider.cache_clear()


def _provider(images: FakeImages) -> OpenAIImageProvider:
    return OpenAIImageProvider(
        api_key="unused-test-key",
        model="gpt-image-2",
        size="1024x1536",
        quality="medium",
        timeout=120,
        client=SimpleNamespace(images=images),
    )


def test_generates_one_portrait_image_and_returns_usage() -> None:
    images = FakeImages(
        SimpleNamespace(
            data=[SimpleNamespace(b64_json="aW1hZ2U=")],
            usage=SimpleNamespace(input_tokens=120, output_tokens=900),
        )
    )

    result = _provider(images).generate("poster prompt")

    assert result.success is True
    assert result.image_base64 == "aW1hZ2U="
    assert result.input_tokens == 120
    assert result.output_tokens == 900
    assert images.kwargs == {
        "model": "gpt-image-2",
        "prompt": "poster prompt",
        "size": "1024x1536",
        "quality": "medium",
        "n": 1,
    }


def test_timeout_is_sanitized() -> None:
    result = _provider(FakeImages(error=APITimeoutError("secret raw response"))).generate(
        "poster prompt"
    )

    assert result.success is False
    assert "시간이 초과" in result.error_message
    assert "secret" not in result.error_message


def test_missing_image_data_is_failure() -> None:
    result = _provider(FakeImages(SimpleNamespace(data=[], usage=None))).generate("poster prompt")

    assert result.success is False
    assert "이미지 데이터" in result.error_message


def test_disabled_factory_does_not_require_sdk_or_key() -> None:
    provider = _create_image_ai_provider(
        "disabled", None, "gpt-image-2", "1024x1536", "medium", 120
    )

    assert isinstance(provider, DisabledImageAIProvider)


def test_openai_factory_requires_key() -> None:
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        _create_image_ai_provider("openai", None, "gpt-image-2", "1024x1536", "medium", 120)


def test_openai_factory_builds_provider_without_calling_api() -> None:
    provider = _create_image_ai_provider(
        "openai", "sk-test", "gpt-image-2", "1024x1536", "medium", 120
    )

    assert isinstance(provider, OpenAIImageProvider)
