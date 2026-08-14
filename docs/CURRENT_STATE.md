# Current State

**기준: 2026-08-14 · 파트장 체계 운영 반영 완료 · 1차 데드코드 정리 완료**

지금 무엇이 되고 무엇이 안 되는지만 적습니다.
과거에 무엇을 했는지는 [`../UPDATELOG.md`](../UPDATELOG.md), 앞으로의 일정은 [`ROADMAP.md`](ROADMAP.md).

## 전체 판정

| 항목 | 상태 |
|---|---|
| P0 · P1 결함 | 0건 · 0건 |
| Feature Freeze | **해제됨** (2026-08-13). 판정 당시 READY: YES |
| 자동 검증 | Backend pytest **208 passed** · Ruff 통과 / Frontend lint·typecheck·build 통과 |
| 운영 DB | Alembic `20260814_0024` (code head = DB current) · 업무 테이블 18개 |
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
| 배포 게이트 | **검증 완료** | CI 성공→배포 / CI 실패→차단 **양방향 실증** (2026-08-14) |

## 알려진 문제와 미검증 항목

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

**1. 문서 통합** — 기획 문서 7개(약 1,700줄)를 `docs/PLAN.md` 하나로 재구성하고
로드맵을 1개로 합칩니다. 포트폴리오 제출 시 "어느 파일에 무엇이 왜 있는지" 설명 가능하게 만드는 작업입니다.

**2. 핵심 코드 주석 보강** — Service·`domain/`·`security/`와 프론트 기능 진입점에
"왜 이렇게 했는지"를 남깁니다.

**3. README 재구성** — 프로젝트 구성 요약 중심으로 줄이고 상세는 docs로 보냅니다.

**4. GitHub branch protection** — master 직접 push 금지 + PR 필수 CI

**5. Pre-Deploy Command로 migration 자동화 검토**

**6.** 공통 오류 응답 형식, ATS·Storage E2E 확대, 위 "화면이 없는 기능"의 UI

**7.** 위 정리가 끝난 뒤 Jira 최종정리

### 완료된 항목 (2026-08-14)

- **운영 역할 부여** — 이서진·김도윤·최다은 `PART_ADMIN`, 김태윤 `TEAM_ADMIN`.
  각 계정 로그인으로 관리 인원(5·4·3·5명) 확인. 김태윤은 구버전 QA팀장에서 CS부서로
  이동하며 누락됐던 건입니다.
- **배포 게이트 양방향 실증** — CI 실패 커밋 `9a7864b` 차단, 수정본 `dda951e` 배포.
- **1차 데드코드 정리** — 알림 기능 제거(테이블 포함), 중복 조직도 PNG 1.24MB,
  미사용 함수 7건.
- 머지로 범위가 넓어진 계정: MS0015 강수아(MKT_1 5명 → MKT 10명), MS0035 박서준(PLAN_1 → PLAN).
  둘 다 팀장이라 의도한 결과입니다.

Jira 반영 대상은 [`JIRA_UPDATE_2026-08-08.md`](JIRA_UPDATE_2026-08-08.md)에 정리돼 있습니다.
