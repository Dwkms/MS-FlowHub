import pytest

from app.repositories.recruitment_repository import RecruitmentRepository


def request_payload(*, requester_id: str = "emp-product-head") -> dict[str, object]:
    return {
        "request_department_id": "dept-product",
        "requester_id": requester_id,
        "approver_id": "emp-hr",
        "position_title": "Backend Developer",
        "headcount": 1,
        "employment_type": "정규직",
        "experience_level": "신입/경력",
        "reason": "신규 기능 개발 인력이 필요합니다.",
        "responsibilities": "FastAPI 기반 API를 개발합니다.",
        "required_skills": "Python, SQL",
        "preferred_skills": "PostgreSQL",
        "desired_start_date": "2026-09-01",
    }


def create_and_submit(client) -> tuple[str, str]:
    created = client.post("/api/v1/recruitment-requests", json=request_payload())
    assert created.status_code == 201
    request_id = created.json()["id"]
    submitted = client.post(
        f"/api/v1/recruitment-requests/{request_id}/submit",
        json={"actor_id": "emp-product-head", "comment": "채용 요청 상신"},
    )
    assert submitted.status_code == 200
    return request_id, submitted.json()["approval_document_id"]


def test_department_head_can_create_recruitment_request(client) -> None:
    response = client.post("/api/v1/recruitment-requests", json=request_payload())

    assert response.status_code == 201
    assert response.json()["status"] == "DRAFT"


def test_employee_can_create_recruitment_request_for_any_department(client) -> None:
    payload = request_payload(requester_id="emp-sales")
    payload["request_department_id"] = "dept-sales"

    response = client.post("/api/v1/recruitment-requests", json=payload)

    assert response.status_code == 201
    assert response.json()["request_department_id"] == "dept-sales"


def test_submit_creates_linked_pending_approval(client) -> None:
    request_id, approval_document_id = create_and_submit(client)

    request = client.get(
        f"/api/v1/recruitment-requests/{request_id}", params={"employee_id": "emp-product-head"}
    )
    approval = client.get(f"/api/v1/approvals/{approval_document_id}")

    assert request.json()["status"] == "PENDING_APPROVAL"
    assert approval.json()["status"] == "PENDING"
    assert approval.json()["document_type"] == "RECRUITMENT_REQUEST"
    assert approval.json()["related_type"] == "RECRUITMENT_REQUEST"
    assert approval.json()["related_id"] == request_id


def test_requester_can_attach_poster_and_posting_includes_its_metadata(client) -> None:
    created = client.post("/api/v1/recruitment-requests", json=request_payload())
    request_id = created.json()["id"]

    uploaded = client.post(
        f"/api/v1/recruitment-requests/{request_id}/poster",
        params={"actor_id": "emp-product-head"},
        files={"poster": ("backend-poster.png", b"poster content", "image/png")},
    )
    downloaded = client.get(
        f"/api/v1/recruitment-requests/{request_id}/poster",
        params={"employee_id": "emp-product-head"},
    )
    submitted = client.post(
        f"/api/v1/recruitment-requests/{request_id}/submit",
        json={"actor_id": "emp-product-head"},
    )
    downloaded_as_approver = client.get(
        f"/api/v1/recruitment-requests/{request_id}/poster",
        params={"employee_id": "emp-hr"},
    )
    client.post(
        f"/api/v1/approvals/{submitted.json()['approval_document_id']}/approve",
        json={"actor_id": "emp-hr"},
    )
    postings = client.get("/api/v1/job-postings", params={"employee_id": "emp-hr"})

    assert uploaded.status_code == 200
    assert uploaded.json()["poster_original_name"] == "backend-poster.png"
    assert downloaded.status_code == 200
    assert downloaded.content == b"poster content"
    assert downloaded_as_approver.status_code == 200
    assert downloaded_as_approver.content == b"poster content"
    assert postings.json()[0]["poster_content_type"] == "image/png"
    assert postings.json()[0]["poster_original_name"] == "backend-poster.png"
    deleted = client.delete(
        f"/api/v1/recruitment-requests/{request_id}", params={"actor_id": "emp-head"}
    )
    assert deleted.status_code == 204


def test_only_requester_or_admin_can_attach_draft_poster(client) -> None:
    created = client.post("/api/v1/recruitment-requests", json=request_payload())
    request_id = created.json()["id"]

    response = client.post(
        f"/api/v1/recruitment-requests/{request_id}/poster",
        params={"actor_id": "emp-sales"},
        files={"poster": ("poster.pdf", b"poster", "application/pdf")},
    )

    assert response.status_code == 403


def test_approval_creates_job_posting_and_blocks_duplicate_processing(client) -> None:
    request_id, approval_document_id = create_and_submit(client)

    approved = client.post(
        f"/api/v1/approvals/{approval_document_id}/approve",
        json={"actor_id": "emp-hr", "comment": "승인합니다."},
    )
    duplicate_approval = client.post(
        f"/api/v1/approvals/{approval_document_id}/approve",
        json={"actor_id": "emp-hr"},
    )
    request = client.get(
        f"/api/v1/recruitment-requests/{request_id}", params={"employee_id": "emp-product-head"}
    )
    postings = client.get("/api/v1/job-postings", params={"employee_id": "emp-hr"})

    assert approved.status_code == 200
    assert duplicate_approval.status_code == 409
    assert request.json()["status"] == "POSTING_CREATED"
    assert request.json()["job_posting_id"] is not None
    assert len(postings.json()) == 1


def test_rejection_does_not_create_job_posting(client) -> None:
    request_id, approval_document_id = create_and_submit(client)

    rejected = client.post(
        f"/api/v1/approvals/{approval_document_id}/reject",
        json={"actor_id": "emp-hr", "comment": "채용 사유 보완이 필요합니다."},
    )
    request = client.get(
        f"/api/v1/recruitment-requests/{request_id}", params={"employee_id": "emp-product-head"}
    )
    postings = client.get("/api/v1/job-postings", params={"employee_id": "emp-hr"})

    assert rejected.status_code == 200
    assert request.json()["status"] == "REJECTED"
    assert request.json()["job_posting_id"] is None
    assert postings.json() == []


def test_unapproved_request_cannot_create_job_posting(client) -> None:
    created = client.post("/api/v1/recruitment-requests", json=request_payload())

    response = client.post(
        f"/api/v1/recruitment-requests/{created.json()['id']}/job-posting",
        params={"actor_id": "emp-hr"},
    )

    assert response.status_code == 409


def test_only_admin_can_delete_recruitment_request(client) -> None:
    created = client.post("/api/v1/recruitment-requests", json=request_payload())
    request_id = created.json()["id"]

    forbidden = client.delete(
        f"/api/v1/recruitment-requests/{request_id}", params={"actor_id": "emp-hr"}
    )
    deleted = client.delete(
        f"/api/v1/recruitment-requests/{request_id}", params={"actor_id": "emp-head"}
    )
    missing = client.get(
        f"/api/v1/recruitment-requests/{request_id}", params={"employee_id": "emp-head"}
    )

    assert forbidden.status_code == 403
    assert deleted.status_code == 204
    assert missing.status_code == 404


def test_admin_deletion_removes_linked_approval_and_job_posting(client) -> None:
    request_id, approval_document_id = create_and_submit(client)
    client.post(
        f"/api/v1/approvals/{approval_document_id}/approve",
        json={"actor_id": "emp-hr"},
    )

    deleted = client.delete(
        f"/api/v1/recruitment-requests/{request_id}", params={"actor_id": "emp-head"}
    )
    approval = client.get(f"/api/v1/approvals/{approval_document_id}")
    postings = client.get("/api/v1/job-postings", params={"employee_id": "emp-head"})

    assert deleted.status_code == 204
    assert approval.status_code == 404
    assert postings.json() == []


def test_existing_job_posting_cannot_be_created_again(client) -> None:
    request_id, approval_document_id = create_and_submit(client)
    client.post(
        f"/api/v1/approvals/{approval_document_id}/approve",
        json={"actor_id": "emp-hr"},
    )

    response = client.post(
        f"/api/v1/recruitment-requests/{request_id}/job-posting",
        params={"actor_id": "emp-hr"},
    )

    assert response.status_code == 409


def test_approval_transaction_rolls_back_when_posting_generation_fails(client, monkeypatch) -> None:
    request_id, approval_document_id = create_and_submit(client)

    def raise_error(*args, **kwargs):
        raise RuntimeError("posting generation failed")

    monkeypatch.setattr(RecruitmentRepository, "create_posting", raise_error)
    with pytest.raises(RuntimeError, match="posting generation failed"):
        client.post(
            f"/api/v1/approvals/{approval_document_id}/approve",
            json={"actor_id": "emp-hr"},
        )

    approval = client.get(f"/api/v1/approvals/{approval_document_id}")
    request = client.get(
        f"/api/v1/recruitment-requests/{request_id}", params={"employee_id": "emp-product-head"}
    )
    assert approval.json()["status"] == "PENDING"
    assert request.json()["status"] == "PENDING_APPROVAL"
