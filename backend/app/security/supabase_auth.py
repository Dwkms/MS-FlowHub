"""Supabase access token을 검증해 사용자 ID를 얻습니다.

프론트엔드는 Supabase Auth로 직접 로그인하고 받은 token을 `Authorization: Bearer`로
보냅니다. 백엔드는 그 token이 **진짜 Supabase가 발급한 것인지** 스스로 확인해야 합니다.
확인 없이 믿으면 아무나 토큰을 만들어 보낼 수 있습니다.

검증 경로가 두 개인 이유:

1. **JWKS 검증(기본)** — Supabase의 공개키를 받아 서명을 로컬에서 검증합니다.
   네트워크 왕복이 없어 빠르고, 공개키는 `lru_cache`로 재사용합니다.
2. **Supabase API 조회(대체)** — 1번이 실패하면 Supabase에 직접 물어봅니다.
   키 교체 직후처럼 캐시된 공개키가 낡았을 때를 대비한 경로입니다.

2번이 있다고 검증이 느슨해지는 것은 아닙니다. 두 경로 모두 실패하면 401입니다.
"""

import json
import logging
from functools import lru_cache
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import jwt
from fastapi import HTTPException, status
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientError, PyJWTError

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


def get_supabase_auth_user_id(access_token: str) -> str:
    settings = get_settings()
    jwks_url = _get_jwks_url(settings)
    issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1"

    try:
        signing_key = get_jwk_client(jwks_url).get_signing_key_from_jwt(access_token)
        payload = jwt.decode(
            access_token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
            issuer=issuer,
            leeway=60,
        )
    except (PyJWKClientError, PyJWTError) as error:
        logger.warning("Supabase JWKS token verification failed: %s", error)
        return _get_user_id_from_supabase(access_token, settings)

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise _unauthorized()
    return user_id


def _get_jwks_url(settings: Settings) -> str:
    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase Auth 환경설정이 필요합니다.",
        )
    return (
        settings.supabase_jwks_url
        or f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    )


@lru_cache
def get_jwk_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_keys=True, lifespan=300, timeout=5)


def _get_user_id_from_supabase(access_token: str, settings: Settings) -> str:
    if not settings.supabase_publishable_key or not settings.supabase_url:
        raise _unauthorized()
    request = Request(
        f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
        headers={
            "apikey": settings.supabase_publishable_key,
            "Authorization": f"Bearer {access_token}",
        },
    )
    try:
        with urlopen(request, timeout=5) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        logger.warning("Supabase fallback token verification failed: %s", error)
        raise _unauthorized() from error

    user_id = payload.get("id")
    if not isinstance(user_id, str) or not user_id:
        raise _unauthorized()
    return user_id


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증이 필요합니다.")
