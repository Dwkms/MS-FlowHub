"""Supabase Storage REST client for recruitment poster files.

Uses the same urllib-based request pattern as app/security/supabase_auth.py
and app/scripts/seed_auth_accounts.py instead of adding a new SDK dependency.
"""

from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.core.config import get_settings

POSTER_BUCKET = "recruitment-posters"


class StorageObjectNotFoundError(Exception):
    pass


class StorageError(Exception):
    pass


def _object_url(bucket: str, object_path: str) -> str:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise StorageError("SUPABASE_URL and SUPABASE_SECRET_KEY must be configured.")
    encoded_path = quote(object_path, safe="")
    return f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{encoded_path}"


def _headers(*, content_type: str | None = None, upsert: bool = False) -> dict[str, str]:
    settings = get_settings()
    headers = {
        "apikey": settings.supabase_secret_key or "",
        "Authorization": f"Bearer {settings.supabase_secret_key}",
    }
    if content_type:
        headers["Content-Type"] = content_type
    if upsert:
        headers["x-upsert"] = "true"
    return headers


def upload_object(bucket: str, object_path: str, content: bytes, content_type: str) -> None:
    request = Request(
        _object_url(bucket, object_path),
        data=content,
        headers=_headers(content_type=content_type, upsert=True),
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:  # noqa: S310
            response.read()
    except HTTPError as error:
        raise StorageError(f"Supabase Storage upload failed for {object_path}.") from error


def _is_not_found(error: HTTPError) -> bool:
    body = error.read().decode("utf-8", errors="ignore")
    return "NoSuchKey" in body or "NoSuchBucket" in body or '"404"' in body


def download_object(bucket: str, object_path: str) -> bytes:
    request = Request(_object_url(bucket, object_path), headers=_headers(), method="GET")
    try:
        with urlopen(request, timeout=15) as response:  # noqa: S310
            return response.read()
    except HTTPError as error:
        if error.code == 404 or _is_not_found(error):
            raise StorageObjectNotFoundError(object_path) from error
        raise StorageError(f"Supabase Storage download failed for {object_path}.") from error


def delete_object(bucket: str, object_path: str) -> None:
    request = Request(_object_url(bucket, object_path), headers=_headers(), method="DELETE")
    try:
        with urlopen(request, timeout=15) as response:  # noqa: S310
            response.read()
    except HTTPError as error:
        if error.code == 404 or _is_not_found(error):
            return
        raise StorageError(f"Supabase Storage delete failed for {object_path}.") from error
