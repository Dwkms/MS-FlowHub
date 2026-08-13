"""포스터 프롬프트는 DB에 있는 사실만 포함해야 한다."""

from app.domain.job_poster_prompt import build_job_poster_context, build_job_poster_prompt


def test_absent_optional_facts_are_omitted_from_context_and_prompt() -> None:
    context = build_job_poster_context(
        posting_title="백엔드 개발자 채용",
        posting_content="주요 업무: API 개발",
        department_name="개발팀",
        position_title="백엔드 개발자",
        headcount=2,
        employment_type="정규직",
        experience_label="경력 3년 이상",
        education_level=None,
        work_location=None,
        salary=None,
        application_deadline=None,
        apply_method=None,
        responsibilities="API 개발",
        required_skills="Python",
        preferred_skills=None,
        design_direction=None,
    )

    prompt = build_job_poster_prompt(context)

    assert "work_location" not in context
    assert "salary" not in context
    assert "근무지:" not in prompt
    assert "급여:" not in prompt
    assert "학력:" not in prompt
    assert "팀 소개" not in prompt
    assert "모집 인원: 2명" in prompt
