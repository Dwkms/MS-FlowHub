# Jira 업데이트 정리 — 2026-08-08

> 마지막 갱신: **2026-08-13** · 기준 커밋 `21c591a` (코드 검증 기준 `b84b8fb`)
>
> 아래 항목을 기존 Jira 에픽에 완료 또는 후속 작업으로 반영합니다.
> 프로젝트별 이슈 키·담당자는 Jira 보드의 기존 값을 유지합니다.

## 완료 처리 — 2026-08-08 기준

| 제목 | 연결할 기존 범주 | 완료 기준 |
| --- | --- | --- |
| CI/CD와 크로스플랫폼 E2E 안정화 | QA·배포·문서 | GitHub Actions CI 구성, 수동 E2E workflow 분리, 데스크톱·모바일 Playwright 14개 통과 |
| 관리자 업무 현황 대시보드 | 대시보드 | 결재·채용·근태 기반 관리자 지표와 권한 분기 구현 |
| 전자결재 관리자 권한 보완 | 전자결재 | 팀장급 이상 결재자 제한, 관리자 승인/반려 처리, TEAM_ADMIN 500 오류 수정 |
| 조직 및 직원번호 개편 | 직원·조직 관리 | 개발팀 SW/HW/QA팀, 마케팅·인사·기획 1·2팀, CS1팀 반영과 migration 적용 |
| 직원 조직도와 반응형 화면 검증 | 직원·조직 관리 | 최신 조직도 자산 교체, 데스크톱·모바일 팝업 이미지 로드 검증 |

## 완료 처리 — 2026-08-12~13 추가분

| 제목 | 연결할 기존 범주 | 완료 기준 | 근거 |
| --- | --- | --- | --- |
| 생성형 AI 공통 기반 | AI | Provider 프로토콜·Mock·Claude·Structured Output·`ai_generations`·일일 한도 | PR #5 |
| 전자결재 AI 초안 생성 | 전자결재 | 초안 API와 화면, `claude-opus-5` 실호출 검증 (건당 약 19원) | PR #7 이전 |
| 채용 정보 구체화와 AI 공고 초안 | 채용 | `recruitment_requests` 6칼럼 migration, `PATCH /api/v1/job-postings/{id}` 신설, AI Context가 DB 값을 우선 사용 | `32523cb` |
| AI 채용 포스터 생성 | 채용 | OpenAI `gpt-image-2`로 2안 생성·비교·선택·확대·PNG 다운로드 (건당 약 24원) | `32523cb` |
| 세션 자동 로그아웃 | 보안 | 생존 신호 방식, `NEXT_PUBLIC_SESSION_TIMEOUT_MINUTES` 기본 30분, 실제 시간 경과 수동 검증 통과 | `32523cb` |
| Feature Freeze 판정 | QA·배포 | **P0 0건 · P1 0건**, `FEATURE FREEZE READY: YES`, `MERGE / RELEASE GATE: GO` | `24c9c84`, `b84b8fb` |
| Render 배포 게이트 전환 | QA·배포 | Backend·Frontend 모두 `Auto-Deploy: After CI Checks Pass`로 전환·저장 확인 | `82d8a89`, `21c591a` |

## 후속 작업 — 현재 상태

| 제목 | 우선순위 | 상태 | 설명 |
| --- | --- | --- | --- |
| GitHub Actions CI 결과 확인 | 높음 | **완료 (08-13)** | `ci.yml` 상시 운영 중. `b84b8fb`의 backend·frontend CI 성공 확인 |
| Render 배포 게이트 결정 | 중간 | **완료 (08-13)** | `After CI Checks Pass`로 확정·적용. 동작 검증은 아래 신규 항목으로 분리 |
| 대시보드 운영 데이터 정책 결정 | 중간 | 미결 | 실데이터가 적은 상태를 유지할지, 검증용 업무 데이터를 추가할지 결정 |
| 파트장 TEAM_ADMIN 권한 부여 여부 결정 | 중간 | 미결 | SW·HW·CS 파트장의 실제 로그인 계정과 권한 부여 범위를 확정 |
| 알림 및 공통 오류 응답 형식 | 낮음 | 미결 | 알림 조회/읽음 처리와 API 표준 오류 응답 형식 설계 |
| ATS·Storage Playwright E2E 확대 | 낮음 | 미결 | 지원자 관리와 파일 업로드/조회 흐름의 브라우저 회귀 테스트 추가 |

## 신규 후속 작업 — 2026-08-13 발생

| 제목 | 우선순위 | 설명 |
| --- | --- | --- |
| Render 배포 게이트 동작 검증 | 중간 | 게이트는 적용됐으나 **아직 작동한 적이 없습니다.** Root Directory가 `backend`·`frontend`라 문서만 바꾼 커밋은 Render가 auto-deploy를 건너뜁니다. 프리즈 이후 `backend/`·`frontend/`를 바꾸는 첫 배포에서 Events의 `Deploy started`가 CI 성공 이후인지 확인 |
| GitHub branch protection 적용 | 중간 | `master` 직접 push 금지 + PR 필수 CI. Render 게이트가 하류 방어라면 이쪽이 상위 보호. **프리즈 중에는 적용하지 않습니다** — P0 핫픽스 대응이 느려짐 |
| Pre-Deploy Command로 migration 자동화 검토 | 낮음 | 현재 두 서비스 모두 Pre-Deploy Command가 비어 있어 Alembic이 수동입니다. `alembic upgrade head` 자동화는 실패 시 운영 DB가 중간 상태로 남을 수 있어 프리즈 이후 별도 판단 |
| 배포 문서의 서비스 주소 정정 반영 | 낮음 | 백엔드 실제 서비스명은 `MS-FlowHub`, URL은 `https://ms-flowhub.onrender.com`입니다. 계획 문서의 `ms-flowhub-backend.onrender.com`은 실재하지 않는 예시값이었고 `21c591a`에서 정정했습니다 |

## Jira 반영 순서

1. **완료 처리** 두 표의 항목을 기존 에픽의 완료 이슈 또는 하위 작업으로 반영한다.
2. **후속 작업 — 현재 상태** 표에서 `완료 (08-13)` 2건을 종료 처리하고, 미결 4건은 우선순위를 유지한 채 남긴다.
3. **신규 후속 작업** 4건을 생성한다. 이 중 `branch protection`과 `Pre-Deploy Command`는 **프리즈 해제 이후** 착수 항목으로 표시한다.
4. 각 이슈에 검증 결과를 기록한다.

### 기록할 검증 결과 (2026-08-13 기준)

```
Backend    Ruff check · Ruff format check 통과
           pytest 201 passed
운영 DB    Alembic 20260813_0023 (code head = DB current)
Frontend   lint · typecheck · production build 통과
CI         GitHub Actions backend·frontend 성공
운영 확인   Backend /health 200, Frontend /login 200,
           Frontend /api/* 프록시 401(미인증 정상 응답)
운영 배포   32523cb — 이후 커밋은 모두 문서 변경이라 배포 대상 아님
```

> Playwright E2E는 `workflow_dispatch` 전용(수동)입니다. 2026-08-08의 "14개 통과"는 당시 기록이며,
> 이후 자동 실행하지 않으므로 최신 실행 결과로 인용하지 않습니다.
