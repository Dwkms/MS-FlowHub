from functools import lru_cache
from typing import Literal
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
    ai_max_tokens: int = Field(default=8000, ge=256)
    ai_timeout_seconds: float = Field(default=15.0, gt=0)
    # 유료 API가 인증만 통과하면 눌리는 버튼 뒤에 있다. 정상 사용은 1인 하루 1~2회라
    # 아래 값에 걸리지 않는다. SUPER_ADMIN 외 일반 계정에는 전역 한도가 비용 방어선이다.
    ai_daily_limit_per_user: int = Field(default=5, ge=1)
    ai_daily_limit_global: int = Field(default=30, ge=1)
    # 채용 포스터 이미지 생성은 기존 Claude 텍스트 초안과 키·모델·timeout을 분리한다.
    # OPENAI_API_KEY는 서버에서만 읽고 Frontend 환경변수로 전달하지 않는다.
    image_ai_provider: Literal["disabled", "openai"] = "disabled"
    openai_api_key: str | None = None
    image_ai_model: str = "gpt-image-2"
    image_ai_size: str = "1024x1536"
    image_ai_quality: Literal["low", "medium", "high"] = "medium"
    image_ai_timeout_seconds: float = Field(default=120.0, gt=0)
    # 이미지 생성은 텍스트 초안보다 건당 비용이 커 별도 최근 24시간 한도를 둔다.
    # SUPER_ADMIN은 검수용 반복 생성을 위해 두 한도에서 제외한다.
    image_ai_daily_limit_per_user: int = Field(default=2, ge=1)
    image_ai_daily_limit_global: int = Field(default=5, ge=1)
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
