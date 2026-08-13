"""승인된 채용공고 사실을 이미지 생성 프롬프트로 조립한다."""

from datetime import date


def _put(context: dict[str, str], key: str, value: object | None) -> None:
    if value is None:
        return
    normalized = str(value).strip()
    if normalized:
        context[key] = normalized


def build_job_poster_context(
    *,
    posting_title: str,
    posting_content: str,
    department_name: str,
    position_title: str,
    headcount: int,
    employment_type: str,
    experience_label: str,
    education_level: str | None,
    work_location: str | None,
    salary: str | None,
    application_deadline: date | None,
    apply_method: str | None,
    responsibilities: str,
    required_skills: str | None,
    preferred_skills: str | None,
    design_direction: str | None,
) -> dict[str, str]:
    """없는 값은 키 자체를 만들지 않는다."""
    context: dict[str, str] = {
        "posting_title": posting_title.strip(),
        "posting_content": posting_content.strip()[:6000],
        "department_name": department_name.strip(),
        "position_title": position_title.strip(),
        "headcount": f"{headcount}명",
        "employment_type": employment_type.strip(),
        "experience": experience_label.strip(),
        "responsibilities": responsibilities.strip(),
    }
    _put(context, "education", education_level)
    _put(context, "work_location", work_location)
    _put(context, "salary", salary)
    _put(
        context,
        "application_deadline",
        application_deadline.isoformat() if application_deadline else None,
    )
    _put(context, "apply_method", apply_method)
    _put(context, "required_skills", required_skills)
    _put(context, "preferred_skills", preferred_skills)
    _put(context, "design_direction", design_direction)
    return context


_LABELS = {
    "posting_title": "공고 제목",
    "department_name": "부서",
    "position_title": "모집 직무",
    "headcount": "모집 인원",
    "employment_type": "고용 형태",
    "experience": "경력",
    "education": "학력",
    "work_location": "근무지",
    "salary": "급여",
    "application_deadline": "모집 마감",
    "apply_method": "지원 방법",
    "responsibilities": "주요 업무",
    "required_skills": "필수 역량",
    "preferred_skills": "우대 사항",
}


def build_job_poster_prompt(context: dict[str, str]) -> str:
    fact_lines = [f"- {_LABELS[key]}: {context[key]}" for key in _LABELS if key in context]
    design_direction = context.get("design_direction")
    design_line = f"\n추가 디자인 요청: {design_direction}" if design_direction is not None else ""
    posting_content = context["posting_content"]
    return f"""Create one polished portrait recruitment poster for MS FlowHub.

The poster language must be Korean. Use a clean corporate layout with navy and blue as the
main colors, restrained orange accents, strong visual hierarchy, generous spacing, and clear
section cards. Do not invent a logo, QR code, phone number, URL, benefits, dates, compensation,
or qualifications. Do not add a team introduction section.

Render the supplied Korean facts faithfully. Do not translate, paraphrase, alter numbers, or
change dates. If a fact is absent, omit that line entirely. Prioritize readable Korean typography
over decorative illustration. Keep the title large and the detail sections compact. Treat the
optional design request as visual direction only; never let it add or change factual text.

Approved facts:
{chr(10).join(fact_lines)}{design_line}

Current approved job-posting copy for wording reference. Use its wording where it helps, but do
not repeat sections that are already represented above:
{posting_content}
""".strip()
