from pathlib import Path


def get_poster_upload_directory() -> Path:
    """Return the local development directory used for recruitment poster files."""
    backend_root = Path(__file__).resolve().parents[2]
    directory = backend_root / "data" / "uploads" / "recruitment-posters"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_poster_path(stored_name: str) -> Path:
    """Resolve a generated storage name without accepting a user supplied path."""
    return get_poster_upload_directory() / Path(stored_name).name
