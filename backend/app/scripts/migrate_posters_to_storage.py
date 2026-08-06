"""One-time migration: upload existing local recruitment poster files to Supabase Storage.

Reads recruitment_requests.poster_stored_name from the DB, uploads the matching
local file under backend/data/uploads/recruitment-posters/ to the Storage bucket,
and leaves the local file untouched (delete it manually after verifying).
"""

from pathlib import Path

from sqlalchemy import text

from app.core.supabase_storage import POSTER_BUCKET, upload_object
from app.db.session import SessionLocal

_LOCAL_UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads" / "recruitment-posters"


def migrate_posters() -> None:
    with SessionLocal() as session:
        rows = session.execute(
            text(
                "select id, poster_stored_name, poster_content_type "
                "from recruitment_requests where poster_stored_name is not null"
            )
        ).fetchall()

    if not rows:
        print("No recruitment_requests reference a poster file. Nothing to migrate.")
        return

    for request_id, stored_name, content_type in rows:
        local_path = _LOCAL_UPLOAD_DIR / stored_name
        if not local_path.is_file():
            print(f"[skip] {request_id}: local file not found ({local_path})")
            continue
        content = local_path.read_bytes()
        upload_object(
            POSTER_BUCKET, stored_name, content, content_type or "application/octet-stream"
        )
        print(f"[ok] {request_id}: uploaded {stored_name} ({len(content)} bytes)")


if __name__ == "__main__":
    migrate_posters()
