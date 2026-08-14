# Current State

**기준: 2026-08-13 · Feature Freeze 해제 · 파트장 체계 머지 완료**

지금 무엇이 되고 무엇이 안 되는지만 적습니다.
과거에 무엇을 했는지는 [`../UPDATELOG.md`](../UPDATELOG.md), 앞으로의 일정은 [`ROADMAP.md`](ROADMAP.md).

## 전체 판정

| 항목 | 상태 |
|---|---|
| P0 · P1 결함 | 0건 · 0건 |
| Feature Freeze | **해제됨** (2026-08-13). 판정 당시 READY: YES |
| 자동 검증 | Backend pytest 210 passed · Ruff 통과 / Frontend lint·typecheck·build 통과 |
| 운영 DB | Alembic `20260813_0023` (code head = DB current) |
| 운영 확인 | Backend `/health` 200 · Frontend `/login` 200 · `/api/*` 프록시 401(미인증 정상) |

## 도메인별

| 도메인 | 상태 | 비고 |
|---|---|---|
| 인증·권한 | **완료** | Supabase Auth + JWKS, 역할 5종(`PART_ADMIN` 포함), 서버 재검증, 자동 로그아웃(기본 30분) |
| 직원·조직·근태 | **완료** | 부서·파트 2계층, 근무 상태 12종, 비공개 사유 분리, 변경 이력 |
| 전자결재 | **완료** | 작성·상신·승인·반려·이력, 결재자 팀장급 제한 |
| 채용 요청·공고 | **완료** | 승인 시 공고 자동 생성, 공고 수정 API, 선택지 구체화 |
| ATS 지원자 | **완료** | 전형 6단계, 종료 단계 되돌리기 차단, 이력 |
| 대시보드 | **완료** | 개인 지표 3종 + 관리자 분석 6종 |
| 직원 매뉴얼·FAQ | **완료** | 목록·검색·상세, 역할별 공개 범위 |
| AX 직원 도우미 | **완료** | 매뉴얼·FAQ 기반 응답. RAG·벡터 DB 없음 |
| 생성형 AI 초안 | **완료** | 전자결재·채용공고 초안(`claude-opus-5`), 실호출 검증 |
| AI 채용 포스터 | **완료** | OpenAI `gpt-image-2` 2안 생성·비교·선택·PNG 다운로드 |
| 알림 | **제거됨** | 2026-08-14에 코드와 `notifications` 테이블을 함께 삭제했습니다 |
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

**storage 레이어 규칙만 있고 구현이 없습니다.**
`localStorage`를 별도 레이어로 감싸는 규칙이 있었지만 구현된 적이 없고,
`features/auth/session-timeout.ts`와 `features/ax/ax-assistant-provider.tsx`가 직접 호출합니다.
규칙을 되살릴지 현실에 맞출지 정해지지 않았습니다.

**API는 있는데 화면이 없는 기능이 있습니다.**
결재 문서 수정(`PATCH /approvals/{id}`), 공고 수정(`PATCH /job-postings/{id}`),
역할 변경(`PATCH /employees/{id}/role`), 조직도 조회(`GET /employees/organization`)가
여기 해당합니다. 조직도는 화면이 API 대신 정적 PNG를 씁니다.

**Playwright E2E는 수동 실행 전용입니다.**
실제 Supabase에 접속하므로 CI에서 자동 실행하지 않습니다. 프론트에는 단위 테스트가 없습니다.

**역할 값 어휘가 두 벌입니다.**
`employee_accounts.role`(권한)과 `employees.role`(시드)이 다른 값을 씁니다.
[`DOMAIN.md`](DOMAIN.md#역할과-권한) 참고.

## 다음 순서

**1. 운영 역할 부여 — 코드는 배포됐지만 아직 아무도 `PART_ADMIN`이 아닙니다.**

| 사번 | 이름 | 소속 | 직책 | 현재 | 부여할 값 |
|---|---|---|---|---|---|
| MS0003 | 이서진 | DEV / DEV_SW | 파트장 | `EMPLOYEE` | `PART_ADMIN` |
| MS0008 | 김도윤 | DEV / DEV_HW | 파트장 | `EMPLOYEE` | `PART_ADMIN` |
| MS0012 | 최다은 | DEV / DEV_QA | 파트장 | `TEAM_ADMIN` | `PART_ADMIN` |
| MS0045 | 김태윤 | CS / CS_1 | 팀장 | `EMPLOYEE` | `TEAM_ADMIN` |

MS0045는 구버전 QA팀장에서 CS부서로 이동하는 과정에서 권한 부여가 누락된 건입니다.

머지로 범위가 넓어진 계정: MS0015 강수아(MKT_1 5명 → MKT 10명), MS0035 박서준(PLAN_1 → PLAN).
둘 다 팀장이라 의도한 결과입니다.

**2. 배포 게이트 동작 검증** — 이번 배포가 첫 코드 배포입니다.
**3. GitHub branch protection** — master 직접 push 금지 + PR 필수 CI
**4. Pre-Deploy Command로 migration 자동화 검토**
**5.** 공통 오류 응답 형식, ATS·Storage E2E 확대, 위 "화면이 없는 기능"의 UI
**6.** 리팩토링·데드코드 정리 후 Jira 최종정리

Jira 반영 대상은 [`JIRA_UPDATE_2026-08-08.md`](JIRA_UPDATE_2026-08-08.md)에 정리돼 있습니다.
