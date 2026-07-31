from fastapi.testclient import TestClient


def create_draft(client: TestClient, title: str = "신규 장비 구매 품의") -> dict:
    response = client.post(
        "/api/v1/approvals",
        json={
            "title": title,
            "document_type": "GENERAL",
            "content": "개발 장비 구매를 요청합니다.",
            "department_id": "dept-product",
            "author_id": "emp-head",
            "approver_id": "emp-hr",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_update_and_list_draft(client: TestClient) -> None:
    draft = create_draft(client)

    update_response = client.patch(
        f"/api/v1/approvals/{draft['id']}",
        json={"actor_id": "emp-head", "title": "수정된 장비 구매 품의"},
    )
    list_response = client.get(
        "/api/v1/approvals",
        params={"employee_id": "emp-head", "search": "수정된", "status": "DRAFT"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["title"] == "수정된 장비 구매 품의"
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_admin_can_draft_for_another_department(client: TestClient) -> None:
    response = client.post(
        "/api/v1/approvals",
        json={
            "title": "영업팀 장비 구매 품의",
            "document_type": "GENERAL",
            "content": "영업팀에서 사용할 장비 구매를 요청합니다.",
            "department_id": "dept-sales",
            "author_id": "emp-head",
            "approver_id": "emp-hr",
        },
    )

    assert response.status_code == 201
    assert response.json()["department_id"] == "dept-sales"
    assert response.json()["author_name"] == "김민성"


def test_non_admin_cannot_draft_for_another_department(client: TestClient) -> None:
    response = client.post(
        "/api/v1/approvals",
        json={
            "title": "다른 부서 문서",
            "document_type": "GENERAL",
            "content": "다른 부서로 작성하는 문서입니다.",
            "department_id": "dept-sales",
            "author_id": "emp-hr",
            "approver_id": "emp-head",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "기안자의 소속 부서와 기안 부서가 다릅니다."


def test_admin_can_delete_pending_document_and_history(client: TestClient) -> None:
    response = client.post(
        "/api/v1/approvals",
        json={
            "title": "인사팀 결재 대기 문서",
            "document_type": "GENERAL",
            "content": "관리자 삭제 권한을 확인합니다.",
            "department_id": "dept-hr",
            "author_id": "emp-hr",
            "approver_id": "emp-sales",
        },
    )
    draft = response.json()
    client.post(
        f"/api/v1/approvals/{draft['id']}/submit",
        json={"actor_id": "emp-hr"},
    )

    delete_response = client.delete(
        f"/api/v1/approvals/{draft['id']}",
        params={"actor_id": "emp-head"},
    )
    get_response = client.get(f"/api/v1/approvals/{draft['id']}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_non_admin_cannot_delete_own_draft(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/approvals",
        json={
            "title": "인사팀 임시 문서",
            "document_type": "GENERAL",
            "content": "인사팀에서 작성한 임시 문서입니다.",
            "department_id": "dept-hr",
            "author_id": "emp-hr",
            "approver_id": "emp-sales",
        },
    )
    draft = create_response.json()
    forbidden_response = client.delete(
        f"/api/v1/approvals/{draft['id']}",
        params={"actor_id": "emp-hr"},
    )

    assert forbidden_response.status_code == 403
    assert forbidden_response.json()["detail"] == "관리자만 문서를 삭제할 수 있습니다."


def test_admin_lists_documents_from_all_employees(client: TestClient) -> None:
    response = client.post(
        "/api/v1/approvals",
        json={
            "title": "인사팀 전체 목록 확인 문서",
            "document_type": "GENERAL",
            "content": "관리자 목록 권한을 확인합니다.",
            "department_id": "dept-hr",
            "author_id": "emp-hr",
            "approver_id": "emp-sales",
        },
    )
    assert response.status_code == 201

    list_response = client.get("/api/v1/approvals", params={"employee_id": "emp-head"})

    assert list_response.status_code == 200
    assert list_response.json()[0]["author_id"] == "emp-hr"


def test_submit_and_approve_flow_updates_dashboard(client: TestClient) -> None:
    draft = create_draft(client)

    submit_response = client.post(
        f"/api/v1/approvals/{draft['id']}/submit",
        json={"actor_id": "emp-head", "comment": "검토 부탁드립니다."},
    )
    dashboard_before = client.get("/api/v1/dashboard", params={"employee_id": "emp-hr"}).json()
    approve_response = client.post(
        f"/api/v1/approvals/{draft['id']}/approve",
        json={"actor_id": "emp-hr", "comment": "승인합니다."},
    )
    dashboard_after = client.get("/api/v1/dashboard", params={"employee_id": "emp-hr"}).json()

    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "PENDING"
    assert dashboard_before["metrics"][0]["value"] == 1
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "APPROVED"
    assert dashboard_after["metrics"][0]["value"] == 0
    assert dashboard_after["recent_tasks"][0]["status"] == "승인"


def test_submit_and_reject_flow_requires_reason(client: TestClient) -> None:
    draft = create_draft(client, title="교육비 지원 품의")
    client.post(
        f"/api/v1/approvals/{draft['id']}/submit",
        json={"actor_id": "emp-head"},
    )

    empty_reason = client.post(
        f"/api/v1/approvals/{draft['id']}/reject",
        json={"actor_id": "emp-hr", "comment": ""},
    )
    rejected = client.post(
        f"/api/v1/approvals/{draft['id']}/reject",
        json={"actor_id": "emp-hr", "comment": "예산 근거를 보완해 주세요."},
    )

    assert empty_reason.status_code == 422
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "REJECTED"
    assert rejected.json()["decision_comment"] == "예산 근거를 보완해 주세요."


def test_invalid_status_transitions_are_blocked(client: TestClient) -> None:
    draft = create_draft(client)

    approve_draft = client.post(
        f"/api/v1/approvals/{draft['id']}/approve",
        json={"actor_id": "emp-hr"},
    )
    client.post(
        f"/api/v1/approvals/{draft['id']}/submit",
        json={"actor_id": "emp-head"},
    )
    client.post(
        f"/api/v1/approvals/{draft['id']}/approve",
        json={"actor_id": "emp-hr"},
    )
    approve_again = client.post(
        f"/api/v1/approvals/{draft['id']}/approve",
        json={"actor_id": "emp-hr"},
    )

    assert approve_draft.status_code == 409
    assert approve_again.status_code == 409


def test_only_designated_approver_can_decide(client: TestClient) -> None:
    draft = create_draft(client)
    client.post(
        f"/api/v1/approvals/{draft['id']}/submit",
        json={"actor_id": "emp-head"},
    )

    response = client.post(
        f"/api/v1/approvals/{draft['id']}/approve",
        json={"actor_id": "emp-sales-head"},
    )

    assert response.status_code == 403


def test_admin_can_approve_a_document_assigned_to_another_approver(client: TestClient) -> None:
    draft = create_draft(client)
    client.post(
        f"/api/v1/approvals/{draft['id']}/submit",
        json={"actor_id": "emp-head"},
    )

    response = client.post(
        f"/api/v1/approvals/{draft['id']}/approve",
        json={"actor_id": "emp-head", "comment": "관리자 승인"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
    assert response.json()["histories"][-1]["actor_id"] == "emp-head"
