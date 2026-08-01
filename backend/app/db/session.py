from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings, normalize_postgres_url


def get_database_url() -> str:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be set to the Supabase PostgreSQL connection string.")
    return normalize_postgres_url(settings.database_url)


def create_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    """Create a session factory only when a runtime DB session is actually needed."""
    engine = create_engine(
        normalize_postgres_url(database_url) if database_url else get_database_url(),
        connect_args={"prepare_threshold": None},
        pool_pre_ping=True,
    )
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return create_session_factory()


def SessionLocal() -> Session:
    return get_session_factory()()


def check_database_connection() -> bool:
    try:
        with SessionLocal() as session:
            with session.connection():
                return True
    except (RuntimeError, SQLAlchemyError):
        return False


def get_db_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
