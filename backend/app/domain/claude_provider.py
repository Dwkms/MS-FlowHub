"""Anthropic Claude Provider.

공식 SDK를 쓴다. HTTP를 직접 부르지 않는 이유는 Structured Output 스키마 정리·검증과
재시도를 SDK가 이미 제공하기 때문이다(docs/AI_AUTOMATION_PLAN.md 10장).

이 모듈은 `anthropic`을 import하므로, Mock 경로가 SDK에 의존하지 않도록
`app/api/dependencies.py`에서 **실제 Provider가 필요할 때만** 지연 import한다.
"""

import json

import anthropic
from pydantic import BaseModel, ValidationError

from app.domain.ai_prompts import build_system_prompt
from app.domain.ai_provider import CLAUDE, AIProviderResult

PROVIDER_NAME = CLAUDE
DEFAULT_MODEL = "claude-opus-5"


class ClaudeProvider:
    """실패를 예외가 아니라 `AIProviderResult(success=False)`로 돌려준다.

    초안 생성은 부가 기능이라, AI가 죽어도 사용자는 직접 작성하면 된다. 여기서 예외를
    올려보내면 기존 전자결재·채용 기능까지 5xx로 끌고 들어간다.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str | None = None,
        timeout: float = 15.0,
        max_retries: int = 2,
        max_tokens: int = 8000,
    ) -> None:
        self._client = anthropic.Anthropic(
            api_key=api_key, timeout=timeout, max_retries=max_retries
        )
        self._model = model or DEFAULT_MODEL
        self._max_tokens = max_tokens

    def generate(
        self, feature_type: str, context: dict, output_schema: type[BaseModel]
    ) -> AIProviderResult:
        try:
            system_prompt = build_system_prompt(feature_type)
        except ValueError as error:
            return self._failure(str(error))

        try:
            response = self._client.messages.parse(
                model=self._model,
                max_tokens=self._max_tokens,
                thinking={"type": "adaptive"},
                # 초안 생성은 사용자가 화면에서 기다리는 작업이라 지연이 품질보다 중요하다.
                output_config={"effort": "low"},
                system=system_prompt,
                messages=[{"role": "user", "content": json.dumps(context, ensure_ascii=False)}],
                output_format=output_schema,
            )
        except anthropic.APITimeoutError:
            return self._failure("AI 응답이 시간 내에 도착하지 않았습니다.")
        except anthropic.RateLimitError:
            return self._failure("AI 호출 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.")
        except anthropic.AuthenticationError:
            return self._failure("AI 인증에 실패했습니다. API 키 설정을 확인해 주세요.")
        except anthropic.APIStatusError as error:
            return self._failure(f"AI 서비스 오류가 발생했습니다. (status {error.status_code})")
        except anthropic.APIConnectionError:
            return self._failure("AI 서비스에 연결하지 못했습니다.")
        except ValidationError:
            # 요청은 정상이고 **응답**이 스키마를 못 맞춘 경우다. SDK가 클라이언트에서
            # 검증하며 던진다. 요청 구성 실패와 구분해야 원인을 오해하지 않는다.
            return self._failure(
                "AI 응답이 지정한 형식을 만족하지 않습니다. "
                "입력을 조금 더 구체적으로 적으면 개선될 수 있습니다."
            )
        except (TypeError, ValueError) as error:
            # SDK 시그니처 변경 등 요청 구성 실패. 기존 업무 기능까지 죽이지 않는다.
            return self._failure(f"AI 요청을 구성하지 못했습니다. ({type(error).__name__})")

        if getattr(response, "stop_reason", None) == "refusal":
            return self._failure("AI가 요청 처리를 거절했습니다.", response=response)

        parsed = getattr(response, "parsed_output", None)
        if parsed is None:
            return self._failure("AI 응답이 지정한 형식을 만족하지 않습니다.", response=response)

        return AIProviderResult(
            provider=PROVIDER_NAME,
            success=True,
            content=parsed.model_dump_json(),
            model_name=getattr(response, "model", self._model),
            input_tokens=_usage(response, "input_tokens"),
            output_tokens=_usage(response, "output_tokens"),
        )

    def _failure(self, message: str, response: object | None = None) -> AIProviderResult:
        """원시 SDK 응답을 그대로 담지 않는다. 정리된 메시지와 토큰 수만 남긴다."""
        return AIProviderResult(
            provider=PROVIDER_NAME,
            success=False,
            model_name=self._model,
            error_message=message,
            input_tokens=_usage(response, "input_tokens"),
            output_tokens=_usage(response, "output_tokens"),
        )


def _usage(response: object | None, field: str) -> int | None:
    usage = getattr(response, "usage", None)
    value = getattr(usage, field, None)
    return value if isinstance(value, int) else None
