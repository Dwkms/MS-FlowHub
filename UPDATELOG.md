# 업데이트 로그

## 목차

- [2026-08-03 · v0.6.4 Playwright E2E 기반 구성](#2026-08-03--v064-playwright-e2e-기반-구성)
- [2026-08-03 · v0.6.3 인증·권한 자동 테스트](#2026-08-03--v063-인증권한-자동-테스트)
- [2026-08-02 · v0.6.2 Supabase Auth 인증 검증](#2026-08-02--v062-supabase-auth-인증-검증)
- [2026-08-01 · v0.6.0 직원·조직 관리 안정화](#2026-08-01--v060-직원조직-관리-안정화)
- [2026-07-31 · v0.5.x 채용·승인 업무 흐름](#2026-07-31--v05x-채용승인-업무-흐름)
- [2026-07-30 · v0.1~v0.4 기반 기능](#2026-07-30--v01v04-기반-기능)

---

## 2026-08-03 · 모바일 직원·조직 관리 화면 보완

- 직원·조직 관리의 검색·필터·조직도 버튼이 중간 화면 폭에서는 한 줄을 유지하고, 모바일에서는 기존 높이의 세로 필터를 유지하도록 너비 규칙을 보완했습니다.
- 대시보드에서 현재 범위만 안내하던 마일스톤 카드를 제거했습니다.
- 조직도에 표시된 개발·마케팅·인사·기획·QA·경영진 색상을 모바일 팀 배지에도 동일한 계열로 적용했습니다.
- 모바일 직원 목록을 `직원·직급·재직 상태·근무 상태` 네 열로 재구성하고, 팀 약어 배지와 상태 중심 표시를 추가했습니다. PC 목록의 기존 전체 정보는 유지됩니다.
- 모바일 조직도 모달은 원본을 축소하지 않고 가로로 이동하며 크게 확인할 수 있도록 보완했습니다.

---

## 2026-08-03 · v0.7.0 직원 매뉴얼 MVP

### 핵심 기능

- 직원 매뉴얼 카테고리, 텍스트 본문, 이미지/PDF URL 자산 테이블과 Alembic migration을 추가했습니다.
- 목록 검색·카테고리 필터·중요 매뉴얼 상단 고정·최근 수정일, 상세 본문과 이미지 확대 보기를 구현했습니다.
- `SUPER_ADMIN`, `HR_ADMIN`만 카테고리와 매뉴얼을 작성·수정·삭제하고, `TEAM_ADMIN`, `EMPLOYEE`는
  공개 매뉴얼만 조회하도록 백엔드 권한 검증을 추가했습니다.
- 로그인·계정부터 채용 요청까지 7개 카테고리, 15개 초기 매뉴얼과 카테고리별 요약 SVG를 seed로 구성했습니다.
- Supabase PostgreSQL에 `20260803_0013` migration을 적용하고, 초기 매뉴얼 seed를 재실행해도
  중복 오류 없이 처리되는 것을 확인했습니다.
- iPhone 16 Pro 폭(402px)에서는 왼쪽 사이드바를 하단 메뉴로 전환하고, 직원 목록은 직원·부서·직급
  세 열만 표시하도록 반응형 레이아웃을 보완했습니다.
- 모바일 하단 메뉴의 비활성 항목이 숨겨지던 규칙을 제거하고, 다섯 메뉴를 동일한 폭의 탭으로
  항상 표시하도록 보완했습니다.
- `조직도 확인 방법` 매뉴얼은 임시 요약 SVG 대신 직원·조직 관리 화면의 실제 `organization-chart.png`를
  사용하도록 갱신했습니다.
- Playwright 전용 테스트 직원과 비활성 인증 테스트 계정을 정리하는 스크립트를 추가하고, 실제 테스트
  계정 데이터를 제거했습니다. E2E 실행 전에는 전용 seed로 다시 생성합니다.
- Playwright `globalSetup`과 `globalTeardown`으로 E2E 테스트 시작 전 계정을 생성하고 종료 후 자동
  정리하도록 구성했습니다.

### 검증 결과

- 매뉴얼 API 테스트 5개 통과: 목록·검색·필터·상세, 초안 비노출, HR 수정·삭제, 조회 역할 차단, seed 중복 방지.

## 2026-08-03 · v0.6.4 Playwright E2E 기반 구성

### 핵심 작업

- Chromium Playwright 환경, 실패 시 trace·screenshot 저장, E2E 실행 명령을 추가했다.
- 테스트 전용 일반 직원·SUPER_ADMIN·비밀번호 변경 계정만 환경변수에서 읽도록 구성해
  비밀번호와 토큰을 코드에 기록하지 않도록 했다.
- 기존 직원 46명을 변경하지 않고 E2E 전용 일반 직원·SUPER_ADMIN Auth 계정을 멱등으로
  생성·연결하는 seed와 중복 방지 테스트를 추가했다.
- E2E seed를 다시 실행할 때 테스트 전용 Auth 계정의 비밀번호도 환경변수 값으로 동기화하도록 보완했다.
- 환경변수 템플릿과 README를 DB·서버 전용 Supabase Auth·Frontend 공개 설정·E2E 테스트 설정으로
  구분해 정리하고, 실제 환경 파일의 값은 수정하지 않았다.
- 로그인, 세션 유지, 로그아웃, 직원 권한 범위, 직원 필터, 전자결재 승인,
  비밀번호 변경 후 복구 시나리오를 추가했다.
- 직원 화면의 검색·부서·재직 상태·근무 상태 필터에 접근성 이름을 추가해
  안정적인 E2E selector로 사용할 수 있게 했다.

### 검증 결과

- Playwright Chromium 핵심 E2E 6개 통과: 잘못된 로그인, 로그인·세션 유지·로그아웃,
  일반 직원·관리자 권한 범위, 직원 필터, 전자결재 작성·승인, 비밀번호 변경·복구
- Backend Ruff check / format check 및 전체 pytest 56개 통과
- Frontend lint, TypeScript 검사, production build 통과

## 2026-08-03 · v0.6.3 인증·권한 자동 테스트

### 핵심 작업

- Auth Seed의 계정 연결 동기화 로직을 분리해 같은 직원·Auth 사용자 목록으로 반복 실행해도
  `employee_accounts`가 중복 생성되지 않음을 자동 테스트할 수 있게 했다.
- 비활성 연결 계정과 `employee_accounts` 미연결 Auth 사용자의 보호 API 접근 차단 테스트를 추가했다.
- `TEAM_ADMIN`의 같은 팀 직원 목록 조회 성공, 일반 직원·HR 관리자의 역할 변경 차단,
  지정되지 않은 결재자의 승인 차단 테스트를 추가했다.

### 검증 결과

- Backend Ruff check 및 format check 통과
- Backend 전체 pytest 55개 통과
- Frontend lint 및 TypeScript 검사 통과
- Frontend production build 통과

## 2026-08-02 · v0.6.2 Supabase Auth 인증 검증

### 핵심 작업

- `employee_accounts` migration이 Supabase PostgreSQL에 적용된 것을 확인했다.
- Auth seed를 반복 실행해 직원 46명과 Supabase Auth 계정 46개의 1:1 연결을 확인했다.
- `SUPER_ADMIN` 1명, `HR_ADMIN` 1명, `TEAM_ADMIN` 4명, `EMPLOYEE` 40명의 역할을 확인했다.
- 활성 계정으로 로그인, 잘못된 비밀번호 거부, 보호 경로, 로그아웃, 비밀번호 변경과 원복을 검증했다.
- 비활성 연결 계정과 `employee_accounts` 미연결 Auth 계정의 접근 차단을 검증했다.
- 활성 계정의 access token이 FastAPI `/api/v1/auth/me`에서 올바른 역할로 해석되는 것을 확인했다.
- 공통 Frontend API Client가 Supabase 세션의 access token을 자동으로
  `Authorization: Bearer ...` 헤더에 포함하도록 변경했다.
- `auth/me` 호출의 수동 토큰 전달을 제거해 업무 API와 동일한 공통 인증 경로를 사용한다.
- Backend에 인증 사용자·현재 직원 조회와 `SUPER_ADMIN`, `HR_ADMIN`, `TEAM_ADMIN`,
  직원 관리·결재 권한 dependency를 추가했다.
- 직원 근무 상태와 재직 상태 사유 API를 `AuthenticatedActor` 기반으로 전환해
  `actor_id` query를 인증 주체로 사용하지 않도록 했다.
- 직원 관리 Frontend API에서도 상태 변경 요청의 `actor_id` query 전송을 제거했다.
- 전자결재 제출 API와 Frontend 호출에서 `actor_id`를 제거하고, 제출 이력을
  Bearer token의 현재 직원으로 기록하도록 전환했다.
- 전자결재 승인·반려 API와 Frontend 호출에서도 `actor_id`를 제거하고, 지정 결재자 또는
  `SUPER_ADMIN`만 Bearer token 기준으로 처리하도록 전환했다.
- 전자결재 작성·수정·삭제·목록 API도 Bearer token으로 현재 사용자를 식별하도록 전환하고,
  `author_id`, `actor_id`, `employee_id`를 인증 주체로 받지 않도록 정리했다.
- 채용 요청 작성·상신·포스터 첨부·삭제·채용공고 생성 API도 Bearer token 기준으로 전환하고,
  `requester_id`와 `actor_id`를 인증 주체로 받지 않도록 정리했다.
- 채용 요청·포스터·채용공고 조회 API도 Bearer token 기준으로 전환하고, 포스터 파일은
  공통 API Client가 인증 헤더와 함께 받아 미리보기·다운로드하도록 정리했다.
- 대시보드와 직원 상세 조회에서 사용자 ID query를 제거하고, Supabase JWKS 서명 검증 후
  `employee_accounts` 역할을 조회하도록 인증 경로를 정리했다.
- 직원 생성·수정·비활성화 API를 `SUPER_ADMIN`과 `HR_ADMIN` 권한으로 제한해 일반 직원의
  직원 관리 변경 요청을 차단했다.
- `TEAM_ADMIN`은 같은 팀 직원의 근태·재직 상태 사유만 변경할 수 있고, 다른 팀 변경은
  서버에서 차단하도록 권한 규칙을 보강했다.
- 전자결재 작성자는 관리자 역할이어도 본인 문서를 승인·반려할 수 없게 하고,
  `TEAM_ADMIN`은 같은 팀 작성 문서만 처리하도록 권한 규칙을 보강했다.
- 직원 목록·상세 조회도 역할 범위로 제한해 `SUPER_ADMIN`·`HR_ADMIN`은 전체,
  `TEAM_ADMIN`은 같은 팀, 일반 직원은 본인 정보만 조회하도록 정리했다.
- 직원 역할 변경 API를 추가하고 `SUPER_ADMIN`만 `employee_accounts.role`을 변경할 수 있도록
  제한했다. 일반 직원과 HR 관리자의 역할 변경 요청은 차단한다.
- 역할 변경 시 수행자·대상·변경 전후 역할을 Backend 감사 로그로 기록하도록 추가했다.
- Supabase JWT의 JWKS 검증이 프로젝트 서명 방식과 맞지 않을 때도, Supabase 사용자 조회로
  토큰을 다시 검증해 로그인 세션이 중단되지 않도록 호환 경로를 추가했다.
- 기존 `ADMIN`/`HR_MANAGER` 레거시 판정을 Supabase Auth 역할과 함께 처리하도록 보완했다.
- README에서 완료 전 단계 안내와 중복된 과거 실행 설명을 정리하고, 실제 인증·Bearer JWT·RBAC
  구현 상태 및 1~4단계에서 확인한 로그인·권한·Network·테스트 오류 대응 방법을 Troubleshooting에 반영했다.

### 검증 결과

- Backend Ruff check / format check 통과
- 직원 상태 API의 Bearer 인증 누락 요청 `401` 테스트 통과
- 전자결재 제출 API의 Bearer 인증 누락 요청 `401` 테스트 통과
- 전자결재 승인·반려 API의 Bearer 인증 누락 요청 `401` 테스트 통과
- 전자결재 작성·수정·삭제·목록 API의 Bearer 인증 누락 요청 `401` 테스트 통과
- 채용 요청 변경 API의 Bearer 인증 누락 요청 `401` 테스트 통과
- 채용 요청 조회 API의 Bearer 인증 누락 요청 `401` 테스트 통과
- 대시보드 Bearer 인증 누락 요청 `401` 테스트 통과
- 일반 직원의 직원 관리 변경 요청 `403`, HR 관리자의 직원 수정 요청 성공 테스트 통과
- 역할 변경 API의 `SUPER_ADMIN` 허용·HR 관리자 차단 테스트 통과
- Backend pytest 50개 통과
- Supabase Auth seed 반복 실행 시 중복 없음
- Frontend lint, TypeScript 검사, production build 통과

## 2026-08-01 · v0.6.0 직원·조직 관리 안정화

### 핵심 작업

- 46명 직원의 부서·팀·관리자 관계, 검색·필터·상세 API와 조직도 조회를 정리했다.
- 일일 근무 상태, 휴가·근무 사유, 공개 요약과 관리자 전용 메모를 추가했다.
- 조직도 이미지, 상태 정보 아이콘, 직원 관리 화면을 연결했다.
- SQLite fallback을 제거하고 Supabase PostgreSQL 전용 실행 구조로 정리했다.
- 백엔드·프론트엔드 실행 명령을 추가했다.
- Supabase Auth 로그인 화면, 세션 보호, 로그아웃, 비밀번호 변경 화면을 구현했다.

### 검증 결과

- Backend API 테스트 fixture를 Supabase lifespan과 분리했다.
- 직원·조직 관련 Backend pytest와 Frontend lint/build를 확인했다.

## 2026-07-31 · v0.5.x 채용·승인 업무 흐름

### 핵심 작업

- Supabase PostgreSQL 기반 Alembic migration 구조를 정리했다.
- 전자결재 작성·수정·제출·승인·반려와 이력·알림을 구현했다.
- 채용 요청, 결재 연계, 채용 공고, 지원자 단계 흐름을 구현했다.
- 채용 포스터 첨부·미리보기·다운로드와 권한 검사를 추가했다.
- 프론트엔드에서 공통 API client와 업무 화면을 연결했다.

### 검증 결과

- 주요 Backend Ruff·pytest와 migration upgrade/downgrade를 확인했다.
- Frontend lint, TypeScript 검사, production build를 확인했다.

## 2026-07-30 · v0.1~v0.4 기반 기능

### 핵심 작업

- FastAPI·Next.js 기본 구조와 공통 설정을 구성했다.
- 부서·직원·대시보드 조회와 초기 직원·조직 seed를 추가했다.
- 전자결재 문서·이력 모델과 승인 상태 흐름을 구현했다.
- SQLAlchemy 2.0 동기 Session, Repository, Service 계층을 정리했다.
- Supabase PostgreSQL용 초기 Alembic migration과 개발 환경 검증 구조를 추가했다.

### 기록 원칙

- 날짜별로 핵심 기능만 하나의 버전 묶음으로 기록한다.
- 같은 날짜의 세부 작업을 별도 제목으로 반복하지 않는다.
- 검증하지 않은 내용은 완료된 것으로 기록하지 않는다.
