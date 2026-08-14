RECRUITMENT_APPROVER_POSITION_KEYWORDS = ("파트장", "팀장", "부장", "이사", "대표")
NON_REQUESTABLE_DEPARTMENT_CODES = frozenset({"EXEC"})


def is_recruitment_approver(position: str) -> bool:
    return any(keyword in position for keyword in RECRUITMENT_APPROVER_POSITION_KEYWORDS)


def is_requestable_recruitment_department(department_code: str) -> bool:
    return department_code not in NON_REQUESTABLE_DEPARTMENT_CODES
