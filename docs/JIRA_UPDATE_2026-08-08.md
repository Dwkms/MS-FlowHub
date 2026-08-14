# Jira 업데이트 정리 — 2026-08-08

> 마지막 갱신: **2026-08-14** · Jira 최종정리 완료
>
> 아래 항목을 기존 Jira 에픽에 완료 또는 후속 작업으로 반영합니다.
> 프로젝트별 이슈 키·담당자는 Jira 보드의 기존 값을 유지합니다.

2026-08-14 Jira 내보내기 CSV 기준으로 **72개(에픽 7개·작업 65개)**의 키·이슈 유형·상위 항목·요약·상태·시작일·기한이 가져오기 원본과 일치합니다. 작업 65개는 모두 지정한 에픽에 연결됐고 누락·중복 이슈는 없습니다. 담당자 72건은 비어 있는 상태로 최종정리를 완료했습니다.

## 완료 처리 — 2026-08-08 기준

| 제목 | 상위 항목(에픽) | 완료 기준 |
| --- | --- | --- |
| CI/CD와 크로스플랫폼 E2E 안정화 | QA·배포·문서화 | GitHub Actions CI 구성, 수동 E2E workflow 분리, 데스크톱·모바일 Playwright 14개 통과 |
| 관리자 업무 현황 대시보드 | MFH-5 대시보드·알림 | 결재·채용·근태 기반 관리자 지표와 권한 분기 구현 |
| 전자결재 관리자 권한 보완 | MFH-3 전자결재 | 팀장급 이상 결재자 제한, 관리자 승인/반려 처리, TEAM_ADMIN 500 오류 수정 |
| 조직 및 직원번호 개편 | MFH-2 직원·조직 관리 | 개발팀 SW/HW/QA팀, 마케팅·인사·기획 1·2팀, CS1팀 반영과 migration 적용 |
| 직원 조직도와 반응형 화면 검증 | MFH-2 직원·조직 관리 | 최신 조직도 자산 교체, 데스크톱·모바일 팝업 이미지 로드 검증 |

## 완료 처리 — 2026-08-12~13 추가분

| 제목 | 상위 항목(에픽) | 완료 기준 | 근거 |
| --- | --- | --- | --- |
| 생성형 AI 공통 기반 | MFH-1 공통 구조 및 접근 권한 | Provider 프로토콜·Mock·Claude·Structured Output·`ai_generations`·일일 한도 | PR #5 |
| 전자결재 AI 초안 생성 | MFH-3 전자결재 | 초안 API와 화면, `claude-opus-5` 실호출 검증 (건당 약 19원) | PR #7 이전 |
| 채용 정보 구체화와 AI 공고 초안 | MFH-4 채용 관리 | `recruitment_requests` 6칼럼 migration, `PATCH /api/v1/job-postings/{id}` 신설, AI Context가 DB 값을 우선 사용 | `32523cb` |
| AI 채용 포스터 생성 | MFH-4 채용 관리 | OpenAI `gpt-image-2`로 2안 생성·비교·선택·확대·PNG 다운로드 (건당 약 24원) | `32523cb` |
| 세션 자동 로그아웃 | MFH-1 공통 구조 및 접근 권한 | 생존 신호 방식, `NEXT_PUBLIC_SESSION_TIMEOUT_MINUTES` 기본 30분, 실제 시간 경과 수동 검증 통과 | `32523cb` |
| Feature Freeze 판정 | QA·배포·문서화 | **P0 0건 · P1 0건**, `FEATURE FREEZE READY: YES`, `MERGE / RELEASE GATE: GO` | `24c9c84`, `b84b8fb` |
| Render 배포 게이트 전환 | QA·배포·문서화 | Backend·Frontend 모두 `Auto-Deploy: After CI Checks Pass`로 전환·저장 확인 | `82d8a89`, `21c591a` |

## 후속 작업 — 현재 상태

| 제목 | 우선순위 | 상태 | 설명 |
| --- | --- | --- | --- |
| GitHub Actions CI 결과 확인 | 높음 | **완료 (08-13)** | `ci.yml` 상시 운영 중. `b84b8fb`의 backend·frontend CI 성공 확인 |
| Render 배포 게이트 결정 | 중간 | **완료 (08-13)** | `After CI Checks Pass`로 확정·적용. 동작 검증은 아래 신규 항목으로 분리 |
| 대시보드 운영 데이터 정책 결정 | 중간 | **완료 (08-13)** | 운영 DB에는 가짜 업무 데이터를 넣지 않고 실데이터만 사용하기로 확정 |
| 파트장 권한 체계 결정 | 중간 | **완료 (08-14)** | `PART_ADMIN`을 신설하고 SW·HW·QA 파트장에게 운영 역할 부여 |
| 공통 오류 응답 형식 | 낮음 | 미결 | 알림은 08-14에 제거. API 표준 오류 응답 형식은 별도 후속 작업으로 유지 |
| ATS·Storage Playwright E2E 확대 | 낮음 | 미결 | 지원자 관리와 파일 업로드/조회 흐름의 브라우저 회귀 테스트 추가 |

## 신규 후속 작업 — 2026-08-13 발생

| 제목 | 우선순위 | 설명 |
| --- | --- | --- |
| Render 배포 게이트 동작 검증 | 중간 | **완료 (08-14).** CI 실패 커밋은 차단되고 수정본만 배포되는 양방향 동작 확인 |
| GitHub branch protection 적용 | 중간 | `master` 직접 push 금지 + PR 필수 CI. Feature Freeze는 해제됐으며 아직 적용하지 않음 |
| Pre-Deploy Command로 migration 자동화 검토 | 낮음 | 현재 두 서비스 모두 Pre-Deploy Command가 비어 있어 Alembic이 수동입니다. `alembic upgrade head` 자동화는 실패 시 운영 DB가 중간 상태로 남을 수 있어 프리즈 이후 별도 판단 |


## Jira 반영 순서

1. **완료 처리** 두 표의 항목을 기존 에픽의 완료 이슈 또는 하위 작업으로 반영한다.
2. 운영 데이터 정책·파트장 권한·배포 게이트 검증은 완료 처리하고, 공통 오류 응답 형식과 ATS·Storage E2E는 후속 작업으로 남긴다.
3. `branch protection`과 `Pre-Deploy Command`는 미착수 후속 작업으로 유지한다.
4. 각 이슈에 검증 결과를 기록한다.

### 기록할 검증 결과 (2026-08-14 기준)

```
Backend    Ruff check · Ruff format check 통과
           pytest 209 passed
운영 DB    Alembic 20260814_0024 (code head = DB current) · 업무 테이블 18개
Frontend   lint · typecheck · production build 통과
CI         GitHub Actions backend·frontend 성공
배포 게이트 CI 성공 -> 배포 / CI 실패 -> 차단 양방향 실증 완료
운영 확인   Backend /health 200, Frontend /login 200,
           Frontend /api/* 프록시 401(미인증 정상 응답), CORS 정상
```

> Playwright E2E는 `workflow_dispatch` 전용(수동)입니다. 2026-08-08의 "14개 통과"는 당시 기록이며,
> 이후 자동 실행하지 않으므로 최신 실행 결과로 인용하지 않습니다.
