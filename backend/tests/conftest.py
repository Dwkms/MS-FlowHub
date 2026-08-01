from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_database_health
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app
from app.models import approval, notification, organization, recruitment  # noqa: F401
from app.models.organization import Department, Employee
from app.repositories.organization_repository import OrganizationRepository


def seed_workflow_test_identities(session: Session) -> None:
    """Keep approval/recruitment fixtures independent from production organization seed data."""
    for department_id, code in (("dept-product", "PRODUCT"), ("dept-sales", "SALES")):
        session.add(
            Department(
                id=department_id,
                code=code,
                name=code.title(),
                display_order=90,
            )
        )
    for employee_id, number, role, department_id in (
        ("emp-head", "TEST001", "ADMIN", "dept-product"),
        ("emp-hr", "TEST002", "HR_MANAGER", "dept-hr"),
        ("emp-sales", "TEST003", "SALES_REP", "dept-sales"),
        ("emp-sales-head", "TEST004", "DEPARTMENT_HEAD", "dept-sales"),
        ("emp-product-head", "TEST005", "DEPARTMENT_HEAD", "dept-product"),
    ):
        session.add(
            Employee(
                id=employee_id,
                employee_no=number,
                name="김민성" if employee_id == "emp-head" else employee_id,
                email=f"{employee_id}@test.local",
                role=role,
                department_id=department_id,
                position="인사팀장" if employee_id == "emp-hr" else "Tester",
                job_title="Test fixture",
            )
        )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    with testing_session() as session:
        OrganizationRepository(session).seed_sample_organization()
        seed_workflow_test_identities(session)
        session.commit()

    def override_session() -> Generator[Session, None, None]:
        with testing_session() as session:
            yield session

    test_app = create_app(verify_database_on_startup=False)
    test_app.dependency_overrides[get_db_session] = override_session
    test_app.dependency_overrides[get_database_health] = lambda: True
    with TestClient(test_app) as test_client:
        yield test_client
    test_app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
