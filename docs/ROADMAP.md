# Roadmap

앞으로 할 일만 적습니다.

- 지금 무엇이 되는지 → [`CURRENT_STATE.md`](CURRENT_STATE.md)
- 과거에 무엇을 했는지 → [`../UPDATELOG.md`](../UPDATELOG.md)
- Jira 보드 반영 대상 → [`JIRA_UPDATE_2026-08-08.md`](JIRA_UPDATE_2026-08-08.md)
- 2026-07-30 ~ 08-15 일정 기준선 → [`archive/ROADMAP_PLAN_2026-08.md`](archive/ROADMAP_PLAN_2026-08.md)

## 지금: Feature Freeze

2026-08-13부터 신규 기능을 추가하지 않고 회귀 결함만 고칩니다.
프리즈 중에도 가능한 것은 문서 정리, 결정 확정, Jira 반영입니다.

## 프리즈 해제 직후

우선순위 순서이며, 1번을 먼저 해야 2번이 함께 확인됩니다.

| 순서 | 항목 | 비고 |
|---|---|---|
| 1 | `PART_ADMIN` 도입 | 설계는 [`DECISIONS.md`](DECISIONS.md)에 확정. 구현은 `feat/part-admin-role` 브랜치에 있고 master 미머지. **적용 전 기존 `TEAM_ADMIN` 보유자 재분류 필요** |
| 2 | 배포 게이트 동작 검증 | 1번 배포에서 `Deploy started`가 CI 성공 뒤인지 확인 |
| 3 | GitHub branch protection | master 직접 push 금지 + PR 필수 CI |
| 4 | Pre-Deploy Command로 migration 자동화 검토 | 실패 시 운영 DB가 중간 상태로 남을 위험이 있어 별도 판단 |

## 이후 후보

우선순위가 확정되지 않은 항목입니다.

- 알림 조회·읽음 API — 테이블은 있고 API가 없습니다
- 공통 오류 응답 형식 정리
- ATS·Storage Playwright E2E 확대
- 데드 코드·덤프 파일 정리 (빈 `frontend/src/storage/`, 역할 값 어휘 이중화, `docs/archive/` 재정리)
- 대시보드 운영 데이터 정책 — 가짜 데이터를 넣지 않기로 확정됨([`DECISIONS.md`](DECISIONS.md))

## 범위 밖

실제 이메일 발송, PDF 분석·OCR, RAG·벡터 DB, n8n, 다단계 결재, WebSocket 실시간 알림,
Docker, 모바일 앱, 자동 채용 결정. 배경은 [`PROJECT_SPEC.md`](PROJECT_SPEC.md).
