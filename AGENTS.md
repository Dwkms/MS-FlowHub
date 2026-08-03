# Project Rules

- 기존에 구현된 UI와 기능은 유지하고 필요한 부분만 수정한다.
- TypeScript 오류 없이 작성한다.
- Python 문법 오류와 Ruff 오류 없이 작성한다.
- API 호출이 불필요하게 중복되지 않게 한다.
- 프론트엔드 비즈니스 로직은 `page.tsx` 또는 UI 컴포넌트에 집중시키지 않는다.
- 프론트엔드 API 호출은 공통 API Client를 사용하고 동일 요청을 여러 컴포넌트에서 중복 구현하지 않는다.
- `localStorage`는 컴포넌트에서 직접 호출하지 않고 별도 storage 레이어를 사용한다.
- FastAPI Router에는 요청 수신, 응답 반환, 의존성 주입만 둔다.
- 업무 규칙은 Service에, DB 접근은 Repository 또는 명시적 데이터 접근 함수에 둔다.
- SQLAlchemy ORM 모델과 Pydantic API 스키마를 분리한다.
- 승인, 반려, 확정 등 상태 변경 규칙은 Service에서 관리한다.
- 프론트엔드가 보낸 금액, 할인액, 합계는 백엔드에서 다시 계산한다.
- 여러 데이터 변경이 하나의 업무이면 하나의 트랜잭션으로 처리한다.
- Seed 데이터는 반복 실행해도 중복 생성되지 않게 작성한다.
- AI 호출은 공통 AI Provider만 사용하고 AI 결과를 최종 업무 결정으로 자동 반영하지 않는다.
- AI 실패가 핵심 업무 데이터 저장을 무조건 실패시키지 않게 설계한다.
- 환경변수와 API Key를 코드에 직접 작성하지 않는다.
- 프론트엔드는 Supabase 업무 테이블에 직접 접근하지 않는다.
- DB 스키마 변경은 Alembic migration으로 기록한다.
- 실제 구현 상태와 README 설명을 일치시킨다.
- 작업 후 변경 파일, 수정 이유, 검증 결과를 간단히 설명한다.

## Context / File Reading

- 관련 파일만 읽고 불필요한 전체 프로젝트 스캔을 하지 않는다.
- 수정 대상과 직접 연결된 파일, 필요한 코드 범위만 우선 확인한다.
- 사용자가 요청하지 않으면 파일 전체 내용을 응답에 다시 출력하지 않는다.
- 기존 코드 구조를 최대한 유지한다.
- 기획 내용은 먼저 `docs/`에서 확인한다.
- 데이터 모델 변경 전 `docs/DATA_MODEL.md`와 현재 migration을 확인한다.
- API 변경 전 `docs/API_SPEC.md`와 관련 Router, Schema, Service를 확인한다.
- AI 기능 변경 전 `docs/AI_DESIGN.md`를 확인한다.

## Code Edit Rules

- 전체 재작성보다 필요한 부분만 Patch 방식으로 수정하고 기존 동작을 깨지 않는 최소 변경을 우선한다.
- 반복 생성을 피하고 기존 유틸, 타입, 컴포넌트, Service, Repository를 우선 재사용한다.
- 새 파일은 역할이 명확하고 반드시 필요한 경우에만 만든다.
- 임시 코드, 테스트 로그, 사용하지 않는 import를 남기지 않는다.
- Router, Service, Repository의 책임을 혼합하지 않는다.
- 오래된 `session.query()`보다 SQLAlchemy 2.0 방식과 동기 Session을 사용한다.
- 별도 요청이 없다면 비동기 DB 코드를 도입하지 않는다.
- DB 구조 변경 시 Alembic migration 적용 여부를 확인하며 Supabase 대시보드의 수동 구조에 의존하지 않는다.
- 오류 발생 시 전체 파일을 교체하기 전에 원인을 분석한다.
- 이해하기 어려운 축약 문법, 과도한 추상화, 역할이 지나치게 큰 함수와 클래스를 피한다.
- 예외를 무조건 잡아 숨기지 않고 사용자 오류와 내부 오류를 구분한다.
- 금액 계산에는 부동소수점 오류를 고려한다.

## Verification Rules

Frontend 변경 시 가능한 범위에서 lint, TypeScript type check, production build, 관련 테스트를 실행한다.

Backend 변경 시 가능한 범위에서 다음을 실행한다.

- `ruff check`
- `ruff format --check`
- `pytest`
- 관련 API 실행 확인
- Alembic migration 상태 확인

DB 변경 시 migration 생성과 내용, 개발 DB 적용, downgrade 가능 여부, Seed 중복 여부, 외래키와 상태값 제약을 확인한다.

검증하지 못했다면 이유를 작업 보고에 적고, 테스트가 실패한 상태를 완료로 보고하지 않는다.

## Documentation Rules

- 의미 있는 작업 단위가 끝날 때마다 `UPDATELOG.md`에 실제 수행 내용만 한국어로 기록한다.
- `UPDATELOG.md`는 최신 날짜 항목이 위에 오도록 내림차순으로 정리한다.
- README에서 현재 동작 기능과 예정 기능을 구분한다.
- 실행 방법, 환경변수, 구조가 바뀌면 README를 갱신한다.
- 반복 오류와 해결 방법은 README의 Troubleshooting에 추가한다.
- 반복되는 프로젝트 규칙은 AGENTS.md에 반영한다.
- 데이터 모델은 `docs/DATA_MODEL.md`, API는 `docs/API_SPEC.md`, AI 입출력은 `docs/AI_DESIGN.md`에 반영한다.
- 일정과 범위는 `docs/ROADMAP.md`와 체크리스트에 함께 반영한다.

## Learning Rules

- 한 작업에서는 하나의 작은 기능 또는 마일스톤만 구현한다.
- 구현 전에 입력, 처리, 출력을 설명한다.
- 핵심 Python과 FastAPI 개념을 초급자 기준으로 설명한다.
- 완료 후 사용자가 직접 수정할 연습문제 하나를 제안한다.
- 오류가 발생하면 전체 정답 코드보다 원인을 먼저 설명한다.
- 사용자가 직접 작성·수정할 부분을 구분한다.
- 새 라이브러리의 사용 위치를 설명한다.
- 기능 완료 후 코드 없이 업무 흐름을 정리한다.

## Response / Token Usage

- 작업 보고는 짧고 핵심적으로 작성하고 긴 설명, 전체 파일 인용, 반복 요약을 피한다.
- 코드와 SQL 전체 내용은 요청받은 경우에만 응답한다.
- 파일 탐색은 필요한 범위로 제한한다.
- 완료 보고에는 변경 파일, 수정 이유, 검증 결과를 포함한다.
- 가능하면 응답에서 200줄 이상의 코드를 한 번에 출력하지 않는다.
- 큰 작업은 작은 마일스톤으로 나누며 다음 마일스톤을 승인 없이 구현하지 않는다.
