"""테스트 전용 계정과 그 계정이 만든 **자동화 산출물만** 지웁니다.

E2E는 실제 Supabase에 붙어 돌기 때문에, 끝난 뒤 남긴 계정을 지워야 직원 목록과
대시보드 지표가 오염되지 않습니다. 그런데 그 계정으로 화면을 조작하면 결재·채용·AI 기록
같은 **업무 데이터**가 함께 생깁니다. 그것까지 지우면 시연용 데이터가 사라집니다.

그래서 이 스크립트는 두 가지를 구분합니다.

    자동화 산출물   제목이 "E2E 결재 "로 시작하는 결재 문서. 지웁니다.
    업무 데이터     채용 요청이 연결돼 있거나 제목이 일반적인 문서. **건드리지 않습니다.**

업무 데이터가 남아 있으면 계정을 지울 수 없습니다(대부분의 FK가 RESTRICT). 그때는
연쇄 삭제로 밀어붙이지 않고 **어떤 테이블에 몇 건이 남았는지 출력하고 중단**합니다.
사람이 보고 "이 데이터를 지울지, 다른 직원에게 넘길지" 정해야 하는 문제이기 때문입니다.

2026-08-14에 실제로 겪은 상황입니다. E2E 최고관리자로 수동 검증하다 만든 채용 요청이
공고·지원자까지 이어져 있었고, 예전 버전은 그 문서를 지우려다 ForeignKeyViolation으로
죽으면서 계정을 남겼습니다. 증상과 대응은 TROUBLESHOOTING.md에 있습니다.
"""

import sys

from sqlalchemy import delete, func, or_, select

from app.db.session import SessionLocal
from app.models.ai_generation import AiGeneration
from app.models.approval import ApprovalDocument, ApprovalHistory
from app.models.auth import EmployeeAccount
from app.models.organization import Employee
from app.models.recruitment import Applicant, ApplicantStageHistory, RecruitmentRequest
from app.scripts.seed_auth_accounts import _admin_request, _existing_auth_users

TEST_EMAILS = (
    "e2e-employee@msflowhub.test",
    "e2e-super-admin@msflowhub.test",
    "auth-test-inactive@msflowhub.test",
)
E2E_TEST_EMAILS = TEST_EMAILS[:2]

#: E2E가 만드는 결재 문서의 제목 접두사. 이 접두사가 붙은 것만 자동으로 지운다.
E2E_DOCUMENT_TITLE_PREFIX = "E2E 결재 "

#: 직원을 RESTRICT로 참조하는 자리. 계정을 지우기 전에 여기가 전부 비어 있어야 한다.
#: 새 테이블이 직원을 참조하게 되면 여기에 추가한다.
RESTRICT_REFERENCES = (
    (RecruitmentRequest, RecruitmentRequest.requester_id, "recruitment_requests.requester_id"),
    (RecruitmentRequest, RecruitmentRequest.approver_id, "recruitment_requests.approver_id"),
    (ApprovalDocument, ApprovalDocument.author_id, "approval_documents.author_id"),
    (ApprovalDocument, ApprovalDocument.approver_id, "approval_documents.approver_id"),
    (ApprovalHistory, ApprovalHistory.actor_id, "approval_histories.actor_id"),
    (AiGeneration, AiGeneration.created_by_id, "ai_generations.created_by_id"),
    (Applicant, Applicant.created_by_id, "applicants.created_by_id"),
    (ApplicantStageHistory, ApplicantStageHistory.actor_id, "applicant_stage_histories.actor_id"),
)


class RemainingReferenceError(RuntimeError):
    """업무 데이터가 남아 있어 계정을 지울 수 없을 때 던진다."""


def find_remaining_references(session, employee_ids: list[str]) -> list[str]:
    """계정 삭제를 막고 있는 참조를 테이블별로 센다.

    비어 있으면 삭제해도 안전하다는 뜻이다.
    """
    remaining: list[str] = []
    for model, column, label in RESTRICT_REFERENCES:
        count = session.scalar(
            select(func.count()).select_from(model).where(column.in_(employee_ids))
        )
        if count:
            remaining.append(f"{label}: {count}건")
    return remaining


def cleanup_test_auth_accounts(
    target_emails: tuple[str, ...] = TEST_EMAILS,
) -> tuple[list[str], list[str]]:
    """테스트 계정과 자동화 산출물만 지운다.

    업무 데이터가 연결돼 있으면 아무것도 지우지 않고 `RemainingReferenceError`를 던진다.
    """
    with SessionLocal() as session:
        employees = session.scalars(select(Employee).where(Employee.email.in_(target_emails))).all()
        employee_ids = [employee.id for employee in employees]
        if not employee_ids:
            return [], []

        # 자동화가 만든 결재 문서만 지운다. 이력은 CASCADE로 함께 사라진다.
        # 제목 접두사로 거르므로, 사람이 화면에서 만든 문서는 남는다.
        session.execute(
            delete(ApprovalDocument).where(
                ApprovalDocument.title.startswith(E2E_DOCUMENT_TITLE_PREFIX),
                or_(
                    ApprovalDocument.author_id.in_(employee_ids),
                    ApprovalDocument.approver_id.in_(employee_ids),
                ),
            )
        )
        session.flush()

        # 남은 참조가 있으면 연쇄 삭제하지 않고 멈춘다. 무엇을 지울지는 사람이 정한다.
        remaining = find_remaining_references(session, employee_ids)
        if remaining:
            session.rollback()
            raise RemainingReferenceError(
                "테스트 계정이 만든 업무 데이터가 남아 있어 계정을 지우지 않았습니다.\n  "
                + "\n  ".join(remaining)
                + "\n\n업무 데이터를 보존하려면 해당 레코드의 작성자를 실제 직원으로 옮긴 뒤"
                " 다시 실행하세요. 자세한 대응은 TROUBLESHOOTING.md를 참고하세요."
            )

        session.execute(
            delete(EmployeeAccount).where(EmployeeAccount.employee_id.in_(employee_ids))
        )
        session.execute(delete(Employee).where(Employee.id.in_(employee_ids)))
        session.commit()

    deleted_auth_user_ids: list[str] = []
    auth_users_by_email = _existing_auth_users()
    for email in target_emails:
        auth_user_id = auth_users_by_email.get(email)
        if auth_user_id is None:
            continue
        _admin_request(f"/auth/v1/admin/users/{auth_user_id}", method="DELETE")
        deleted_auth_user_ids.append(auth_user_id)

    return [employee.email for employee in employees], deleted_auth_user_ids


def main() -> None:
    target_emails = E2E_TEST_EMAILS if "--e2e-only" in sys.argv else TEST_EMAILS
    try:
        emails, auth_user_ids = cleanup_test_auth_accounts(target_emails)
    except RemainingReferenceError as error:
        print(f"정리를 중단했습니다.\n\n{error}")
        raise SystemExit(1) from error
    print(f"Removed {len(emails)} test employees and {len(auth_user_ids)} Auth users.")


if __name__ == "__main__":
    main()
