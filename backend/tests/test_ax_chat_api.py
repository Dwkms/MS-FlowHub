"""AX 도우미 회귀 테스트.

기획서 8장 하드 게이트 4개를 고정한다:
오답 0건 / 권한 없는 매뉴얼 노출 0건 / 정책 질문 우선 매칭 / 무관 질문 근거 없음.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.dependencies import get_authenticated_actor
from app.models.ax import AxChatLog
from app.models.manual import Manual, ManualCategory
from app.scripts.seed_faqs import seed_faqs
from app.scripts.seed_manuals import seed_manuals
from app.security.identity import ActorContext

# 기획서 2장 매핑표. 질문은 FAQ 원문이 아니라 직원이 실제로 칠 법한 표현으로 바꿨다.
# 원문을 그대로 넣으면 매칭이 자명해져서 회귀 테스트 가치가 없다.
CONFIRMED_CASES = [
    ("전자결재 어떻게 올려요?", "manual-faq-approval-create"),
    ("결재에 파일 첨부돼요?", "manual-faq-approval-attachment"),
    ("반려 사유 어디서 봐요?", "manual-faq-approval-rejection-reason"),
    ("조직도 어디 있어요", "manual-faq-employee-org-chart"),
    ("오늘 근무상태 변경하려면?", "manual-faq-attendance-change-status"),
    ("반차 어떻게 써요?", "manual-faq-attendance-leave-request"),
    ("예전 근태 기록 볼 수 있나요", "manual-faq-attendance-history"),
    ("채용요청하면 공고 바로 나가나요", "manual-faq-recruitment-posting-created"),
    ("지원자 전형 단계 변경", "manual-faq-applicant-stage-change"),
    ("불합격한 지원자 되돌릴 수 있나요", "manual-faq-applicant-stage-rollback"),
    ("로그인이 안돼요", "manual-faq-login-session-expired"),
    ("403 에러가 떠요", "manual-faq-permission-403"),
    ("메뉴가 안 보여요", "manual-faq-permission-missing-menu"),
]

# 정답 문서를 1위로 뽑지만 2위와 접전이라 확신하지 않는 질문들.
# 오답이 아니라 "후보 제시"로 떨어지는 것이 설계 의도다.
CANDIDATE_CASES = [
    "내가 쓴 문서 내가 승인할 수 있나요",
    "직원 찾는 방법",
    "병가 사유 남들이 보나요",
    "채용요청 작성 방법",
    "비밀번호 바꾸고 싶어요",
]

IRRELEVANT_QUESTIONS = [
    "오늘 점심 뭐 먹지",
    "주차장 어디에요",
    "택배 어디서 받나요",
    "회의실 예약은 어떻게 하나요",
    "커피머신 고장났어요",
    "연봉 인상은 언제인가요",
]


def set_actor(client: TestClient, role: str = "EMPLOYEE") -> None:
    client.app.dependency_overrides[get_authenticated_actor] = lambda: ActorContext(
        employee_id="emp-head", role=role, auth_user_id="auth-emp-head"
    )


@pytest.fixture
def ax_client(client: TestClient) -> TestClient:
    session_factory = client.app.state.testing_session_factory
    with session_factory() as session:
        seed_manuals(session)
        seed_faqs(session)
        session.commit()
    set_actor(client)
    return client


def ask(client: TestClient, question: str) -> dict:
    response = client.post("/api/v1/ax/chat", json={"question": question})
    assert response.status_code == 200, response.text
    return response.json()


def test_chat_requires_authentication(client: TestClient) -> None:
    assert client.post("/api/v1/ax/chat", json={"question": "로그인이 안돼요"}).status_code == 401


@pytest.mark.parametrize(("question", "expected_id"), CONFIRMED_CASES)
def test_confirmed_answers_cite_the_expected_document(
    ax_client: TestClient, question: str, expected_id: str
) -> None:
    payload = ask(ax_client, question)
    assert payload["result_type"] == "CONFIRMED", payload
    assert payload["source"]["doc_id"] == expected_id
    assert payload["answer"]


@pytest.mark.parametrize("question", CANDIDATE_CASES)
def test_close_calls_offer_candidates_instead_of_guessing(
    ax_client: TestClient, question: str
) -> None:
    """접전이면 확신하지 않는다. 틀린 답을 자신 있게 내는 것보다 낫다."""
    payload = ask(ax_client, question)
    assert payload["result_type"] == "CANDIDATES", payload
    assert payload["source"] is None
    assert 2 <= len(payload["candidates"]) <= 3


@pytest.mark.parametrize("question", IRRELEVANT_QUESTIONS)
def test_irrelevant_questions_never_guess(ax_client: TestClient, question: str) -> None:
    payload = ask(ax_client, question)
    assert payload["result_type"] == "NO_MATCH", payload
    assert payload["source"] is None
    assert payload["candidates"] == []


@pytest.mark.parametrize(
    "question",
    [
        "AI가 제 결재를 대신 승인해 주나요?",
        "챗봇이 지원자를 대신 합격시켜 줄 수 있나요",
        "AI가 알아서 반려해줘",
    ],
)
def test_policy_answer_wins_over_search(ax_client: TestClient, question: str) -> None:
    """정책 질문은 검색 점수에 따라 답이 흔들리면 안 되므로 검색보다 먼저 평가한다."""
    payload = ask(ax_client, question)
    assert payload["result_type"] == "POLICY", payload
    assert "하지 않습니다" in payload["answer"]


@pytest.mark.parametrize(
    "question",
    [
        "제가 승인해야 할 결재가 몇 건인가요",
        "우리 부서 오늘 근태 현황 알려줘",
        "제 상급자는 누구인가요",
    ],
)
def test_personal_data_questions_are_declined_with_guidance(
    ax_client: TestClient, question: str
) -> None:
    payload = ask(ax_client, question)
    assert payload["result_type"] == "PERSONAL_DATA", payload


def test_confirmed_answer_links_related_manual_and_route(ax_client: TestClient) -> None:
    payload = ask(ax_client, "반차 어떻게 써요?")
    assert payload["source"]["manual_slug"] == "work-status-and-reason"
    assert payload["route"] == "/employees"


def test_restricted_manual_never_reaches_a_regular_employee(ax_client: TestClient) -> None:
    """매뉴얼 9건이 모두 전체공개라 실데이터로는 재현할 수 없어 픽스처로 검증한다."""
    session_factory = ax_client.app.state.testing_session_factory
    with session_factory() as session:
        category = session.scalars(select(ManualCategory)).first()
        session.add(
            Manual(
                id="manual-secret-payroll",
                category_id=category.id,
                title="급여 지급 절차",
                slug="secret-payroll",
                summary="급여 지급 절차와 지급일 안내입니다.",
                content="급여 지급 절차는 매월 25일 기준으로 처리합니다. 급여 대장 확인 방법.",
                target_roles=["SUPER_ADMIN"],
                status="PUBLISHED",
            )
        )
        session.commit()

    set_actor(ax_client, "EMPLOYEE")
    payload = ask(ax_client, "급여 지급 절차 알려줘")
    assert "manual-secret-payroll" not in str(payload)

    set_actor(ax_client, "SUPER_ADMIN")
    payload = ask(ax_client, "급여 지급 절차 알려줘")
    assert payload["source"]["doc_id"] == "manual-secret-payroll"


def test_every_question_is_logged_with_candidates(ax_client: TestClient) -> None:
    ask(ax_client, "반차 어떻게 써요?")
    ask(ax_client, "오늘 점심 뭐 먹지")

    session_factory = ax_client.app.state.testing_session_factory
    with session_factory() as session:
        logs = {log.question_text: log for log in session.scalars(select(AxChatLog))}

    confirmed = logs["반차 어떻게 써요?"]
    assert confirmed.result_type == "CONFIRMED"
    assert confirmed.matched_id == "manual-faq-attendance-leave-request"
    # 상위 후보를 남겨야 실패 원인을 "순위 문제"와 "문서 부재"로 구분할 수 있다.
    assert 1 <= len(confirmed.top_candidates) <= 3
    assert confirmed.top_candidates[0]["score"] >= confirmed.top_candidates[-1]["score"]

    assert logs["오늘 점심 뭐 먹지"].result_type == "NO_MATCH"


def test_logs_do_not_store_who_asked(ax_client: TestClient) -> None:
    """46명 규모 조직에서 질문자 식별은 그 자체로 민감 정보다(기획서 7장)."""
    ask(ax_client, "병가 사유 남들이 보나요")
    assert not hasattr(AxChatLog, "employee_id")
