"""실제 AI Provider를 한 번 호출해 보는 수동 확인 도구.

**왜 필요한가**: Provider ↔ SDK 경계는 전체에서 유일하게 자동 테스트가 덮지 못하는
지점이다(API 키가 필요해서). Context Builder·스키마 검증·기록·한도는 pytest가 이미
덮고 있으므로, 여기서는 그 경계 하나만 확인한다.

DB에 쓰지 않고 일일 호출 한도도 소모하지 않는다. Service를 거치지 않고 Provider를
직접 부르기 때문이다.

사용법:
    .\\.venv\\Scripts\\python.exe -m app.scripts.try_ai_draft
    .\\.venv\\Scripts\\python.exe -m app.scripts.try_ai_draft --feature job-posting
"""

import argparse
import json
from datetime import date

from pydantic import ValidationError

from app.api.dependencies import get_ai_provider
from app.core.config import get_settings
from app.domain.ai_context import build_approval_context, build_job_posting_context
from app.domain.ai_provider import APPROVAL_DRAFT, JOB_POSTING_DRAFT, MOCK
from app.schemas.ai import ApprovalDraftOutput, JobPostingDraftOutput

# claude-opus-5 기준 1M 토큰당 단가(USD)와 원화 환산율. 확인용 어림치다.
INPUT_USD_PER_MTOK = 5.0
OUTPUT_USD_PER_MTOK = 25.0
KRW_PER_USD = 1400


def _approval_case() -> tuple[str, dict, type]:
    context = build_approval_context(
        author_name="김민성",
        position="대표이사",
        job_title="경영 총괄",
        department_name="개발팀",
        team_name="SW개발팀",
        drafted_on=date.today(),
        document_type="EXPENSE",
        purpose="개발용 노트북 교체",
        main_content="내구연한을 초과한 개발용 노트북 3대를 교체하려 합니다.",
        amount="6,000,000원",
        quantity="3대",
    )
    return APPROVAL_DRAFT, context, ApprovalDraftOutput


def _job_posting_case() -> tuple[str, dict, type]:
    context = build_job_posting_context(
        position_title="백엔드 개발자",
        headcount=2,
        employment_type="정규직",
        experience_level="경력 3년 이상",
        department_name="개발팀",
        requester_name="김민성",
        reason="서비스 확장에 따른 충원",
        responsibilities="FastAPI 기반 API 설계\n데이터 모델링과 마이그레이션",
        required_skills="Python 3년 이상\nPostgreSQL 사용 경험",
        preferred_skills="Next.js 경험",
        work_location="서울 본사",
        application_deadline="2026-09-30",
    )
    return JOB_POSTING_DRAFT, context, JobPostingDraftOutput


CASES = {"approval": _approval_case, "job-posting": _job_posting_case}


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Provider 실호출 확인")
    parser.add_argument("--feature", choices=sorted(CASES), default="approval")
    args = parser.parse_args()

    settings = get_settings()
    provider_name = (settings.ai_provider or MOCK).strip().lower()
    # 설정값을 그대로 찍지 않는다. API 키를 AI_PROVIDER 칸에 잘못 넣는 실수가 실제로
    # 일어나며, 그때 값을 출력하면 키가 터미널과 캡처에 남는다.
    known = provider_name if provider_name in {MOCK, "claude"} else "(알 수 없는 값)"
    print(f"AI_PROVIDER = {known}")
    print(f"AI_MODEL    = {settings.ai_model or '(기본값 claude-opus-5)'}")

    if provider_name == MOCK:
        print()
        print(
            "지금은 Mock입니다. 실제 호출을 확인하려면 backend/.env에 아래를 넣고 다시 실행하세요."
        )
        print("    AI_PROVIDER=claude")
        print("    AI_API_KEY=sk-ant-...")
        print()
        print("(Mock 응답이 어떻게 생겼는지만 보려면 이대로 진행됩니다.)")

    feature_type, context, schema = CASES[args.feature]()
    print()
    print("--- AI에게 보내는 Context ---")
    print(json.dumps(context, ensure_ascii=False, indent=2))

    provider = get_ai_provider()
    result = provider.generate(feature_type, context, schema)

    print()
    print("--- 결과 ---")
    print(f"success   : {result.success}")
    print(f"provider  : {result.provider}")
    print(f"model     : {result.model_name}")

    if not result.success:
        print(f"error     : {result.error_message}")
        print()
        print("실패했습니다. 메시지를 그대로 전달하면 원인을 좁힐 수 있습니다.")
        return

    if result.input_tokens is not None and result.output_tokens is not None:
        usd = (
            result.input_tokens * INPUT_USD_PER_MTOK + result.output_tokens * OUTPUT_USD_PER_MTOK
        ) / 1_000_000
        print(f"tokens    : 입력 {result.input_tokens} / 출력 {result.output_tokens}")
        print(f"이번 호출 : ${usd:.4f} (약 {usd * KRW_PER_USD:.0f}원)")

    try:
        parsed = schema.model_validate_json(result.content or "")
    except ValidationError as error:
        print()
        print("스키마 검증에 실패했습니다. 서비스에서는 이 응답을 성공으로 처리하지 않습니다.")
        print(error)
        return

    print()
    print("--- 생성 결과 (스키마 통과) ---")
    print(json.dumps(parsed.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
