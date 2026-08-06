"""Create the private Supabase Storage bucket used for recruitment posters.

Idempotent: safe to run multiple times, does nothing if the bucket already exists.
"""

import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.core.supabase_storage import POSTER_BUCKET


def _storage_request(
    path: str, payload: dict[str, object] | None = None, *, method: str | None = None
) -> dict[str, object]:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SECRET_KEY must be configured.")
    request = Request(
        f"{settings.supabase_url.rstrip('/')}/storage/v1{path}",
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers={
            "apikey": settings.supabase_secret_key,
            "Authorization": f"Bearer {settings.supabase_secret_key}",
            "Content-Type": "application/json",
        },
        method=method or ("POST" if payload is not None else "GET"),
    )
    with urlopen(request, timeout=10) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def ensure_poster_bucket() -> None:
    try:
        _storage_request(f"/bucket/{POSTER_BUCKET}")
        print(f"Bucket already exists: {POSTER_BUCKET}")
        return
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="ignore")
        if "NoSuchBucket" not in body and '"404"' not in body:
            raise

    _storage_request(
        "/bucket",
        {
            "id": POSTER_BUCKET,
            "name": POSTER_BUCKET,
            "public": False,
            "file_size_limit": 5 * 1024 * 1024,
            "allowed_mime_types": ["image/jpeg", "image/png", "image/webp", "application/pdf"],
        },
    )
    print(f"Created bucket: {POSTER_BUCKET}")


if __name__ == "__main__":
    ensure_poster_bucket()
