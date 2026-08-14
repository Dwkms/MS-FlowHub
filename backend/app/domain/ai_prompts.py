"""실제 LLM에 보낼 시스템 프롬프트.

AI의 역할은 "사실 생성"이 아니라 "주어진 사실의 문장화"다. 이 파일의 문구는 그 경계를
지키게 하는 1차 방어선이고, 2차는 Context에서 값을 아예 빼는 것, 3차는 스키마 검증이다
(docs/archive/AI_AUTOMATION_PLAN.md 9장).
"""

from app.domain.ai_provider import APPROVAL_DRAFT, JOB_POSTING_DRAFT

_COMMON_RULES = """\
너는 사내 업무 포털의 문서 초안 작성을 돕는다. 다음 규칙을 반드시 지킨다.

1. 입력으로 주어진 사실만 사용한다. 주어지지 않은 금액·날짜·수량·인원·급여·복리후생·
   회사 정책·자격증 요구사항·근무지·마감일·결재자를 절대 만들어내지 않는다.
2. 값이 없으면 그 값을 언급하는 문장을 아예 쓰지 않는다. 추정하거나 예시를 넣지 않는다.
3. 승인·반려 여부, 합격 여부처럼 사람이 판단할 사항을 문장에 담지 않는다.
4. 한국어 사내 문서 문체로 쓴다. 과장된 수식어와 이모지를 쓰지 않는다.
5. 지정된 JSON 스키마에 정확히 맞춰 출력한다. 스키마에 없는 필드를 추가하지 않는다.
6. 선택 필드에 쓸 근거가 입력에 없으면 빈 문자열로 둔다. 이미 다른 필드에 있는 정보나
   메타데이터로 대신 채우지 않는다. 비어 있는 편이 억지로 채운 것보다 낫다.
"""

_APPROVAL_RULES = """\
전자결재 품의 문서의 초안을 작성한다.

- title: 문서 제목. 부서와 목적이 드러나게 간결히.
- purpose: 요청 목적을 서술형 한 문단으로.
- details: 주요 내용. 입력에 금액·수량·시점이 있으면 그대로 반영하고, 없으면 생략한다.
- expected_effect: 승인 시 기대 효과. 확정되지 않은 성과를 단정하지 않는다.
"""

_JOB_POSTING_RULES = """\
채용공고 본문의 초안을 작성한다.

- 입력의 주요 업무·필수 역량·우대 사항은 이미 담당자가 작성한 내용이다. 없는 항목을
  새로 만들지 말고, 주어진 내용을 공고에 어울리는 문장으로 다듬는다.
- responsibilities·requirements·preferred_qualifications는 항목별 한 문장으로 쓴다.
- 급여·복리후생은 입력에 있을 때만 언급한다.
- closing_message에는 입력에 있는 마감일·지원 방법만 담는다.
- team_or_recruitment_description은 팀 소개가 입력되었을 때만 채운다. 없으면 빈 문자열로
  둔다. 부서명이나 요청자 이름 같은 이미 알려진 정보로 대신 채우지 않는다.
"""

_FEATURE_RULES = {
    APPROVAL_DRAFT: _APPROVAL_RULES,
    JOB_POSTING_DRAFT: _JOB_POSTING_RULES,
}


def build_system_prompt(feature_type: str) -> str:
    rules = _FEATURE_RULES.get(feature_type)
    if rules is None:
        raise ValueError(f"지원하지 않는 생성 유형입니다: {feature_type}")
    return f"{_COMMON_RULES}\n{rules}"
