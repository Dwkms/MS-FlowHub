"""채용 포스터 이미지 생성 Provider 경계.

텍스트 Structured Output Provider와 반환 형식이 다르므로 별도 Protocol을 사용한다.
Router와 Service는 OpenAI SDK를 직접 알지 않고 이 계약만 의존한다.
"""

from dataclasses import dataclass
from typing import Protocol

DISABLED = "disabled"
OPENAI = "openai"


@dataclass(frozen=True)
class ImageAIProviderResult:
    provider: str
    success: bool
    model_name: str | None = None
    image_base64: str | None = None
    content_type: str | None = None
    error_message: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class ImageAIProvider(Protocol):
    def generate(self, prompt: str) -> ImageAIProviderResult: ...


class DisabledImageAIProvider:
    """명시적으로 비활성화된 상태를 유료 호출 없이 반환한다."""

    def generate(self, prompt: str) -> ImageAIProviderResult:
        del prompt
        return ImageAIProviderResult(
            provider=DISABLED,
            success=False,
            error_message="채용 포스터 이미지 생성 기능이 비활성화되어 있습니다.",
        )
