/** 채용 요청 선택지. 백엔드 `app/domain/recruitment_options.py`와 값을 맞춘다. */

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
