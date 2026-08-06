"""Employee employment and daily-work status rules shared by API use cases."""

EMPLOYMENT_STATUSES = frozenset({"ACTIVE", "ON_LEAVE", "SCHEDULED", "RESIGNED"})
DAILY_WORK_STATUSES = (
    "WORKING",
    "REMOTE_WORK",
    "OUT_OF_OFFICE",
    "BUSINESS_TRIP",
    "ANNUAL_LEAVE",
    "MORNING_HALF",
    "AFTERNOON_HALF",
    "SICK_LEAVE",
    "TRAINING",
    "OTHER",
    "OFF_WORK",
    "ABSENT",
)
NON_WORKING_EMPLOYMENT_STATUSES = frozenset({"ON_LEAVE", "SCHEDULED", "RESIGNED"})
NORMAL_WORK_STATUSES = frozenset({"WORKING", "OFF_WORK"})
CHECK_IN_WORK_STATUSES = frozenset({"WORKING", "REMOTE_WORK", "OUT_OF_OFFICE", "BUSINESS_TRIP"})
REQUIRED_REASON_WORK_STATUSES = frozenset({"SICK_LEAVE", "ABSENT"})
REQUIRED_EMPLOYMENT_REASON_STATUSES = frozenset({"ON_LEAVE"})
PRIVATE_REASON_VIEWER_ROLES = frozenset({"ADMIN", "HR_MANAGER", "SUPER_ADMIN", "HR_ADMIN"})


def requires_reason(work_status: str) -> bool:
    return work_status in REQUIRED_REASON_WORK_STATUSES


def requires_employment_reason(employment_status: str) -> bool:
    return employment_status in REQUIRED_EMPLOYMENT_REASON_STATUSES


def supports_daily_work_status(employment_status: str) -> bool:
    return employment_status not in NON_WORKING_EMPLOYMENT_STATUSES
