# Update Log

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
