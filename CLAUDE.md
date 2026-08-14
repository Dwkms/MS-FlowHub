# MS FlowHub — Agent Guide

> **`AGENTS.md`와 `CLAUDE.md`는 내용이 같아야 합니다.** Codex는 `AGENTS.md`를,
> Claude Code는 `CLAUDE.md`를 자동으로 읽기 때문에 양쪽 모두에 규칙이 있어야 합니다.
> 한쪽을 고치면 다른 쪽에 그대로 복사하세요.

전자결재를 중심으로 직원·조직, 근태, 채용을 연결한 사내 업무 시스템입니다.
가상 회사 MS의 직원 46명을 기준으로 만든 취업 포트폴리오 프로젝트이며 Render에 실제 배포돼 있습니다.

**FastAPI + Next.js + Supabase PostgreSQL.** Feature Freeze는 2026-08-13에 해제됐습니다.

## Context Map — 작업 전에 해당 문서를 먼저 읽습니다

이 파일에는 핵심 규칙만 있습니다. **상세는 아래 문서에 있고, 필요한 것을 능동적으로 열어 봐야 합니다.**
전부 읽지는 마세요. 작업 종류에 맞는 것만 봅니다.

| 하려는 일 | 먼저 볼 문서 |
|---|---|
| 무엇이 되고 무엇이 안 되는지 | [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md) |
| 이 **기능**을 왜 만들었는지 | [`docs/PLAN.md`](docs/PLAN.md) — 기능별·시간순 |
| 시스템 구조·인증 흐름·배포 | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| 업무 규칙·권한·상태 전이 | [`docs/DOMAIN.md`](docs/DOMAIN.md) |
| 테이블·컬럼·관계 | [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) |
| 엔드포인트 확인·추가 | [`docs/API_SPEC.md`](docs/API_SPEC.md) |
| 코드 작성 규칙·검증 명령 | [`docs/CODING_RULES.md`](docs/CODING_RULES.md) |
| 이 **구조·기술**을 왜 골랐는지 | [`docs/DECISIONS.md`](docs/DECISIONS.md) — 설계 결정 기록 |
| 배포·Render 설정 | [`docs/DEPLOYMENT_PLAN.md`](docs/DEPLOYMENT_PLAN.md) |
| AI 기능 제약 | [`docs/AI_DESIGN.md`](docs/AI_DESIGN.md) |
| 겪은 오류와 해결 | [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) |
| 과거에 무엇을 했는지 | [`UPDATELOG.md`](UPDATELOG.md) |

예시 — 직원관리 기능을 고친다면:
`DOMAIN.md`의 직원·근태 절 → `DATA_MODEL.md`의 해당 테이블 →
`backend/app/services/employee_service.py`와 `frontend/src/features/employees/` 순으로 봅니다.

## 코드 규칙

- **최소 변경.** 전체 재작성 대신 필요한 부분만 고치고 기존 UI·동작을 유지합니다.
- **재사용 우선.** 새로 만들기 전에 기존 유틸·타입·컴포넌트·Service·Repository를 찾습니다.
- **계층 책임 분리.** Router는 요청·응답만, 업무 규칙은 Service, DB 접근은 Repository.
- **권한은 서버에서 판정.** 화면 표시로만 막지 않습니다.
- **프론트엔드는 Supabase 업무 테이블에 직접 접근하지 않습니다.** 로그인만 예외입니다.
- **DB 스키마 변경은 Alembic migration으로 기록합니다.** 대시보드 수동 변경에 의존하지 않습니다.
- **AI는 상태를 바꾸지 않습니다.** 공통 Provider만 거치고, AI 실패가 업무 저장을 막지 않게 합니다.
- **비밀값을 코드에 쓰지 않습니다.** `SUPABASE_SECRET_KEY`·`DATABASE_URL`·AI 키를 `NEXT_PUBLIC_*`에
  절대 넣지 않습니다.
- **같은 정책이 백엔드와 프론트에 복제된 곳이 있습니다.** 결재자 자격(`recruitment_policy.py` ↔
  `lib/approver-policy.ts`), 채용 선택지(`recruitment_options.py` ↔ `recruitment-options.ts`).
  한쪽만 고치면 화면과 서버 판정이 어긋납니다.

세부 규칙은 [`docs/CODING_RULES.md`](docs/CODING_RULES.md)에 있습니다.

## 검증 규칙

- **검증 없이 완료 보고하지 않습니다.** 실행하지 못한 검증은 이유를 밝힙니다.
- **검증 명령의 종료 코드를 가리지 마세요.** `pytest -q | tail`처럼 파이프를 쓰면 `tail`의
  종료 코드가 쓰여 실패가 묻힙니다. 파일로 받고 `exit=$?`를 눈으로 확인한 뒤 커밋합니다.
- **오류를 겪으면 그 자리에서 [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)에 남깁니다.**
  증상 → 원인 → 판별 → 해결 순서로 적습니다. 작업 중이던 다른 문서에 적으면 다음 사람이 못 찾습니다.

## 배포 규칙

- **코드 커밋을 push의 마지막에 둡니다.** 두 Render 서비스의 Root Directory가 `backend`·`frontend`라
  **push의 tip 커밋**이 그 밖이면 배포가 통째로 건너뛰어집니다. 문서와 코드를 함께 올릴 때 특히 주의합니다.
- **push 후 실제 배포 여부를 확인합니다.** Render 서비스 상단의 커밋 해시가 master 최신과 같은지 봅니다.
  `Deploy skipped` 이벤트는 항상 남지 않습니다.
- 배포는 CI 성공 후에만 시작됩니다(`Auto-Deploy: After CI Checks Pass`).

## 작업 보고

변경한 파일, 그렇게 고친 이유, 검증 결과를 짧게 적습니다.
전체 파일 내용이나 긴 코드 블록을 요청 없이 다시 출력하지 않습니다.
큰 작업은 마일스톤으로 나누고, 다음 마일스톤을 승인 없이 진행하지 않습니다.
