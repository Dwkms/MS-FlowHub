from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.api.dependencies import get_authenticated_actor
from app.models.manual import Manual, ManualCategory
from app.scripts.seed_manuals import seed_manuals
from app.security.identity import ActorContext


def set_actor(client: TestClient, role: str, employee_id: str = "emp-head") -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id=employee_id,
        role=role,
        auth_user_id=f"auth-{employee_id}",
    )


def create_category(client: TestClient) -> dict:
    set_actor(client, "SUPER_ADMIN")
    response = client.post(
        "/api/v1/manuals/categories",
        json={"name": "테스트 카테고리", "description": "매뉴얼 API 테스트", "display_order": 1},
    )
    assert response.status_code == 201
    return response.json()


def create_manual(client: TestClient, category_id: str, *, status: str = "PUBLISHED") -> dict:
    response = client.post(
        "/api/v1/manuals",
        json={
            "category_id": category_id,
            "title": "근태 상태 등록 안내",
            "summary": "오늘의 근무 상태를 등록하는 방법입니다.",
            "content": "직원 상세에서 오늘의 근무 상태를 선택하고 저장합니다.",
            "target_roles": ["SUPER_ADMIN", "HR_ADMIN", "TEAM_ADMIN", "EMPLOYEE"],
            "is_pinned": True,
            "status": status,
            "assets": [
                {
                    "asset_type": "IMAGE",
                    "file_url": "/manuals/attendance.svg",
                    "alt_text": "근태 요약",
                }
            ],
        },
    )
    assert response.status_code == 201
    return response.json()


def test_manual_list_search_filter_and_detail(client: TestClient) -> None:
    category = create_category(client)
    manual = create_manual(client, category["id"])
    set_actor(client, "EMPLOYEE", "emp-sales")

    list_response = client.get(
        "/api/v1/manuals", params={"search": "근태", "category_id": category["id"]}
    )
    detail_response = client.get(f"/api/v1/manuals/{manual['slug']}")

    assert list_response.status_code == 200
    assert list_response.json()[0]["is_pinned"] is True
    assert list_response.json()[0]["thumbnail_url"] == "/manuals/attendance.svg"
    assert detail_response.status_code == 200
    assert detail_response.json()["assets"][0]["asset_type"] == "IMAGE"


def test_draft_is_hidden_from_read_only_roles(client: TestClient) -> None:
    category = create_category(client)
    manual = create_manual(client, category["id"], status="DRAFT")
    set_actor(client, "EMPLOYEE", "emp-sales")

    assert client.get("/api/v1/manuals").json() == []
    assert client.get(f"/api/v1/manuals/{manual['slug']}").status_code == 404


def test_hr_admin_can_update_and_delete_manual(client: TestClient) -> None:
    category = create_category(client)
    manual = create_manual(client, category["id"])
    set_actor(client, "HR_ADMIN", "emp-hr")

    update_response = client.patch(
        f"/api/v1/manuals/{manual['slug']}",
        json={"title": "수정된 근태 안내", "is_pinned": False},
    )
    delete_response = client.delete(f"/api/v1/manuals/{manual['slug']}")

    assert update_response.status_code == 200
    assert update_response.json()["title"] == "수정된 근태 안내"
    assert delete_response.status_code == 204


def test_team_admin_and_employee_cannot_manage_manuals(client: TestClient) -> None:
    category = create_category(client)
    manual = create_manual(client, category["id"])
    set_actor(client, "TEAM_ADMIN", "emp-sales-head")

    team_update = client.patch(f"/api/v1/manuals/{manual['slug']}", json={"title": "차단"})
    set_actor(client, "EMPLOYEE", "emp-sales")
    employee_delete = client.delete(f"/api/v1/manuals/{manual['slug']}")

    assert team_update.status_code == 403
    assert employee_delete.status_code == 403


def test_manual_seed_is_idempotent(client: TestClient) -> None:
    session_factory = client.app.state.testing_session_factory
    with session_factory() as session:
        seed_manuals(session)
        session.commit()
        seed_manuals(session)
        session.commit()
        category_count = session.scalar(select(func.count()).select_from(ManualCategory))
        manual_count = session.scalar(select(func.count()).select_from(Manual))

    assert category_count == 7
    assert manual_count == 15
