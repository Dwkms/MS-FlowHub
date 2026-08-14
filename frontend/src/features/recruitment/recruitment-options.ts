/**
 * 채용 요청 화면의 선택지 목록.
 *
 * **주의: 같은 목록이 백엔드에도 있습니다.**
 * `backend/app/domain/recruitment_options.py`가 `Literal`로 같은 값을 정의하고 검증합니다.
 * 한쪽에만 항목을 추가하면 화면에는 뜨는데 저장할 때 **런타임 422**가 납니다.
 * 반대로 백엔드에만 추가하면 사용자가 고를 방법이 없습니다.
 *
 * 자유 입력이 아니라 목록으로 좁힌 이유: 담당자가 "정규직"/"정규"/"풀타임"을 제각각 치면
 * 그 값이 그대로 공고 본문과 AI 프롬프트로 흘러갑니다.
 *
 * 경력만 구조가 다릅니다. `신입`·`경력무관`은 년수가 없고 `경력`일 때만 최소 년수를
 * 함께 받습니다. 화면에서는 라디오 3개 + 조건부 드롭다운으로 표현합니다.
 */

export const EMPLOYMENT_TYPES = ["정규직", "계약직", "인턴", "파트타임", "프리랜서"] as const;
export const EDUCATION_LEVELS = [
  "학력무관",
  "고졸 이상",
  "초대졸 이상",
  "대졸 이상",
  "석사 이상",
] as const;
export const APPLY_METHODS = ["이메일", "잡코리아", "사람인", "고용24"] as const;

export type EmploymentType = (typeof EMPLOYMENT_TYPES)[number];
export type EducationLevel = (typeof EDUCATION_LEVELS)[number];
export type ApplyMethod = (typeof APPLY_METHODS)[number];
export type ExperienceLevel = "NEW" | "EXPERIENCED" | "ANY";

/** 경력 최소 년수 상한. 그 위는 서버가 한 칸으로 묶는다. */
export const EXPERIENCE_YEARS_MAX = 20;
export const EXPERIENCE_YEARS = Array.from({ length: EXPERIENCE_YEARS_MAX }, (_, index) => index + 1);

export const EXPERIENCE_CHOICES: { value: ExperienceLevel; label: string }[] = [
  { value: "NEW", label: "신입" },
  { value: "EXPERIENCED", label: "경력" },
  { value: "ANY", label: "경력무관" },
];
