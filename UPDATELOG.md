# Update Log

## 2026-08-01 오늘 작업 종합

### 완료한 기능

- Supabase PostgreSQL 단일 DB와 46명 직원·조직 Seed를 유지했습니다.
- 날짜별 근무 상태, 재직 상태, 상태별 공개 사유와 비공개 상세 사유를
  직원·조직 관리 화면과 API에 연결했습니다.
- 조직도 이미지 보기, 상태 정보 아이콘·상세 모달, 필터 URL 유지 기능을
  구현했습니다.
- 직원관리 API 테스트 fixture를 운영 Supabase lifespan과 분리했습니다.
  SQLite 테스트 세션과 health dependency를 override로 주입할 수 있습니다.
- 채용 요청 결재자는 팀장급 이상으로 제한하고, 경영진 부서는 요청 부서
  선택에서 제외했습니다. 부서장 표기는 실제 부서명 기반으로 변경했습니다.
- 대시보드 새로고침 시 임시 사용자 ID로 먼저 요청하던 문제를 수정했습니다.
- Supabase Auth 브라우저 환경변수, 로그인·로그아웃, 세션 보호, 로그인 성공 후
  대시보드 이동, 현재 비밀번호 검증 방식의 비밀번호 변경 화면을 추가했습니다.
- 상단 사용자 전환 UI를 제거하고 사이드바 하단 설정 메뉴에 비밀번호 변경과
  로그아웃을 배치했습니다.

### 오늘 검증한 결과

- Backend Ruff check/format 통과
- Backend API 테스트 34개 통과
- Frontend `npm run lint` 통과
- Frontend `npm run build` 통과

### 아직 완료로 보지 않는 항목

- `employee_accounts` migration과 Auth Seed는 코드가 준비되었지만 실제 Supabase
  환경에서 migration 적용·46개 계정 생성·로그인 실동작 확인이 필요합니다.
- 기존 전자결재·직원 API 전체가 아직 Supabase Auth JWT와 RBAC dependency로
  완전히 전환된 상태는 아닙니다. 일부 API에는 기존 개발용 actor 파라미터가 남아
  있으므로 운영 인증 완료로 표시하지 않습니다.

### 내일 권장 순서

1. Supabase에서 `employee_accounts` migration 적용 및 Auth Seed 실행
2. 실제 계정 1개로 로그인·로그아웃·비밀번호 변경·새로고침 세션 유지 확인
3. FastAPI의 모든 보호 Router에서 Bearer 토큰과 employee_accounts 역할을 검증
4. SUPER_ADMIN/HR_ADMIN/TEAM_ADMIN/EMPLOYEE별 직원·결재 접근 테스트 추가
5. 개발용 현재 사용자 전환·actor_id 경로 제거 후 프론트 API client에 access token 연결
6. Auth 실패, 비활성 계정, 직원 연결 누락, 권한 부족 시나리오의 E2E 검증
7. Jira에서 다음 작업 일정과 우선순위를 정리하고 개발 진행 상황을 연결
8. 기본 대시보드의 마일스톤·현재 구현 범위·접근 가능 모듈·관리자 권한 안내 문구 점검
9. 여유가 있으면 Workspace 내 직원 매뉴얼의 대상 사용자·목차·운영 방식을 기획

## 2026-08-01 Authenticated password change

- Replaced the recovery-email page with an authenticated password-change page.
- The page verifies the current password, requires a matching new-password
  confirmation, then updates the Supabase Auth password.
- Added the entry point beside the logged-in user information in the top bar.

### Verification

- `npm run lint`: passed
- `npm run build`: passed

## 2026-08-01 Password recovery flow

- Added a password-change link below the login button.
- Added `/reset-password` for Supabase recovery-email delivery and new-password
  submission after the recovery link opens the application.

### Verification

- `npm run lint`: passed
- `npm run build`: passed

## 2026-08-01 Supabase Auth login page and session gate

- Added `/login` with email/password sign-in through Supabase Auth.
- Added a session guard that redirects unauthenticated visitors from the portal
  to `/login`, restores Supabase sessions, and sends a successful login to the
  dashboard.
- Replaced the top-bar development user switcher with authenticated-user
  display and a Supabase logout action.

### Verification

- `npm run lint`: passed
- `npm run build`: passed

## 2026-08-01 Supabase Auth frontend environment setup

- Added public Supabase URL and publishable-key placeholders to
  `frontend/.env.local` and `frontend/.env.example`.
- Added a guarded browser-client factory using only
  `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.
  It reports missing configuration without exposing key values.
- Added the official `@supabase/supabase-js` browser dependency.

### Verification

- `npm run lint`: passed
- `npm run build`: passed

## 2026-08-01 Dashboard refresh stability

- Delayed dashboard loading until the current-user employee list is resolved.
  This prevents the removed fallback ID (`emp-head`) from producing an
  intermittent dashboard 404 during refresh.
- The fallback dashboard is now used quietly when the employee-options API is
  unavailable, while real dashboard failures still display their warning.
- Cleared the dashboard warning after a successful dashboard response.

### Verification

- `npm run lint`: passed
- `npm run build`: passed

## 2026-08-01 Recruitment request approver scope

- Restricted recruitment-request approvers to team-leader level and above in
  both the form and backend Service validation.
- Removed the executive department from the recruitment-request department
  selector and reject it server-side while preserving CEO organization data.
- Replaced generic department-head option labels with actual department labels
  such as `개발팀장` and `마케팅팀장`.

## 2026-08-01 Employee organization stabilization refactor

### Changed

- Added `create_app()` so tests create an application without the production
  Supabase startup check; production `app` still verifies Supabase at startup.
- Converted database session creation to lazy runtime initialization. Test
  SQLite sessions and database health are injected with FastAPI dependency
  overrides and never open a Supabase connection.
- Added an `ActorContext` dependency bridge and centralized status rules and
  employee-status authorization outside Routers and Services.
- Moved organization-tree access behind `EmployeeService`; employee Router now
  receives requests and returns service responses only.
- Recovered the complete API suite with isolated workflow fixture identities,
  and added coverage for combined status filters, mandatory sick-leave reasons,
  private-note redaction, and administrator viewing.
- Reviewed model boundaries for future `attendance_change_histories` and
  `employee_leave_periods`; no tables or production data were changed.

### Verification

- `ruff check app tests`: passed
- `ruff format --check app tests`: passed
- `pytest -q`: 33 passed (one third-party TestClient deprecation warning)

## 2026-08-01 현재 구현 정리

### 완료한 작업

- SQLite 런타임 fallback과 로컬 DB 파일을 제거하고 Supabase PostgreSQL 단일 연결로 통일했습니다.
- `run-backend.cmd`, `run-frontend.cmd`를 추가해 프로젝트 루트에서 서버를 간단히 실행할 수 있게 했습니다.
- 조직도·부서·팀·직원 46명 데이터를 Supabase에 연결하고 멱등 Seed를 구성했습니다.
- 직원 목록에 검색, 부서, 재직 상태, 당일 근무 상태 필터와 URL 쿼리 보존을 추가했습니다.
- `attendance_records`와 날짜별 근무 상태, 체크인·체크아웃, 중복 방지 제약을 추가했습니다.
- 조직도 이미지 확대 모달을 추가하고 과거 테스트 직원·빈 테스트 부서 데이터를 정리했습니다.
- `BEFORE_WORK` 상태를 제거하고 기록이 없는 상태는 `-`로 표시하도록 변경했습니다.
- 근무·휴직 사유를 `reason_category`, `reason_summary`, `private_note`로 분리했습니다.
- 병가·결근·휴직의 공개 사유 필수 입력, 일반 근무 상태의 사유 아이콘 비노출, 정보 아이콘 상세 모달을 구현했습니다.
- 병가·휴직의 비공개 상세는 관리자와 인사담당자만 조회하도록 제한했습니다.

### DB 마이그레이션

- `20260801_0006_employee_organization`
- `20260801_0007_attendance_records`
- `20260801_0008_remove_before_work`
- `20260801_0009_remove_legacy_departments`
- `20260801_0010_employee_status_reasons`
- `20260801_0011_structured_status_reasons`

### 검증 결과

- Supabase 직원 46명, 오늘 근태 46건 확인
- Seed 반복 실행 시 직원·근태 중복 생성 없음 확인
- Ruff check / format check 통과
- Frontend ESLint, TypeScript, production build 통과
- SQLite 메모리 서비스 검증: 필수 사유, 공개·비공개 권한, 일반 상태 아이콘 비노출 확인
- 기존 `pytest` 30개는 테스트 fixture가 DB override 전에 Supabase 연결을 강제하는 구조 때문에 앱 lifespan 단계에서 실패

### 이후 작업

- 테스트 fixture에서 Supabase health check를 격리하고 전체 API 테스트를 복구합니다.
- 실제 인증·Supabase Auth와 관리자·인사·직속 관리자 권한을 세션 기반으로 연결합니다.
- 근무 상태 변경 이력, 기간형 휴직, 사유 수정 이력을 추가합니다.
- 직원별 근태 이력·월간 조회와 관리자 일괄 입력을 추가합니다.
- Supabase Storage, 운영 배포, CI/CD와 E2E 테스트를 구성합니다.

## 2026-08-01 문서화 규칙 보완

- README Troubleshooting 항목을 `문제 원인`과 `해결 방법` 문단으로 구분했습니다.
- 앞으로 발생하는 오류도 동일한 형식과 재현·검증 명령을 함께 기록합니다.

## [2026-08-01] Employment and daily work status

- Added date-based attendance records, combined employee filters, and status badges.
- Seeded today's attendance for all 46 employees and randomized ten active employees' work statuses.

## [2026-08-01] Organization chart image and legacy data cleanup

- Removed five legacy placeholder employee records from Supabase.
- Added an organization-chart button next to the employee status filter and an enlarged image modal.

## [2026-08-01] Supabase-only database runtime

- Removed the SQLite fallback, automatic local schema creation, and local SQLite database file.
- Backend startup now requires a reachable Supabase `DATABASE_URL`.

## [2026-08-01] Backend launcher

- Added `run-backend.cmd` to start FastAPI with the project virtual environment.
- Added `run-frontend.cmd` to start the Next.js development server.

## [2026-07-31] Supabase 연결 및 migration 완료

### Changed

- `backend/.env`의 Supabase 애플리케이션·migration URL을 Psycopg 3 형식으로 정리하고 비밀번호 특수문자를 URL 인코딩했다.
- `sslmode=require`를 적용하고 Psycopg가 처리하지 못하는 `pgbouncer=true` 옵션을 제거했다.
- Alembic migration `20260731_0001`부터 `20260731_0005`까지 Supabase PostgreSQL에 적용했다.
- 조직·직원, 전자결재, 알림, 채용 요청, 채용공고 테이블과 초기 부서·직원 데이터를 생성했다.
- 전체 구현 범위와 다음 작업인 직원관리프로세스를 `docs/IMPLEMENTATION_SUMMARY.md`에 정리했다.

### Verification

- Alembic revision: `20260731_0005 (head)`
- Supabase 연결: 성공
- migration DB 연결: 성공
- 핵심 테이블 생성 여부: 성공
- 초기 데이터: departments 5건, employees 5건

### Next

- 직원 등록·조회·수정·비활성화 및 부서·역할 변경 프로세스 구현

## [v0.5.11] - 2026-07-31

### Changed

- DB health 확인이 실제 SQLAlchemy 연결을 검사하도록 보완
- `DATABASE_URL` 설정 후 Supabase 연결 실패 시 SQLite fallback으로 오인하지 않고 서버 시작을 중단하도록 보완
- Alembic의 `MIGRATION_DATABASE_URL` 우선 사용과 PostgreSQL URL 예시를 문서화

### Verification

- 로컬 SQLite migration head와 seed 2회 멱등성 확인
- 연결 실패 health 테스트 추가, Backend 테스트 30개 통과

### Notes

- 실행 환경에 `backend/.env`와 실제 DB URL이 없어 Supabase PostgreSQL 연결 및 PostgreSQL smoke test는 수행하지 못함

## [v0.5.10] - 2026-07-31

### Added

- 이미지 첨부파일의 확대 미리보기 모달과 다운로드 버튼
- 문서 첨부파일의 다운로드 전용 동작과 파일 종류 표시

### Changed

- 채용 포스터 공통 첨부 영역을 이미지와 문서 파일의 확인 방식에 맞게 구분

### Verification

- Frontend type check, lint, production build 실행

## [v0.5.9] - 2026-07-31

### Added

- 채용 요청 상세와 연결된 전자결재 상세에서 채용 포스터 첨부파일을 열어보는 공통 표시 영역

### Changed

- 채용공고 목록, 채용 요청, 전자결재 화면이 같은 포스터 첨부 표시 컴포넌트를 사용하도록 정리

### Verification

- 전자결재가 연결된 채용 요청의 첨부파일 조회 권한을 기존 API 테스트 범위와 Frontend build로 확인

## [v0.5.8] - 2026-07-31

### Changed

- 채용 요청 작성과 요청 부서 선택을 모든 활성 샘플 직원에게 허용
- 기존 역할별 요청 부서 제한은 향후 직원·부서 관리에서 관리자가 역할과 허용 부서를 부여하는 방식으로 재도입 예정

### Verification

- 역할이 일반 직원인 영업사원이 다른 부서의 채용 요청을 생성하는 API 테스트 추가

## [v0.5.7] - 2026-07-31

### Added

- 채용 요청 임시 저장 단계의 채용 포스터 첨부·열기 API와 로컬 개발용 파일 저장소
- 승인 후 생성된 채용공고에서 포스터 파일을 확인하는 첨부 영역

### Changed

- 채용공고 화면을 단일 텍스트 본문 대신 모집 요약, 주요 업무, 필수 역량, 우대 사항으로 구분해 표시
- `20260731_0005_recruitment_poster.py` migration으로 포스터 메타데이터를 채용 요청에 연결

### Verification

- Backend Ruff, pytest 29개, 로컬 Alembic upgrade head 확인

### Notes

- 프로토타입의 첨부 파일은 `backend/data/uploads/recruitment-posters/`에 저장된다. Supabase 배포 환경의 파일 저장소 연동은 이후 확장 범위다.

## [v0.5.6] - 2026-07-31

### Changed

- 관리자가 지정 결재자가 아닌 전자결재도 승인·반려할 수 있도록 역할 기반 결재 권한 확장
- 전자결재 상세 화면에서 관리자에게 결재 대기 문서의 승인·반려 버튼 표시

## [v0.5.5] - 2026-07-31

### Added

- 관리자 전용 채용 요청 삭제 API와 상세 화면 삭제 버튼

### Changed

- 채용 요청 삭제 시 연결된 채용공고, 전자결재 문서·이력, 관련 알림을 하나의 트랜잭션으로 함께 정리

### Verification

- 관리자 삭제·비관리자 차단·연결 데이터 삭제 테스트 추가

## [v0.5.4] - 2026-07-31

### Fixed

- 브라우저가 FastAPI에 직접 요청하던 방식을 Next.js `/api/*` proxy 경유 방식으로 변경
- 로컬 브라우저와 개발 서버의 `localhost`/`127.0.0.1` 주소 해석 차이로 화면에서 API 연결이 실패할 수 있던 문제 수정

### Notes

- `next.config.ts` 변경 후에는 Frontend 개발 서버를 반드시 재시작해야 한다.

## [v0.5.3] - 2026-07-31

### Fixed

- Frontend 기본 API 주소를 `localhost`에서 `127.0.0.1`로 통일해 Windows 로컬 개발 환경의 API 연결 지연·실패 가능성을 제거

## [v0.5.2] - 2026-07-31

### Fixed

- API 연결 전 fallback 현재 사용자가 이전 부서장 정보로 남아 요청 부서 선택이 잠기던 문제 수정
- fallback 사용자도 `김민성 · 관리자`로 DB Seed와 일치시켜, 관리자에게 전체 부서 선택을 제공

## [v0.5.1] - 2026-07-31

### Fixed

- 채용 요청 작성 화면에서 부서 API가 비어 있거나 초기 연결이 늦을 때 요청 부서 선택 목록이 비어 보이던 문제를 수정
- 공통 fallback 부서 목록으로 개발팀·재무팀·인사팀·영업팀·서비스기획팀을 항상 표시

### Verification

- Frontend TypeScript type check, ESLint, production build 실행

## [v0.5.0] - 2026-07-31

### Added

- 채용 요청 작성·목록·상세 및 상신 API와 ATS Lite 화면
- 공통 전자결재와 채용 요청의 관련 업무 연결
- 승인 시 템플릿 기반 채용공고 초안 자동 생성, 반려 상태 동기화
- `20260731_0004_recruitment_flow.py` migration과 채용 요청 핵심 API 테스트

### Database

- `approval_documents.related_type`, `related_id`, `notifications`, `recruitment_requests`, `job_postings` 추가

### Verification

- Backend Ruff, pytest 24개, migration upgrade/downgrade 확인
- Frontend TypeScript type check, ESLint, production build 확인

### Notes

- 지원자 관리·채용 단계·AI 생성은 다음 ATS 마일스톤이며 이번 버전에 포함하지 않았다.
- 실제 Supabase 접속 정보가 없어 원격 PostgreSQL 적용은 검증하지 못했다.

최신 버전을 위에 기록한다. 기능 마일스톤은 Minor, 작은 오류 수정은 Patch, 공개 가능한 완성 버전은 Major 변경을 검토한다. 실제 수행하지 않은 작업·검증·배포는 기록하지 않는다.

## [v0.4.5] - 2026-07-31

### Changed

- 전자결재 목록의 관리 열과 삭제 버튼을 제거
- 관리자 삭제는 전자결재 상세 화면에서만 제공하도록 변경

### Verification

- Backend Ruff·포맷 검사와 pytest 16개 테스트 통과
- Frontend ESLint, TypeScript type check, production build 통과
- 실행 서버 API v0.4.5 및 전자결재 목록 HTTP 200 확인

## [v0.4.4] - 2026-07-31
## [v0.4.4] - 2026-07-31

### Changed

- 전자결재 삭제 권한을 임시 저장 작성자 기준에서 관리자 역할 전용으로 변경
- 관리자는 모든 상태의 전자결재를 삭제하고 전체 문서 목록을 조회할 수 있게 변경
- 전자결재 상세와 목록의 삭제 버튼을 관리자에게만 표시

### Verification

- 관리자의 타인 결재 대기 문서 삭제, 일반 역할의 본인 임시 문서 삭제 거부, 관리자 전체 목록 조회 테스트 추가
- Backend Ruff·포맷 검사와 pytest 16개 테스트 통과
- Frontend ESLint, TypeScript type check, production build 통과
- 실행 서버에서 인사 담당자 작성·상신 → 관리자 전체 목록 조회 → 관리자 삭제 204 확인

### Notes

- 삭제 권한은 특정 직원 이름이 아니라 DB의 `ADMIN` 역할로 판단하므로 이후 직원 관리에서 관리자 역할을 부여하면 자동 적용된다.

## [v0.4.3] - 2026-07-31

### Added

- 전자결재 임시 저장 문서 삭제 API와 목록·상세 화면 삭제 버튼

### Changed

- 임시 저장 문서는 작성자 또는 관리자가 삭제할 수 있고, 결재 요청 이후 문서는 삭제하지 않도록 보호

### Verification

- 임시 저장 삭제, 타인 삭제 거부, 상신 후 삭제 거부 테스트 추가
- Backend Ruff·포맷 검사와 pytest 15개 테스트 통과
- Frontend ESLint, TypeScript type check, production build 통과
- 실행 서버에서 임시 문서 생성 → DELETE 204 → 재조회 404 확인

## [v0.4.2] - 2026-07-30

### Changed

- 샘플 기안자를 김민성 관리자로 변경
- 김민성 관리자만 모든 기안 부서를 선택할 수 있게 변경하고, 다른 역할은 소속 부서 기안 규칙을 유지

### Database

- `20260730_0003_make_project_owner_admin.py`: 기존 샘플 기안자의 이름·이메일·역할을 관리자 권한으로 갱신

### Verification

- 관리자의 타 부서 기안 허용과 일반 역할의 타 부서 기안 차단 테스트 추가
- Backend Ruff·포맷 검사와 pytest 13개 테스트 통과
- Frontend ESLint, TypeScript type check, production build 통과
- Alembic migration upgrade/current/downgrade 및 김민성 관리자 작성 화면 확인

## [v0.4.1] - 2026-07-30

### Added

- 전자결재 기안 부서 목록 확인용 샘플 부서: 개발팀, 재무팀

### Changed

- 전자결재 작성 화면의 기안 부서 선택을 현재 사용자 소속 부서 고정에서 목록 선택 방식으로 변경

### Database

- `20260730_0002_add_sample_departments.py`: Supabase PostgreSQL에 샘플 부서 2개를 추가하는 Alembic data migration

### Verification

- 부서 목록 API가 5개 샘플 부서를 반환하는 테스트 추가

### Notes

- 기존 로컬 DB는 다음 Backend 재시작 시 중복 없이 새 부서를 자동 추가한다.

## [v0.4.0] - 2026-07-30

### Added

- 전자결재 문서 목록·검색·상태 필터와 작성·상세 화면
- 임시 저장, 결재 상신, 지정 결재자 승인·반려, 반려 사유와 처리 이력
- SQLAlchemy ORM 기반 조직·전자결재 Repository와 동기 Session
- Supabase PostgreSQL용 최초 Alembic migration (`20260730_0001_approval_flow.py`)
- Supabase 미설정 시 새로고침 후에도 유지되는 로컬 SQLite 개발 저장소
- 현재 사용자 storage 레이어와 공통 PortalShell, 경로별 활성 메뉴
- 실제 전자결재 대기 집계와 최근 업무의 대시보드 연동

### Changed

- 직원·부서 조회를 상수 Mock Repository에서 SQLAlchemy Repository로 전환
- 전자결재 최근 업무만 실제 API 데이터로 전환하고 ATS/CRM Mock 표시는 유지
- Backend/Frontend 버전을 v0.4.0으로 갱신

### Database

- `departments`, `employees`, `approval_documents`, `approval_histories` 생성
- 결재 상태 CHECK, 직원·부서 FK, 목록 조회 index와 멱등 샘플 조직 데이터 추가
- 별도 SQLite 테스트 DB에서 migration upgrade/current/downgrade 검증

### Verification

- Backend Ruff와 포맷 검사 통과
- FastAPI TestClient 10개 테스트 통과
- Frontend ESLint, TypeScript type check, production build 통과
- API 작성→상신→승인, 작성→상신→반려 및 재조회 지속성 확인
- 브라우저 목록·검색·필터·작성·승인·반려·상태 새로고침·대시보드 연동 확인

### Notes

- 실제 Supabase 접속정보가 없어 원격 DB 적용은 검증하지 않았다.
- 프로젝트 기준은 Python 3.12이나 현재 PC에는 3.11만 있어 이번 검증도 3.11 가상환경에서 수행했다.
- ATS Lite, CRM Lite, 인앱 알림 저장은 이번 범위에서 구현하지 않았다.
- 로컬 DB는 `backend/data/ms_flowhub.db`이며 Git 추적에서 제외된다.

## [v0.2.0] - 2026-07-30

### Added

- FastAPI Backend 기본 구조와 공통 설정 (`backend/app/`)
- Mock 부서·직원 Repository와 역할별 대시보드 Service
- Health, Departments, Employees, Dashboard API
- Next.js App Router, TypeScript, Tailwind CSS 기반 업무 포털 첫 화면
- 공통 Frontend API Client와 Backend 미연결 fallback
- Backend/Frontend 환경변수 예시와 저장소 `.gitignore`
- FastAPI TestClient 기본 API 테스트 5개

### Fixed

- 로컬 `localhost`와 `127.0.0.1` 개발 주소의 CORS 불일치
- 상위 lockfile을 workspace root로 잘못 인식하던 Turbopack 탐색 범위
- Next.js production 전이 의존성 보안 취약점 override

### Verification

- Backend: `ruff check`, `ruff format --check`, `pytest` 통과
- Frontend: ESLint, TypeScript type check, production build 통과
- npm production dependency audit 취약점 0건
- HTTP Health·직원·영업사원 대시보드와 Frontend 200 응답 확인
- 브라우저에서 API 연결, 사용자 역할 전환, 접근 모듈 변경, 콘솔 오류 없음 확인

### Notes

- 실제 Supabase 연결, ORM 모델, Alembic 초기화, DB Seed는 아직 구현하지 않았다.
- 프로젝트 기준은 Python 3.12이나 현재 PC에는 3.11만 있어 최초 런타임 검증은 3.11 가상환경에서 수행했다.
- 전체 npm audit에는 ESLint 개발 도구의 `brace-expansion` high 9건이 남아 있다. 현재 수정 버전 강제 적용은 ESLint를 깨뜨려 적용하지 않았으며 production 의존성에는 포함되지 않는다.
- 전자결재·ATS·CRM·AI 메뉴는 다음 마일스톤 이후 구현 예정이다.

## [v0.1.0] - 2026-07-30

### Added

- MS FlowHub 최초 프로젝트 기획 문서 (`docs/PROJECT_SPEC.md`)
- 개발 작업 공통 규칙 (`AGENTS.md`)
- README 기본 구조와 기획 단계 안내 (`README.md`)
- 채용 및 영업·견적 업무 흐름 초안 (`docs/USER_FLOWS.md`)
- 데이터 모델과 API 명세 초안 (`docs/DATA_MODEL.md`, `docs/API_SPEC.md`)
- AI Provider 설계 초안 (`docs/AI_DESIGN.md`)
- 로드맵, 프로토타입 체크리스트, 학습 기록 템플릿, 설계 결정 기록

### Verification

- 요청된 12개 문서 파일 존재 여부 확인
- 문서 내 프로젝트명, 회사명, 목표일, 기술 기준, 범위 핵심어 정적 검색
- Markdown 기본 구조와 내부 상대 링크 점검

### Notes

- 애플리케이션 코드, DB, API, AI 연동은 아직 구현되지 않았다.
- 다음 마일스톤은 공통 프로젝트 환경과 Supabase 개발 프로젝트 준비이며 사용자 승인 후 시작한다.
- 2026-08-15 프로토타입은 채용 및 영업·견적 대표 흐름의 시연을 범위로 한다.

## Version Plan

- v0.2.0: 공통 프로젝트 환경
- v0.3.0: 직원·부서·역할 전환
- v0.4.0: 전자결재
- v0.5.0: ATS Lite
- v0.6.0: CRM·견적 Lite
- v0.7.0: 공통 AI Provider
- v0.8.0: 통합 업무 흐름
- v0.9.0: 프로토타입 안정화
- v1.0.0: 포트폴리오 공개 버전
# v0.6.0 - Employee organization management

## 2026-08-01 - Remove before-work attendance status

- Removed the `BEFORE_WORK` option from the employee work-status filter.
- Employees without an attendance record now show `-`; legacy `BEFORE_WORK` records
  are migrated to `OFF_WORK`.

## 2026-08-01 - Clean up legacy organization data

- Kept empty approval and recruitment tables because their implemented APIs and screens use them.
- Added a guarded migration to remove only the empty legacy `FINANCE`, `PRODUCT`, and `SALES`
  department records; departments with employees or teams are not removed.

## 2026-08-01 - Employee status reasons

- Added employee-entered reasons for sick leave, half days, and long-term leave.
- Added self-or-admin-only status update APIs and detail-modal reason viewing.

## 2026-08-01 - Structured status reason disclosure

- Replaced repeated list-row reason text with compact info icons shown only when a reason exists.
- Added public reason summaries, private notes, registrant, and registration time for daily and
  employment-status reasons; private notes are limited to administrators and HR managers.

- Added department/team/employee relationship fields and an Alembic migration.
- Added idempotent 46-person organization seed data, employee search/filter/detail APIs, and organization tree API.
- Connected the new employee management page to the shared API client.
