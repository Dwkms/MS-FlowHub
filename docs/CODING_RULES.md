# Coding Rules

실제 코드에서 이미 지키고 있는 규칙만 적었습니다. 구조 설명은 [`ARCHITECTURE.md`](ARCHITECTURE.md).

## 공통

- 전체 재작성 대신 필요한 부분만 고칩니다. 기존 동작을 깨지 않는 최소 변경이 우선입니다.
- 기존 유틸·타입·컴포넌트·Service·Repository를 먼저 찾아 재사용합니다.
- 새 파일은 역할이 분명할 때만 만듭니다.
- 환경변수와 API 키를 코드에 직접 쓰지 않습니다.
- 임시 코드, 디버그 로그, 미사용 import를 남기지 않습니다.
- 축약 문법, 과도한 추상화, 역할이 너무 큰 함수·클래스를 피합니다.
- 예외를 전부 삼키지 않고 사용자 오류와 내부 오류를 구분합니다.

## Backend

**계층 책임을 섞지 않습니다.**

| 계층 | 넣을 것 | 넣지 말 것 |
|---|---|---|
| Router (`api/`) | 요청 수신, 의존성 주입, 응답 반환 | 업무 규칙, 직접 쿼리 |
| Service | 업무 규칙, 상태 전이, 권한 판정, 트랜잭션 | 원시 SQL |
| Repository | SQLAlchemy 조회·저장 | 업무 판단 |
| Domain (`domain/`) | 순수 규칙·상수·Provider 계약 | DB·HTTP 의존 |

- SQLAlchemy는 2.0 방식(`select()`)과 **동기 Session**을 씁니다. 옛 `session.query()`와
  비동기 DB 코드는 별도 요청이 없으면 도입하지 않습니다.
- ORM 모델과 Pydantic 스키마를 분리합니다.
- 승인·반려·확정 같은 상태 변경 규칙은 Service에 둡니다.
- 여러 데이터 변경이 하나의 업무이면 하나의 트랜잭션으로 처리합니다.
- 프론트엔드가 보낸 금액·할인액·합계는 백엔드에서 다시 계산합니다. 부동소수점 오차를 고려합니다.
- 선택지·상태값은 한 곳을 단일 출처로 두고 파생시킵니다
  (예: `domain/recruitment_options.py`가 `Literal`에서 `get_args`로 목록을 만듭니다).
- DB 스키마 변경은 반드시 Alembic migration으로 기록합니다. Supabase 대시보드의 수동 변경에
  의존하지 않습니다. 신규 컬럼은 기존 데이터와 호환되도록 nullable을 우선 검토합니다.
- Seed는 반복 실행해도 중복 생성되지 않게 작성합니다.

**AI 관련**

- AI 호출은 공통 Provider(`domain/ai_provider.py`)만 거칩니다.
- Provider는 원시 문자열을 반환하고 검증은 Service가 합니다.
- AI 결과를 업무 결정으로 자동 반영하지 않습니다. 상태를 바꾸지 않습니다.
- AI 실패가 핵심 업무 저장을 실패시키지 않게 합니다 (`200 + success:false` 패턴).
- Context에 없는 값은 키 자체를 만들지 않습니다. `None`을 넣으면 AI가 지어냅니다.
- 자세한 제약은 [`AI_DESIGN.md`](AI_DESIGN.md)와 [`AI_AUTOMATION_PLAN.md`](AI_AUTOMATION_PLAN.md).

## Frontend

- 업무 로직을 `page.tsx`나 UI 컴포넌트에 몰아넣지 않습니다. 기능 로직은 `features/`에 둡니다.
- API 호출은 `lib/api-client.ts`를 거치고, 기능별 호출은 `features/*/api.ts`에 모읍니다.
  같은 요청을 여러 컴포넌트에서 중복 구현하지 않습니다.
- 불필요한 중복 API 호출을 만들지 않습니다.
- 타입은 `src/types/`에 두고 백엔드 스키마와 이름을 맞춥니다.
- 스타일은 `app/globals.css`의 시맨틱 클래스와 CSS 변수를 씁니다. Tailwind 유틸리티 클래스는
  이 프로젝트의 방식이 아닙니다 ([`ARCHITECTURE.md`](ARCHITECTURE.md#frontend-계층) 참고).
- 프론트엔드는 Supabase 업무 테이블에 직접 접근하지 않습니다. 로그인만 예외입니다.
- TypeScript 오류 없이 작성합니다.

## 검증

변경 범위에 해당하는 것만 실행하면 됩니다.

```powershell
# Backend
cd backend
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m alembic current

# Frontend
cd frontend
npm run lint; npm run typecheck; npm run build
```

- DB를 바꿨으면 migration 생성·적용, downgrade 가능 여부, Seed 중복, FK·상태값 제약을 확인합니다.
- Playwright E2E(`frontend/e2e/`)는 실제 Supabase에 접속하므로 **수동 실행 전용**입니다.
  CI에서 자동 실행되지 않습니다.
- 검증하지 못한 항목은 보고에 이유를 적습니다. 실패한 상태를 완료로 보고하지 않습니다.

## 문서 반영

작업 성격에 따라 해당 문서만 갱신합니다. 같은 내용을 여러 문서에 복사하지 않습니다.

오류는 **겪은 그 자리에서** `TROUBLESHOOTING.md`에 적습니다. 증상 → 원인 → 판별 → 해결
순서로 쓰고, 작업 중이던 다른 문서에 적어 두지 않습니다. 나중에 같은 증상을 만난 사람이
찾는 곳은 `TROUBLESHOOTING.md` 한 곳입니다.

| 바뀐 것 | 갱신할 문서 |
|---|---|
| 무엇을 했는지(이력) | `UPDATELOG.md` — 최신 날짜가 위 |
| 구현 상태가 달라짐 | [`CURRENT_STATE.md`](CURRENT_STATE.md) |
| 데이터 모델 | [`DATA_MODEL.md`](DATA_MODEL.md) |
| API | [`API_SPEC.md`](API_SPEC.md) |
| 업무 규칙 | [`DOMAIN.md`](DOMAIN.md) |
| 구조·배포 | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| 겪은 오류와 해결 | `TROUBLESHOOTING.md` — 루트의 별도 파일입니다. README 안이 아닙니다 |
| 설계 판단의 근거 | [`DECISIONS.md`](DECISIONS.md) |
| 에이전트가 항상 지킬 규칙 | `AGENTS.md`와 `CLAUDE.md` **양쪽 모두**. 두 파일은 내용이 같아야 합니다 |
