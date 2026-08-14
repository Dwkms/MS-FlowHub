"""채용 요청에 적용하는 두 가지 자격 규칙.

이 파일에는 DB도 HTTP도 없습니다. 문자열을 받아 참·거짓만 돌려주는 순수 규칙이라
Service에서 가져다 쓰고 테스트도 값만 넣어 확인할 수 있습니다.
"""

# 결재자로 지정할 수 있는 직책 키워드.
#
# `employees.position`에 "파트장", "개발팀장", "대표이사"처럼 자유로운 문자열이 들어 있어서
# 정확히 일치가 아니라 **포함**으로 판정합니다. "개발팀장"에 "팀장"이 들어 있으므로 통과합니다.
#
# 주의: 포함 판정이라 순서나 부분 문자열에 걸리기 쉽습니다. 실제로 2026-08-14 이전에는
# "파트장"이 빠져 있었는데, "파트장"이라는 글자 안에 "팀장"이 없어서 파트장이 결재자
# 후보에서 조용히 걸러지고 있었습니다. 조직상 파트장은 팀원의 상급자이므로 추가했습니다.
RECRUITMENT_APPROVER_POSITION_KEYWORDS = ("파트장", "팀장", "부장", "이사", "대표")

# 채용 요청을 낼 수 없는 부서.
# EXEC(경영진)는 대표이사 1명뿐인 내부 참조용 부서라 채용 요청의 주체가 될 수 없습니다.
NON_REQUESTABLE_DEPARTMENT_CODES = frozenset({"EXEC"})


def is_recruitment_approver(position: str) -> bool:
    """이 직책을 결재자로 지정할 수 있는가.

    같은 규칙이 프론트엔드 `frontend/src/lib/approver-policy.ts`에도 복제돼 있습니다.
    한쪽만 고치면 화면에서는 선택되는데 서버가 422로 막는 상태가 되므로 항상 함께 고칩니다.
    """
    return any(keyword in position for keyword in RECRUITMENT_APPROVER_POSITION_KEYWORDS)


def is_requestable_recruitment_department(department_code: str) -> bool:
    """이 부서가 채용 요청을 낼 수 있는가."""
    return department_code not in NON_REQUESTABLE_DEPARTMENT_CODES
