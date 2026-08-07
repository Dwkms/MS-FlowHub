from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.api.dependencies import get_authenticated_actor
from app.models.manual import ManualFaq
from app.scripts.seed_faqs import seed_faqs
from app.security.identity import ActorContext


def set_actor(client: TestClient, role: str, employee_id: str = "emp-head") -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id=employee_id,
        role=role,
        auth_user_id=f"auth-{employee_id}",
    )


def seed(client: TestClient) -> None:
    session_factory = client.app.state.testing_session_factory
    with session_factory() as session:
        seed_faqs(session)
        session.commit()


def test_faq_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/faqs").status_code == 401


def test_every_authenticated_role_can_read_faqs(client: TestClient) -> None:
    seed(client)
    for role in ("SUPER_ADMIN", "HR_ADMIN", "TEAM_ADMIN", "EMPLOYEE"):
        set_actor(client, role)
        response = client.get("/api/v1/faqs")
        assert response.status_code == 200, role
        payload = response.json()
        assert len(payload) == 18
        assert payload[0]["display_order"] < payload[-1]["display_order"]
        assert {"id", "category", "question", "answer"} <= set(payload[0])


def test_unpublished_faq_is_hidden(client: TestClient) -> None:
    seed(client)
    session_factory = client.app.state.testing_session_factory
    with session_factory() as session:
        faq = session.scalar(select(ManualFaq).where(ManualFaq.id == "manual-faq-login-how"))
        faq.is_published = False
        session.commit()

    set_actor(client, "EMPLOYEE")
    questions = [item["id"] for item in client.get("/api/v1/faqs").json()]
    assert "manual-faq-login-how" not in questions
    assert len(questions) == 17


def test_faq_seed_is_idempotent(client: TestClient) -> None:
    session_factory = client.app.state.testing_session_factory
    with session_factory() as session:
        seed_faqs(session)
        session.commit()
        seed_faqs(session)
        session.commit()
        total = session.scalar(select(func.count()).select_from(ManualFaq))

    assert total == 18
