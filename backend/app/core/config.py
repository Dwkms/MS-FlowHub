from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_postgres_url(url: str) -> str:
    """Use the project's Psycopg 3 SQLAlchemy dialect for Supabase URIs."""
    if url.startswith("postgresql://"):
        url = f"postgresql+psycopg://{url.removeprefix('postgresql://')}"
    elif url.startswith("postgres://"):
        url = f"postgresql+psycopg://{url.removeprefix('postgres://')}"

    parsed = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parsed.query) if key != "pgbouncer"]
    return urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment)
    )


class Settings(BaseSettings):
    app_name: str = "MS FlowHub"
    database_url: str | None = None
    migration_database_url: str | None = None
    ai_provider: str = "mock"
    ai_api_key: str | None = None
    ai_model: str | None = None
    discount_approval_threshold: float = Field(default=10, ge=0, le=100)
    frontend_origin: str = "http://localhost:3000"
    supabase_url: str | None = None
    supabase_publishable_key: str | None = None
    supabase_secret_key: str | None = None
    supabase_jwks_url: str | None = None
    auth_seed_default_password: str | None = None
    e2e_auth_employee_password: str | None = None
    e2e_auth_super_admin_password: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def data_source(self) -> str:
        return "supabase"

    @property
    def frontend_origins(self) -> list[str]:
        origins = [self.frontend_origin]
        local_origins = {"http://localhost:3000", "http://127.0.0.1:3000"}
        if self.frontend_origin in local_origins:
            origins.extend(local_origins - {self.frontend_origin})
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
