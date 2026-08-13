"""채용 요청 선택지와 사람이 읽는 표기 조립.

자유 입력이던 항목을 코드값으로 좁힌다. 담당자가 "정규직"/"정규"/"풀타임"을 제각각 치면
그 값이 그대로 공고 본문과 AI 프롬프트로 흘러가기 때문이다.

선택지는 `Literal`을 단일 출처로 두고 튜플은 거기서 파생시킨다. 목록과 검증 타입이
따로 놀면 한쪽만 고쳐도 아무 데서도 걸리지 않는다.

**기존 데이터는 코드값이 아니다.** 이 칼럼들은 자유 입력으로 먼저 운영됐고 "Junior",
"신입/경력" 같은 값이 남아 있다. 그래서 표기 함수는 모르는 값을 만나면 버리지 않고
원문을 그대로 돌려준다. 신규 입력만 코드값으로 제한한다.
"""

from typing import Final, Literal, get_args

EmploymentType = Literal["정규직", "계약직", "인턴", "파트타임", "프리랜서"]
EducationLevel = Literal["학력무관", "고졸 이상", "초대졸 이상", "대졸 이상", "석사 이상"]
ApplyMethod = Literal["이메일", "잡코리아", "사람인", "고용24"]
ExperienceLevel = Literal["NEW", "EXPERIENCED", "ANY"]

EMPLOYMENT_TYPES: Final[tuple[str, ...]] = get_args(EmploymentType)
EDUCATION_LEVELS: Final[tuple[str, ...]] = get_args(EducationLevel)
APPLY_METHODS: Final[tuple[str, ...]] = get_args(ApplyMethod)
EXPERIENCE_LEVELS: Final[tuple[str, ...]] = get_args(ExperienceLevel)

EXPERIENCE_NEW: Final = "NEW"
EXPERIENCE_EXPERIENCED: Final = "EXPERIENCED"
EXPERIENCE_ANY: Final = "ANY"

#: 경력 년수 상한. 그 이상은 한 칸으로 묶는다.
EXPERIENCE_YEARS_MAX: Final = 20

_EXPERIENCE_LABELS: Final[dict[str, str]] = {
    EXPERIENCE_NEW: "신입",
    EXPERIENCE_ANY: "경력무관",
}


def describe_experience(level: str, years_min: int | None) -> str:
    """공고 본문·화면·AI Context에 넣을 경력 표기를 만든다.

    코드값을 그대로 내보내면 공고에 "EXPERIENCED"가 박히고 AI도 그 단어를 받는다.
    """
    if level == EXPERIENCE_EXPERIENCED:
        if years_min is None:
            return "경력"
        return f"경력 {min(years_min, EXPERIENCE_YEARS_MAX)}년 이상"
    # 모르는 값은 자유 입력 시절의 원문이다. 버리지 않고 그대로 보여준다.
    return _EXPERIENCE_LABELS.get(level, level)
