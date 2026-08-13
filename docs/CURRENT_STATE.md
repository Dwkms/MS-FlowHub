# Current State

**기준: 2026-08-13 · Feature Freeze 중 · 운영 배포 커밋 `32523cb`**

지금 무엇이 되고 무엇이 안 되는지만 적습니다.
과거에 무엇을 했는지는 [`../UPDATELOG.md`](../UPDATELOG.md), 앞으로의 일정은 [`ROADMAP.md`](ROADMAP.md).

## 전체 판정

| 항목 | 상태 |
|---|---|
| P0 · P1 결함 | 0건 · 0건 |
| Feature Freeze | READY: YES — 신규 기능 중단, 회귀 결함만 수정 |
| 자동 검증 | Backend pytest 201 passed · Ruff 통과 / Frontend lint·typecheck·build 통과 |
| 운영 DB | Alembic `20260813_0023` (code head = DB current) |
| 운영 확인 | Backend `/health` 200 · Frontend `/login` 200 · `/api/*` 프록시 401(미인증 정상) |

## 도메인별

| 도메인 | 상태 | 비고 |
|---|---|---|
| 인증·권한 | **완료** | Supabase Auth + JWKS, 역할 4종, 서버 재검증, 자동 로그아웃(기본 30분) |
| 직원·조직·근태 | **완료** | 부서·파트 2계층, 근무 상태 12종, 비공개 사유 분리, 변경 이력 |
| 전자결재 | **완료** | 작성·상신·승인·반려·이력, 결재자 팀장급 제한 |
| 채용 요청·공고 | **완료** | 승인 시 공고 자동 생성, 공고 수정 API, 선택지 구체화 |
| ATS 지원자 | **완료** | 전형 6단계, 종료 단계 되돌리기 차단, 이력 |
| 대시보드 | **완료** | 개인 지표 3종 + 관리자 분석 6종 |
| 직원 매뉴얼·FAQ | **완료** | 목록·검색·상세, 역할별 공개 범위 |
| AX 직원 도우미 | **완료** | 매뉴얼·FAQ 기반 응답. RAG·벡터 DB 없음 |
| 생성형 AI 초안 | **완료** | 전자결재·채용공고 초안(`claude-opus-5`), 실호출 검증 |
| AI 채용 포스터 | **완료** | OpenAI `gpt-image-2` 2안 생성·비교·선택·PNG 다운로드 |
| 알림 | **부분 구현** | `notifications` 테이블에 채용 처리 알림이 쌓이지만 **조회·읽음 API가 없습니다** |
| CI | **완료** | `ci.yml`이 master push·PR마다 Backend·Frontend 검사 |
| 배포 게이트 | **적용됨 · 동작 미검증** | 아래 참고 |

## 알려진 문제와 미검증 항목

**배포 게이트가 아직 한 번도 작동하지 않았습니다.**
두 Render 서비스 모두 `Auto-Deploy: After CI Checks Pass`로 바꿨지만, 전환 이후 push된 커밋이
전부 문서 변경이라 Root Directory(`backend`·`frontend`) 밖이었습니다.
프리즈 이후 첫 코드 배포에서 Events의 `Deploy started`가 CI 성공 뒤인지 확인해야 합니다.

**백엔드가 잠들면 프론트 프록시가 즉시 502를 냅니다.**
Render 무료 플랜 특성입니다. 화면은 뜨는데 데이터만 안 나와 장애로 오인하기 쉽습니다.
판별법은 [`../TROUBLESHOOTING.md`](../TROUBLESHOOTING.md)의 "화면은 뜨는데 API만 502".

**`frontend/src/storage/`가 빈 디렉터리입니다.**
`localStorage`를 storage 레이어로 감싸는 규칙이 있었지만 실제로는 두 파일이 직접 호출합니다.
규칙을 되살릴지 현실에 맞출지 정해지지 않았습니다.

**Playwright E2E는 수동 실행 전용입니다.**
실제 Supabase에 접속하므로 CI에서 자동 실행하지 않습니다. 프론트에는 단위 테스트가 없습니다.

**역할 값 어휘가 두 벌입니다.**
`employee_accounts.role`(권한)과 `employees.role`(시드)이 다른 값을 씁니다.
[`DOMAIN.md`](DOMAIN.md#역할과-권한) 참고.

## 프리즈 해제 후 착수 순서

1. **`PART_ADMIN` 도입** — 설계는 [`DECISIONS.md`](DECISIONS.md)에 확정. 구현은 브랜치
   `feat/part-admin-role`에 있고 master 미머지. 적용 전 기존 `TEAM_ADMIN` 보유자를
   팀장/파트장으로 재분류해야 합니다
2. **배포 게이트 동작 검증** — 1번 배포에서 함께 확인됨
3. **GitHub branch protection** — master 직접 push 금지 + PR 필수 CI
4. **Pre-Deploy Command로 migration 자동화 검토** — 현재는 배포 전 수동 `alembic upgrade head`
5. 알림 조회·읽음 API, 공통 오류 응답 형식
6. ATS·Storage Playwright E2E 확대

Jira 반영 대상은 [`JIRA_UPDATE_2026-08-08.md`](JIRA_UPDATE_2026-08-08.md)에 정리돼 있습니다.
