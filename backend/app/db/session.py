from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings, normalize_postgres_url

settings = get_settings()


def get_database_url() -> str:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be set to the Supabase PostgreSQL connection string.")
    return normalize_postgres_url(settings.database_url)


engine = create_engine(
    get_database_url(),
    connect_args={"prepare_threshold": None},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def check_database_connection() -> bool:
    try:
        with engine.connect():
            return True
    except SQLAlchemyError:
        return False


def get_db_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
