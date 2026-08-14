from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.api.dependencies import get_current_auth_user
from app.models.auth import EmployeeAccount
from app.models.organization import Employee
from app.scripts.seed_auth_accounts import sync_employee_accounts, sync_selected_employee_accounts


def test_inactive_linked_account_is_blocked(client: TestClient) -> None:
    session_factory = client.app.state.testing_session_factory
    with session_factory() as session:
        session.add(
            EmployeeAccount(
                id="account-inactive",
                auth_user_id="auth-inactive",
                employee_id="emp-ms0011",
                role="EMPLOYEE",
                is_active=False,
            )
        )
        session.commit()
    client.app.dependency_overrides[get_current_auth_user] = lambda: "auth-inactive"

    response = client.get("/api/v1/employees")

    assert response.status_code == 403


def test_auth_user_without_employee_account_is_blocked(client: TestClient) -> None:
    client.app.dependency_overrides[get_current_auth_user] = lambda: "auth-unlinked"

    response = client.get("/api/v1/employees")

    assert response.status_code == 403


def test_auth_seed_sync_is_idempotent(client: TestClient) -> None:
    session_factory = client.app.state.testing_session_factory
    with session_factory() as session:
        employees = session.scalars(select(Employee).order_by(Employee.employee_no)).all()
        auth_users = {employee.email: f"auth-{employee.id}" for employee in employees}

        sync_employee_accounts(session, auth_users, "test-password")
        session.commit()
        first_count = session.scalar(select(func.count()).select_from(EmployeeAccount))

        sync_employee_accounts(session, auth_users, "test-password")
        session.commit()
        second_count = session.scalar(select(func.count()).select_from(EmployeeAccount))
        super_admin = session.scalar(
            select(EmployeeAccount).where(EmployeeAccount.employee_id == "emp-ms0001")
        )

    assert first_count == len(employees)
    assert second_count == first_count
    assert super_admin is not None
    assert super_admin.role == "SUPER_ADMIN"


def test_selected_auth_sync_creates_qa_part_accounts(client: TestClient) -> None:
    session_factory = client.app.state.testing_session_factory
    employee_nos = {"MS0012", "MS0013", "MS0014"}
    with session_factory() as session:
        employees = session.scalars(
            select(Employee).where(Employee.employee_no.in_(employee_nos))
        ).all()
        auth_users = {employee.email: f"auth-{employee.id}" for employee in employees}

        sync_selected_employee_accounts(session, employee_nos, auth_users, "test-password")
        session.commit()
        employee_ids = [employee.id for employee in employees]
        accounts = session.scalars(
            select(EmployeeAccount).where(EmployeeAccount.employee_id.in_(employee_ids))
        ).all()

    assert len(accounts) == 3
    assert {account.role for account in accounts} == {"PART_ADMIN", "EMPLOYEE"}
    # QA파트장은 자기 파트만 관리하므로 팀장용 TEAM_ADMIN이 아니라 PART_ADMIN이다.
    qa_part_lead = next(account for account in accounts if account.employee_id == "emp-ms0047")
    assert qa_part_lead.role == "PART_ADMIN"


def test_cleanup_stops_when_test_account_has_business_data() -> None:
    """테스트 계정이 만든 업무 데이터가 남아 있으면 계정을 지우지 않고 멈춰야 한다.

    2026-08-14에 실제로 겪은 상황이다. E2E 최고관리자로 수동 검증하다 만든 채용 요청이
    공고·지원자까지 이어져 있었는데, 예전 스크립트는 그 결재 문서를 지우려다
    ForeignKeyViolation으로 죽으면서 계정을 남겼다.

    여기서는 DB에 붙지 않고 참조 검사 함수만 확인한다. 실제 삭제는 운영 Supabase를
    건드리므로 자동 테스트에서 실행하지 않는다.
    """
    from app.models.approval import ApprovalDocument
    from app.models.recruitment import RecruitmentRequest
    from app.scripts.cleanup_test_auth_accounts import (
        E2E_DOCUMENT_TITLE_PREFIX,
        RESTRICT_REFERENCES,
        RemainingReferenceError,
        find_remaining_references,
    )

    class _FakeSession:
        """참조가 있다고 답하는 가짜 세션. 첫 번째 항목만 1건으로 만든다."""

        def __init__(self) -> None:
            self.calls = 0

        def scalar(self, _statement) -> int:
            self.calls += 1
            return 1 if self.calls == 1 else 0

    remaining = find_remaining_references(_FakeSession(), ["emp-e2e-super-admin"])

    assert remaining, "참조가 남아 있으면 목록이 비어 있으면 안 된다"
    assert "1건" in remaining[0]
    # 오류 메시지를 만들 수 있어야 사람이 무엇을 고칠지 안다.
    assert str(RemainingReferenceError("\n".join(remaining)))

    # 검사 대상에 업무 데이터 테이블이 빠져 있으면 같은 사고가 반복된다.
    labels = {label for _, _, label in RESTRICT_REFERENCES}
    assert "recruitment_requests.requester_id" in labels
    assert "approval_documents.author_id" in labels
    assert "approval_histories.actor_id" in labels
    assert "ai_generations.created_by_id" in labels

    # 자동화 문서만 지우도록 접두사로 거른다.
    assert E2E_DOCUMENT_TITLE_PREFIX == "E2E 결재 "
    assert ApprovalDocument.title is not None
    assert RecruitmentRequest.approval_document_id is not None
