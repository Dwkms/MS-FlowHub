"""Seed employee FAQ entries. Safe to run repeatedly; existing rows are updated in place."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.manual import ManualFaq

# FAQ id_suffix -> 함께 안내할 매뉴얼 slug. 답변 아래 "자세히 보기"로 연결된다.
# 적절한 매뉴얼이 없으면 넣지 않는다. 관련 없는 매뉴얼을 걸면 안내가 오히려 헷갈린다.
RELATED_MANUAL_SLUGS = {
    "login-how": "login-and-password",
    "login-password-change": "login-and-password",
    "login-session-expired": "login-and-password",
    "employee-search": "employee-search",
    "employee-org-chart": "organization-chart",
    "attendance-change-status": "work-status-and-reason",
    "attendance-private-reason": "work-status-and-reason",
    "attendance-history": "work-status-and-reason",
    "attendance-leave-request": "work-status-and-reason",
    "approval-create": "approval-create-submit",
    "approval-attachment": "approval-create-submit",
    "approval-no-approve-button": "approval-decision-history",
    "approval-rejection-reason": "approval-decision-history",
    "recruitment-create": "recruitment-request-to-posting",
    "recruitment-posting-created": "recruitment-request-to-posting",
    "applicant-stage-change": "applicant-stage-management",
    "applicant-stage-rollback": "applicant-stage-management",
    "permission-missing-menu": "dashboard-overview",
    "permission-401": "login-and-password",
    "general-features": "dashboard-overview",
    # permission-403: 권한 부족 오류를 다루는 매뉴얼이 없어 연결하지 않는다.
}

# (id_suffix, category, question, answer)
FAQS = [
    (
        "login-how",
        "로그인·계정",
        "MS FlowHub에 로그인하려면 어떻게 하나요?",
        "회사에서 발급받은 이메일과 비밀번호를 입력해 로그인합니다.\n"
        "로그인이 완료되면 업무 홈으로 이동하며, 현재 계정의 역할과 소속에 따라"
        " 사용할 수 있는 기능이 표시됩니다.",
    ),
    (
        "login-password-change",
        "로그인·계정",
        "비밀번호는 어떻게 변경하나요?",
        "로그인 후 사용자 메뉴에서 비밀번호 변경 기능을 이용합니다.\n"
        "현재 비밀번호를 확인한 뒤 새 비밀번호를 입력하면 변경됩니다.",
    ),
    (
        "login-session-expired",
        "로그인·계정",
        "로그인이 풀렸어요.",
        "로그인 세션이 만료되었을 가능성이 있습니다.\n"
        "로그인 화면에서 다시 로그인한 뒤 이용하세요. 반복적으로 발생하면 관리자에게 문의하세요.",
    ),
    (
        "employee-search",
        "직원·조직",
        "다른 직원을 찾거나 검색하려면 어떻게 하나요?",
        "「직원 · 부서」 메뉴에서 이름, 사번 또는 이메일을 입력해 찾을 수 있습니다.\n"
        "부서, 재직 상태, 오늘의 근무 상태 필터를 함께 사용하면 원하는 직원을"
        " 더 빠르게 검색할 수 있습니다.",
    ),
    (
        "employee-org-chart",
        "직원·조직",
        "조직도는 어디에서 확인하나요?",
        "「직원 · 부서」 화면에서 「조직도 보기」를 선택하면"
        " 현재 회사의 부서와 직원 조직 관계를 확인할 수 있습니다.",
    ),
    (
        "attendance-change-status",
        "근태·휴가",
        "오늘의 근무 상태는 어디서 변경하나요?",
        "「직원 · 부서」에서 본인의 직원 상세 정보를 열고 「근무 상태 변경」을 선택합니다.\n"
        "근무 중, 재택근무, 외근, 출장, 휴가, 반차, 병가 등의 상태를 선택한 후 저장하면"
        " 해당 날짜에 반영됩니다.",
    ),
    (
        "attendance-private-reason",
        "근태·휴가",
        "병가·결근 사유는 다른 직원도 확인할 수 있나요?",
        "일반 직원에게는 공개 가능한 사유만 표시됩니다.\n"
        "비공개 상세 사유는 권한이 있는 관리자와 인사담당자만 확인할 수 있습니다.",
    ),
    (
        "attendance-history",
        "근태·휴가",
        "이전 근무 상태 변경 기록을 확인할 수 있나요?",
        "직원 상세의 변경 이력에서 확인할 수 있습니다.\n"
        "근무 상태가 실제로 변경된 경우 이전 상태와 변경된 상태, 변경자, 변경 시간이 기록됩니다.",
    ),
    (
        "approval-create",
        "전자결재",
        "전자결재 문서는 어떻게 작성하나요?",
        "「전자결재」 메뉴에서 「새 문서 작성」을 선택합니다.\n"
        "문서 제목과 내용을 작성한 뒤 저장하고 결재자에게 상신하면 됩니다.",
    ),
    (
        "approval-no-approve-button",
        "전자결재",
        "결재를 상신했는데 승인 버튼이 보이지 않아요.",
        "승인·반려 기능은 해당 문서의 지정 결재자 또는 처리 권한이 있는 관리자에게만 표시됩니다.\n"
        "본인이 작성한 문서는 원칙적으로 본인이 승인할 수 없습니다.",
    ),
    (
        "approval-rejection-reason",
        "전자결재",
        "반려된 결재의 이유는 어디에서 확인하나요?",
        "전자결재 문서의 처리 이력에서 반려 여부와 반려 의견을 확인할 수 있습니다.",
    ),
    (
        "recruitment-create",
        "채용 요청·ATS",
        "채용 요청은 어떻게 작성하나요?",
        "ATS Lite의 채용 요청 화면에서 모집 직무, 인원, 고용 형태, 경력 수준,"
        " 채용 사유와 주요 업무 등을 입력합니다.\n"
        "필요한 경우 채용 포스터를 첨부할 수 있습니다.",
    ),
    (
        "recruitment-posting-created",
        "채용 요청·ATS",
        "채용 요청을 작성하면 바로 공고가 생성되나요?",
        "아닙니다.\n"
        "작성한 채용 요청을 결재 상신하고 승인을 받아야 합니다."
        " 승인이 완료된 채용 요청을 기준으로 채용공고가 생성됩니다.",
    ),
    (
        "applicant-stage-change",
        "채용 요청·ATS",
        "지원자 전형 단계는 어떻게 변경하나요?",
        "「ATS Lite → 지원자 관리」에서 지원자를 선택한 후 현재 전형 단계를 변경합니다.\n\n"
        "현재 단계는 다음과 같이 관리됩니다.\n"
        "지원 접수 → 서류 검토 → 1차 면접 → 2차 면접 → 채용 확정 또는 불합격",
    ),
    (
        "applicant-stage-rollback",
        "채용 요청·ATS",
        "불합격한 지원자를 이전 단계로 되돌릴 수 있나요?",
        "현재 시스템에서는 채용 확정과 불합격을 종료 단계로 관리하므로"
        " 종료 후 이전 전형 단계로 변경할 수 없습니다.",
    ),
    (
        "permission-missing-menu",
        "권한",
        "다른 직원에게 보이는 메뉴나 기능이 제 화면에는 안 보여요.",
        "MS FlowHub는 직원의 역할과 소속에 따라 사용할 수 있는 메뉴와 기능이 다르게 표시됩니다.\n"
        "본인의 업무 범위에 포함되지 않는 메뉴는 화면에 나타나지 않습니다.",
    ),
    (
        "permission-403",
        "권한",
        "403 권한 부족 메시지가 표시됩니다.",
        "로그인은 정상적으로 되어 있지만 현재 계정에 해당 작업을 수행할 권한이 없는 경우입니다.\n"
        "필요한 업무가 맞다면 관리자 또는 인사담당자에게 문의하세요.",
    ),
    (
        "permission-401",
        "권한",
        "401 오류가 표시됩니다.",
        "로그인 정보가 없거나 세션이 만료된 경우 발생할 수 있습니다.\n다시 로그인한 뒤 이용하세요.",
    ),
    # display_order는 아래 목록 순서에서 나온다. 새 항목을 중간에 끼우면 기존 FAQ의 순번이
    # 모두 밀리므로, 추가 항목은 목록 끝에 붙인다.
    (
        "general-features",
        "일반",
        "MS FlowHub에서 어떤 기능을 사용할 수 있나요?",
        "업무 홈 대시보드, 직원·조직 조회와 조직도, 근태 기록, 전자결재,"
        " 채용 요청과 ATS Lite를 사용할 수 있습니다.\n"
        "표시되는 메뉴와 사용할 수 있는 기능은 계정의 역할과 소속에 따라 다릅니다.",
    ),
    (
        "attendance-leave-request",
        "근태·휴가",
        "연차·반차는 어떻게 신청하나요?",
        "별도의 신청서를 올리거나 사전 승인을 받는 절차는 없습니다.\n"
        "「직원 · 부서」에서 본인의 직원 상세를 열고 「근무 상태 변경」에서 연차 또는"
        " 오전·오후 반차를 선택해 저장하면 해당 날짜에 기록됩니다.",
    ),
    (
        "approval-attachment",
        "전자결재",
        "전자결재 문서에 파일을 첨부할 수 있나요?",
        "전자결재 문서는 파일 첨부를 지원하지 않습니다. 제목과 내용으로만 작성합니다.\n"
        "파일 첨부는 채용 요청의 채용 포스터에서만 사용할 수 있으며"
        " 전자결재 문서와는 다른 기능입니다.",
    ),
]


def seed_faqs(session: Session) -> int:
    """Insert or update FAQ rows by fixed id so repeated runs never duplicate."""
    for order, (suffix, category, question, answer) in enumerate(FAQS, start=1):
        faq_id = f"manual-faq-{suffix}"
        faq = session.scalar(select(ManualFaq).where(ManualFaq.id == faq_id))
        if faq is None:
            faq = ManualFaq(id=faq_id)
            session.add(faq)
        faq.category = category
        faq.question = question
        faq.answer = answer
        manual_slug = RELATED_MANUAL_SLUGS.get(suffix)
        faq.related_manual_id = f"manual-{manual_slug}" if manual_slug else None
        faq.display_order = order
        faq.is_published = True
    return len(FAQS)


def main() -> None:
    with SessionLocal() as session:
        count = seed_faqs(session)
        session.commit()
    print(f"Seeded {count} FAQ entries.")


if __name__ == "__main__":
    main()
