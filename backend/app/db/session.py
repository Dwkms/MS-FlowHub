from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base

settings = get_settings()
_backend_root = Path(__file__).resolve().parents[2]
_local_data_dir = _backend_root / "data"
_local_database_path = _local_data_dir / "ms_flowhub.db"


def get_database_url() -> str:
    if settings.database_url:
        return settings.database_url
    return f"sqlite:///{_local_database_path.as_posix()}"


def _create_engine():
    database_url = get_database_url()
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    database_engine = create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
    if database_url.startswith("sqlite"):
        event.listen(
            database_engine,
            "connect",
            lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"),
        )
    return database_engine


engine = _create_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def check_database_connection() -> bool:
    try:
        with engine.connect():
            return True
    except SQLAlchemyError:
        return False


def initialize_local_database() -> None:
    if settings.database_url:
        return

    from app.models import approval, notification, organization, recruitment  # noqa: F401
    from app.repositories.organization_repository import OrganizationRepository

    _local_data_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        OrganizationRepository(session).seed_sample_organization()
        session.commit()


def get_db_session() -> Generator[Session, None, None]:
    initialize_local_database()
    with SessionLocal() as session:
        yield session
