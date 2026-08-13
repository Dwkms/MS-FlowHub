# MS FlowHub — Agent Guide

전자결재를 중심으로 직원·조직, 근태, 채용을 연결한 사내 업무 시스템입니다.
가상 회사 MS의 직원 46명을 기준으로 만든 취업 포트폴리오 프로젝트이며 Render에 실제 배포돼 있습니다.

**FastAPI + Next.js + Supabase PostgreSQL.** 상세는 아래 Context Map에서 필요한 문서만 읽으세요.

## 현재 상태

**Feature Freeze 중입니다.** 신규 기능을 추가하지 않고 회귀 결함만 고칩니다.
프리즈 이후로 미룬 작업과 도메인별 구현 상태는 [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md).

## Context Map

작업 종류에 맞는 문서만 읽습니다. 전부 읽지 마세요.

| 하려는 일 | 먼저 볼 문서 |
|---|---|
| 시스템 구조·인증 흐름·배포 | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| 업무 규칙·권한·상태 전이 | [`docs/DOMAIN.md`](docs/DOMAIN.md) |
| 테이블·컬럼·관계 | [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) |
| 엔드포인트 확인·추가 | [`docs/API_SPEC.md`](docs/API_SPEC.md) |
| 무엇이 되고 무엇이 안 되는지 | [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md) |
| 코드 작성 규칙·검증 명령 | [`docs/CODING_RULES.md`](docs/CODING_RULES.md) |
| 왜 이렇게 만들었는지 | [`docs/DECISIONS.md`](docs/DECISIONS.md) |
| 배포·Render 설정 | [`docs/DEPLOYMENT_PLAN.md`](docs/DEPLOYMENT_PLAN.md) |
| AI 기능 제약 | [`docs/AI_DESIGN.md`](docs/AI_DESIGN.md) |
| 겪은 오류와 해결 | [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) |
| 과거에 무엇을 했는지 | [`UPDATELOG.md`](UPDATELOG.md) |

예시 — 직원관리 기능을 고친다면:
`DOMAIN.md`의 직원·근태 절 → `DATA_MODEL.md`의 해당 테이블 →
`backend/app/services/employee_service.py`와 `frontend/src/features/employees/` 순으로 봅니다.

## 반드시 지킬 것

- **최소 변경.** 전체 재작성 대신 필요한 부분만 고치고 기존 UI·동작을 유지합니다.
- **재사용 우선.** 새로 만들기 전에 기존 유틸·타입·컴포넌트·Service·Repository를 찾습니다.
- **계층 책임 분리.** Router는 요청·응답만, 업무 규칙은 Service, DB 접근은 Repository.
- **권한은 서버에서 판정.** 화면 표시로만 막지 않습니다.
- **프론트엔드는 Supabase 업무 테이블에 직접 접근하지 않습니다.** 로그인만 예외입니다.
- **DB 스키마 변경은 Alembic migration으로 기록합니다.** 대시보드 수동 변경에 의존하지 않습니다.
- **AI는 상태를 바꾸지 않습니다.** 공통 Provider만 거치고, AI 실패가 업무 저장을 막지 않게 합니다.
- **비밀값을 코드에 쓰지 않습니다.** `SUPABASE_SECRET_KEY`·`DATABASE_URL`·AI 키를 `NEXT_PUBLIC_*`에
  절대 넣지 않습니다.
- **검증 없이 완료 보고하지 않습니다.** 실행하지 못한 검증은 이유를 밝힙니다.

세부 규칙과 검증 명령은 [`docs/CODING_RULES.md`](docs/CODING_RULES.md)에 있습니다.

## 작업 보고

변경한 파일, 그렇게 고친 이유, 검증 결과를 짧게 적습니다.
전체 파일 내용이나 긴 코드 블록을 요청 없이 다시 출력하지 않습니다.
큰 작업은 마일스톤으로 나누고, 다음 마일스톤을 승인 없이 진행하지 않습니다.

## 설명 방식 (요청이 있을 때만)

사용자가 설명·학습을 요청하면 그때 적용합니다. 평소 작업에는 위 "작업 보고"를 따릅니다.

- 구현 전에 입력·처리·출력을 먼저 설명합니다.
- Python·FastAPI 개념은 초급자 기준으로 풉니다.
- 오류가 나면 정답 코드보다 원인을 먼저 설명합니다.
- 사용자가 직접 작성·수정할 부분을 구분해 줍니다.
