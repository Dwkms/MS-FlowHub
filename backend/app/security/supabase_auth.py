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
