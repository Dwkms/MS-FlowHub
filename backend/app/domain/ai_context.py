"""AI Context 조립.

DB 세션을 받지 않는 **순수 함수**다. Service가 조회한 값을 넘겨받아 dict를 만든다.
그래야 DB 없이 "무엇이 AI에게 전달되는가"를 테스트할 수 있다.

여기가 개인정보 차단 지점이다. `EmployeeDetail`에는 이메일·사번·근태 사유·비공개 상세
사유가 함께 들어 있지만, 이 함수는 **명시적으로 받은 인자만** 담는다. 객체를 통째로
넘기지 않는 이유가 그것이다(docs/AI_AUTOMATION_PLAN.md 11장·19장).

값이 없으면 키 자체를 만들지 않는다. `None`을 넣어두면 AI가 "금액: 미정" 같은 문장을
쓸 여지가 생긴다. 주지 않은 사실은 존재조차 알리지 않는 것이 가장 확실한 차단이다.
"""

from datetime import date

# 프롬프트에 넣을 한국어 라벨. 프론트엔드 presentation.ts의 documentTypeLabels와 같은
# 값이지만, 백엔드가 AI에게 보낼 문구라 여기서 따로 갖는다.
DOCUMENT_TYPE_LABELS = {
    "GENERAL": "일반 품의",
    "RECRUITMENT_REQUEST": "채용 요청",
    "EXPENSE": "비용 품의",
    "QUOTATION_DISCOUNT": "견적 할인",
}


def _put(context: dict, key: str, value: object) -> None:
    """빈 값은 키를 만들지 않는다."""
    if value is None:
        return
    text = str(value).strip()
    if text:
        context[key] = text


def build_approval_context(
    *,
    author_name: str,
    position: str,
    department_name: str,
    drafted_on: date,
    document_type: str,
    purpose: str,
    main_content: str,
    job_title: str | None = None,
    team_name: str | None = None,
    amount: str | None = None,
    quantity: str | None = None,
    desired_date: str | None = None,
    extra_note: str | None = None,
) -> dict:
    """전자결재 초안용 Context.

    앞쪽 인자는 DB에서 온 사실, 뒤쪽은 사용자가 화면에서 채운 맥락이다. 금액·수량·시점은
    사용자가 입력했을 때만 Context에 들어가고, 그래야 §9의 "AI가 만들면 안 되는 값"이
    구조적으로 차단된다.
    """
    context: dict = {}
    _put(context, "author_name", author_name)
    _put(context, "position", position)
    _put(context, "job_title", job_title)
    _put(context, "department_name", department_name)
    _put(context, "team_name", team_name)
    _put(context, "drafted_on", drafted_on.isoformat())

    _put(context, "document_type", document_type)
    _put(context, "document_type_label", DOCUMENT_TYPE_LABELS.get(document_type))
    _put(context, "purpose", purpose)
    _put(context, "main_content", main_content)
    _put(context, "amount", amount)
    _put(context, "quantity", quantity)
    _put(context, "desired_date", desired_date)
    _put(context, "extra_note", extra_note)
    return context


def build_job_posting_context(
    *,
    position_title: str,
    headcount: int,
    employment_type: str,
    experience_level: str,
    department_name: str,
    requester_name: str,
    reason: str | None = None,
    responsibilities: str | None = None,
    required_skills: str | None = None,
    preferred_skills: str | None = None,
    desired_start_date: str | None = None,
    work_location: str | None = None,
    application_deadline: str | None = None,
    apply_method: str | None = None,
    team_intro: str | None = None,
    salary: str | None = None,
) -> dict:
    """채용공고 초안용 Context.

    `responsibilities`·`required_skills`·`preferred_skills`는 **이미 담당자가 작성한
    텍스트**다. AI가 없는 것을 만드는 게 아니라 공고 문장으로 다듬는다.

    근무 위치·마감일·지원 방법·급여는 DB에 없으므로 사용자가 입력했을 때만 들어간다.
    입력이 없으면 키가 없고, 따라서 AI가 "서울 본사" 같은 값을 지어낼 근거가 없다.
    """
    context: dict = {}
    _put(context, "position_title", position_title)
    _put(context, "headcount", f"{headcount}명")
    _put(context, "employment_type", employment_type)
    _put(context, "experience_level", experience_level)
    _put(context, "department_name", department_name)
    _put(context, "requester_name", requester_name)
    _put(context, "reason", reason)
    _put(context, "responsibilities", responsibilities)
    _put(context, "required_skills", required_skills)
    _put(context, "preferred_skills", preferred_skills)
    _put(context, "desired_start_date", desired_start_date)

    _put(context, "work_location", work_location)
    _put(context, "application_deadline", application_deadline)
    _put(context, "apply_method", apply_method)
    _put(context, "team_intro", team_intro)
    _put(context, "salary", salary)
    return context
