"""AX 도우미 고정 응답 룰 — 검색보다 먼저 평가된다.

두 룰 모두 자유 추론이 아니라 좁은 명시적 조건만 쓴다. 애매하면 발동시키지 않고
일반 검색으로 넘긴다. 과잉 발동으로 답할 수 있는 질문까지 막는 쪽이 더 나쁘기 때문이다.
설계 근거는 docs/archive/AX_FAQ_CHATBOT_PLAN.md 3장 참조.
"""

CONFIRMED = "CONFIRMED"
CANDIDATES = "CANDIDATES"
NO_MATCH = "NO_MATCH"
POLICY = "POLICY"
PERSONAL_DATA = "PERSONAL_DATA"

POLICY_ANSWER = (
    "아니요. 이 도우미는 등록된 매뉴얼과 FAQ에서 안내 문서를 찾아 보여줄 뿐이며,"
    " 결재 승인·반려나 지원자 합격·불합격 같은 업무 처리는 하지 않습니다.\n"
    "모든 업무 처리는 담당자가 직접 화면에서 수행합니다."
)

NO_MATCH_ANSWER = "관련 매뉴얼이나 FAQ를 찾지 못했습니다.\n인사팀 또는 관리자에게 문의해 주세요."

PERSONAL_DATA_ANSWER = (
    "이 항목은 도우미가 답변하지 않습니다.\n로그인한 본인 화면에서 직접 확인해 주세요."
)

CANDIDATES_ANSWER = "이 중에서 찾으시는 내용이 있나요?"

# "AI가 대신 처리해 주나요?"류. 주체와 행위가 함께 나올 때만 발동한다.
_POLICY_SUBJECTS = ("ai", "에이아이", "인공지능", "도우미", "챗봇", "봇이")
_POLICY_ACTIONS = ("대신", "자동으로", "알아서", "승인", "반려", "합격", "불합격", "처리해")

# 개인화·실시간 조회 질문. 1인칭 표현과 수량·현황 표현이 함께 나올 때만 발동한다.
_PERSONAL_SUBJECTS = ("제가", "내가", "제 ", "내 ", "나의", "저의", "우리", "본인")
_PERSONAL_QUANTITIES = ("몇 건", "몇건", "몇 명", "몇명", "누구", "현황", "목록", "얼마나")


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def is_policy_question(question: str) -> bool:
    """AI가 업무를 대신 처리하는지 묻는 질문인지."""
    text = question.lower()
    return _contains_any(text, _POLICY_SUBJECTS) and _contains_any(text, _POLICY_ACTIONS)


def is_personal_data_question(question: str) -> bool:
    """본인·부서의 실시간 업무 데이터를 묻는 질문인지(v1 범위 밖)."""
    text = question.lower()
    return _contains_any(text, _PERSONAL_SUBJECTS) and _contains_any(text, _PERSONAL_QUANTITIES)
