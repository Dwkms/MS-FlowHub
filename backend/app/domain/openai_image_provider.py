"""OpenAI Image API 구현.

SDK 예외나 원문 응답은 API 밖으로 내보내지 않는다. API 키도 이 객체 생성 시에만 받고
로그·결과·DB에는 저장하지 않는다.
"""

from typing import Any

from app.domain.image_ai_provider import OPENAI, ImageAIProviderResult


def _usage_value(usage: object | None, name: str) -> int | None:
    value = getattr(usage, name, None)
    return value if isinstance(value, int) else None


def _safe_error_message(error: Exception) -> str:
    error_name = type(error).__name__
    if error_name == "APITimeoutError":
        return "OpenAI 이미지 생성 시간이 초과되었습니다. 다시 시도해 주세요."
    if error_name == "RateLimitError":
        return "OpenAI 이미지 생성 사용 한도에 도달했습니다. 잠시 후 다시 시도해 주세요."
    if error_name == "APIConnectionError":
        return "OpenAI 이미지 생성 서비스에 연결할 수 없습니다."
    return "OpenAI 이미지 생성 요청을 처리하지 못했습니다."


class OpenAIImageProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        size: str,
        quality: str,
        timeout: float,
        client: Any | None = None,
    ) -> None:
        if client is None:
            # disabled 경로와 자동 테스트는 SDK를 import하지 않는다.
            from openai import OpenAI

            client = OpenAI(api_key=api_key, timeout=timeout)
        self.client = client
        self.model = model
        self.size = size
        self.quality = quality

    def generate(self, prompt: str) -> ImageAIProviderResult:
        try:
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size=self.size,
                quality=self.quality,
                n=1,
            )
            data = response.data[0] if response.data else None
            image_base64 = getattr(data, "b64_json", None)
            if not image_base64:
                return ImageAIProviderResult(
                    provider=OPENAI,
                    success=False,
                    model_name=self.model,
                    error_message="OpenAI가 이미지 데이터를 반환하지 않았습니다.",
                )
            usage = getattr(response, "usage", None)
            return ImageAIProviderResult(
                provider=OPENAI,
                success=True,
                model_name=self.model,
                image_base64=image_base64,
                content_type="image/png",
                input_tokens=_usage_value(usage, "input_tokens"),
                output_tokens=_usage_value(usage, "output_tokens"),
            )
        except Exception as error:  # SDK 경계에서 외부 오류를 안전한 업무 결과로 변환한다.
            return ImageAIProviderResult(
                provider=OPENAI,
                success=False,
                model_name=self.model,
                error_message=_safe_error_message(error),
            )
