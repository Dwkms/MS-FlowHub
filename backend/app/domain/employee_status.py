"""직원의 재직 상태와 하루 단위 근무 상태 규칙.

상태값을 **여기 한 곳에 모아 두는 이유**가 있습니다. 같은 목록을 Service와 화면과 테스트가
각자 들고 있으면 상태를 하나 추가할 때 한 곳만 고치고 넘어가게 됩니다. 그러면 API는 받아주는데
화면에는 안 뜨거나, 반대로 화면에서 고른 값을 서버가 422로 막는 일이 생깁니다.

상태의 **의미와 전이 규칙**은 `docs/DOMAIN.md`에, **컬럼 정의**는 `docs/DATA_MODEL.md`에 있습니다.
"""

# 재직 상태 — 사람이 회사와 맺고 있는 관계입니다. 하루 단위로 바뀌지 않습니다.
#   ACTIVE    재직 중
#   ON_LEAVE  휴직
#   SCHEDULED 입사 예정 (아직 출근 전)
#   RESIGNED  퇴직
EMPLOYMENT_STATUSES = frozenset({"ACTIVE", "ON_LEAVE", "SCHEDULED", "RESIGNED"})

# 일일 근무 상태 — "오늘 이 사람이 어떻게 일하고 있나"입니다. 날짜마다 하나씩 기록됩니다.
# frozenset이 아니라 tuple인 이유: 화면의 드롭다운이 이 순서를 그대로 씁니다.
# 집합으로 두면 순서가 보장되지 않아 목록이 매번 뒤바뀝니다.
DAILY_WORK_STATUSES = (
    "WORKING",  # 근무 중
    "REMOTE_WORK",  # 재택근무
    "OUT_OF_OFFICE",  # 외근
    "BUSINESS_TRIP",  # 출장
    "ANNUAL_LEAVE",  # 휴가
    "MORNING_HALF",  # 오전 반차
    "AFTERNOON_HALF",  # 오후 반차
    "SICK_LEAVE",  # 병가
    "TRAINING",  # 교육
    "OTHER",  # 기타
    "OFF_WORK",  # 퇴근
    "ABSENT",  # 결근
)

# 재직 상태가 이 중 하나이면 "오늘 어떻게 일하는가"를 기록할 대상이 아닙니다.
# 휴직·입사예정·퇴직자에게 근무 상태를 남기면 근태 통계가 오염됩니다.
NON_WORKING_EMPLOYMENT_STATUSES = frozenset({"ON_LEAVE", "SCHEDULED", "RESIGNED"})

# 사유 없이 그냥 기록해도 되는 평범한 상태입니다.
NORMAL_WORK_STATUSES = frozenset({"WORKING", "OFF_WORK"})

# 출근으로 인정하는 상태 — 자리에 없어도 업무 중인 경우를 포함합니다.
CHECK_IN_WORK_STATUSES = frozenset({"WORKING", "REMOTE_WORK", "OUT_OF_OFFICE", "BUSINESS_TRIP"})

# 공개 사유를 반드시 입력해야 하는 상태.
# 병가와 결근은 나중에 확인이 필요해질 수 있어 최소한의 사유를 남기게 했습니다.
REQUIRED_REASON_WORK_STATUSES = frozenset({"SICK_LEAVE", "ABSENT"})

# 재직 상태를 이걸로 바꿀 때 사유가 필요합니다.
REQUIRED_EMPLOYMENT_REASON_STATUSES = frozenset({"ON_LEAVE"})

# 비공개 사유(`private_note`)를 볼 수 있는 역할.
#
# 두 가지 어휘가 섞여 있는 것은 오타가 아닙니다. 이 프로젝트에는 역할 값이 두 벌 있습니다.
#   employee_accounts.role  SUPER_ADMIN / HR_ADMIN / ...   ← 실제 권한 판정에 쓰는 값
#   employees.role          ADMIN / HR_MANAGER / ...       ← Seed가 채우는 별개 값
# 어느 쪽이 들어와도 막히지 않도록 둘 다 받습니다. 자세한 배경은 docs/DOMAIN.md 참고.
#
# TEAM_ADMIN(팀장)과 PART_ADMIN(파트장)은 **일부러 빠져 있습니다.** 관리 범위를 갖는 것과
# 팀원의 병가 사유를 읽는 것은 다른 문제입니다.
PRIVATE_REASON_VIEWER_ROLES = frozenset({"ADMIN", "HR_MANAGER", "SUPER_ADMIN", "HR_ADMIN"})


def requires_reason(work_status: str) -> bool:
    """이 근무 상태로 바꿀 때 공개 사유 입력이 필수인가."""
    return work_status in REQUIRED_REASON_WORK_STATUSES


def requires_employment_reason(employment_status: str) -> bool:
    """이 재직 상태로 바꿀 때 사유 입력이 필수인가."""
    return employment_status in REQUIRED_EMPLOYMENT_REASON_STATUSES


def supports_daily_work_status(employment_status: str) -> bool:
    """이 재직 상태인 직원에게 일일 근무 상태를 기록해도 되는가.

    퇴직자에게 "오늘 근무 중"을 남길 수 없게 막는 것이 목적입니다.
    """
    return employment_status not in NON_WORKING_EMPLOYMENT_STATUSES
