# MS FlowHub

## 2026-08-01 현재 작업 상태

오늘 직원·조직 관리 안정화와 Supabase Auth 로그인 화면을 정리했습니다.
로그인 페이지(`/login`), 로그인 성공 후 대시보드 이동, 세션이 없는 보호
페이지의 로그인 리다이렉트, 로그아웃, 현재 비밀번호를 확인하는 비밀번호
변경(`/change-password`)이 프론트엔드에 구현되어 있습니다.

`employee_accounts` 연결 모델과 Auth Seed 코드도 준비되어 있으나, 실제
Supabase에서 migration과 Seed를 실행하고 계정 로그인을 확인해야 합니다.
또한 기존 업무 API 전체의 `actor_id`를 JWT 기반 RBAC으로 교체하는 작업은
다음 단계입니다. 따라서 현재 로그인 UI가 보인다고 해서 모든 업무 API의
운영 인증이 완료된 것은 아닙니다.

내일은 아래 순서로 진행합니다.

1. `employee_accounts` migration/Auth Seed를 Supabase에 적용
2. 실제 로그인·로그아웃·비밀번호 변경·세션 유지 확인
3. API 전체 Bearer 인증과 역할별 권한 검사 전환
4. 개발용 사용자 전환 및 `actor_id` 제거, 권한별 테스트 보강
5. Jira에 개발 일정과 작업 우선순위 등록
6. 기본 대시보드의 마일스톤, 현재 구현 범위, 접근 가능 모듈, 관리자 권한 안내 정리
7. 여유가 있으면 Workspace 직원 매뉴얼 추가를 위한 기획 검토

## 현재 구현 기준 (2026-08-01)

현재 애플리케이션 DB는 Supabase PostgreSQL만 사용합니다. `backend/.env`의
`DATABASE_URL`을 설정한 뒤 Alembic migration과 Seed를 실행해야 합니다. 이전
SQLite fallback과 `backend/data/ms_flowhub.db`는 더 이상 사용하지 않습니다.

현재 직원·조직 관리에는 46명 조직 데이터, 조직도 보기, 재직·당일 근무 상태 필터,
날짜별 근태, 구조화된 사유(`reason_category`, `reason_summary`, `private_note`)가
구현되어 있습니다. 일반 상태에는 아이콘을 표시하지 않고, 사유가 있는 특수 상태만
ⓘ 아이콘으로 상세 사유를 엽니다.

완료한 작업과 이후 작업은 [UPDATELOG](./UPDATELOG.md)에 누적 기록합니다.

## Supabase PostgreSQL 연결 검증 상태

FastAPI와 Alembic은 Supabase PostgreSQL 연결만 사용한다. `MIGRATION_DATABASE_URL`이 있으면 Alembic이 우선 사용하고, 없으면 `DATABASE_URL`을 사용한다. 두 URL이 없거나 연결에 실패하면 health 오류를 반환하고 서버 시작을 중단한다.

현재 저장소 작업 환경에는 `backend/.env`와 DB URL이 없어 실제 Supabase 접속·migration·PostgreSQL 업무 흐름 검증은 보류되었다. 비밀값은 저장소에 기록하지 말고 `backend/.env.example` 형식에 맞춰 로컬 `backend/.env`에만 설정한다.

> v0.5.10: 이미지 첨부파일은 확대 미리보기와 다운로드를, 문서 파일은 다운로드를 제공한다.

개발 서버 proxy는 기본적으로 `http://127.0.0.1:8000`의 FastAPI를 사용한다. 포트 충돌이 있을 때만 `frontend/.env.local`에 `BACKEND_URL=http://127.0.0.1:8001`처럼 로컬 대상 주소를 지정할 수 있다.

## 채용 포스터 첨부 (v0.5.7)

채용 요청을 임시 저장할 때 요청 작성자 또는 관리자는 JPG, PNG, WEBP, PDF 형식의 포스터를 최대 5MB까지 첨부할 수 있다. 결재 승인으로 생성된 채용공고는 첨부 파일 이름과 열기 링크를 함께 보여 준다.

개발용 fallback에서는 파일을 `backend/data/uploads/recruitment-posters/`에 저장한다. Supabase PostgreSQL은 요청과 파일 메타데이터를 저장하며, 운영 배포의 실제 파일 저장소는 이후 Supabase Storage 등으로 교체한다. 프론트엔드는 계속 FastAPI API로만 파일을 요청한다.

전자결재·채용·영업 업무를 연결하고 생성형 AI로 반복 업무를 지원하는 사내 업무 통합 플랫폼

[Update Log](./UPDATELOG.md) · [Project Spec](./docs/PROJECT_SPEC.md) · [Roadmap](./docs/ROADMAP.md) · [Prototype Checklist](./docs/PROTOTYPE_CHECKLIST.md)

> 현재 상태: **v0.5.0 전자결재 연동 ATS Lite 첫 흐름 구현**  
> 프로토타입 목표일: **2026-08-15**

## 프로젝트 개요

MS FlowHub는 가상 회사 MS의 업무 흐름을 축소 구현하는 취업 포트폴리오 프로젝트다. 전자결재를 공통 엔진으로 사용해 채용 요청과 견적 할인 승인을 후속 업무에 연결한다. 실제 기업용 ERP 완제품이 아니며, ATS Lite와 CRM Lite는 대표 시나리오 시연 범위로 제한한다.

## 기획 배경과 해결하려는 문제

- 요청·승인·후속 업무가 분리되어 생기는 중복 입력과 상태 단절
- 채용 및 견적 문서의 반복 작성과 요약 부담
- 역할별로 다른 작성·승인 권한과 처리 이력의 추적 필요
- AI 결과를 자동 결정이 아니라 검토 가능한 초안으로 안전하게 활용할 필요

## 프로젝트 목표

- 전자결재 중심의 두 통합 업무 흐름을 끝까지 시연한다.
- 핵심 업무 규칙을 FastAPI 서비스 계층에 명확히 둔다.
- Supabase PostgreSQL과 Alembic으로 재현 가능한 데이터 구조를 만든다.
- Mock AI로 API 키 없는 시연을 보장한다.
- 초급 개발자가 입력·처리·출력, 오류 원인, 테스트를 설명할 수 있게 개발 기록을 남긴다.

## 프로토타입 범위

| 영역 | 포함 범위 | 깊이 |
|---|---|---|
| 공통 | 직원, 부서, 역할 전환, 대시보드, 알림, Seed | 시연 필수 |
| 전자결재 | 작성, 상신, 단일 승인/반려, 의견, 상태, 이력 | 핵심 구현 |
| ATS Lite | 채용 요청, 승인 후 공고, 지원자, 단계 | 대표 흐름 |
| CRM·견적 Lite | 고객, 기회, 상품, 견적, 할인 결재, 확정 | 대표 흐름 |
| AI | 7개 생성 기능, Mock/실제 Provider 인터페이스, 수정 결과 | 보조 기능 |

## 현재 구현 상태

- 완료: FastAPI/Next.js 기본 환경, 직원·부서, 역할 전환, 전자결재 작성·수정·관리자 삭제 API·상신·승인·반려·목록·상세·이력, 실제 결재 대시보드 집계
- 저장: `DATABASE_URL` 설정 시 Supabase PostgreSQL, 미설정 시 파일 기반 로컬 SQLite 개발 DB
- DB 관리: SQLAlchemy 2.0 동기 Session, 최초 Alembic migration, 멱등 샘플 직원·부서
- 구현: 채용 요청 작성·상신, 공통 전자결재 연결, 승인 시 템플릿 기반 채용공고 초안 자동 생성, 반려 동기화, 알림 저장 구조
- 미구현: Supabase 실제 접속 검증, 지원자 관리·채용 단계, CRM 업무 API, AI Provider, 배포
- ATS Lite는 채용 요청과 공고 목록만 실제 기능으로 제공하며, CRM Lite는 안내용 Mock 표시를 유지한다.

## 사용자 역할

일반 직원, 부서장, 인사 담당자, 영업사원, 영업팀장, 관리자. 프로토타입은 샘플 직원을 선택해 역할을 전환한다. 프론트에서 받은 ID를 그대로 신뢰하지 않고 FastAPI 서비스가 직원 정보를 조회한다. 현재는 시연 편의를 위해 모든 활성 샘플 직원이 채용 요청을 작성하고 모든 요청 부서를 선택할 수 있다. 직원·부서 관리 마일스톤에서 관리자가 역할과 허용 부서를 부여하는 규칙으로 교체한다.

## 핵심 업무 시나리오

### 채용

부서장 선택 → 채용 요청 작성 → AI 요약·공고 초안 → 결재 상신 → 인사 담당자 승인 → 공고 생성 → 지원자 등록·단계 변경 → AI 경력 요약·면접 질문 → 사용자 수정.

### 영업·견적

영업사원 선택 → 고객·기회·견적 작성 → 서버 금액 계산 → 10% 초과 할인 감지 → 결재와 AI 요약 → 영업팀장 승인 → 견적 확정 → AI 안내 메일 초안 → 사용자 수정.

상세 단계는 [User Flows](./docs/USER_FLOWS.md)를 참고한다.

## 주요 기능

- 허용된 결재·견적·채용 상태 전환과 재처리 방지
- 승인된 채용 요청만 공고로 변환
- 10% 이하 견적은 결재 없이 확정 가능, 초과 견적은 승인 전 확정 금지
- 금액과 할인액을 PostgreSQL `NUMERIC`/Python `Decimal` 기준으로 서버 재계산
- 공통 `ai_generations` 기록과 생성 결과 사용자 수정
- AI는 승인, 반려, 합격, 불합격, 견적 확정, 실제 발송을 자동 수행하지 않음

## 기술 스택

- Frontend: Next.js App Router, TypeScript, Tailwind CSS
- Backend: Python 3.12, FastAPI, Uvicorn, Pydantic v2, pydantic-settings
- Data: Supabase PostgreSQL, SQLAlchemy 2.0 동기 방식, Psycopg 3, Alembic
- Quality: pytest, FastAPI TestClient, Ruff
- AI: 공통 Provider 인터페이스, MockAIProvider, 환경변수 기반 실제 LLM Provider

## 전체 시스템 구조

```text
Browser (Next.js)
       │ 공통 API Client
       ▼
FastAPI Router → Service(권한·업무 규칙·트랜잭션)
                    ├─ Repository → SQLAlchemy/Psycopg → Supabase PostgreSQL
                    └─ AI Provider → Mock 또는 실제 LLM
```

프론트엔드는 Supabase 업무 테이블을 직접 조회·수정하지 않는다.

## Frontend 구조

`src/app/`은 라우팅, `features/dashboard/`는 대시보드 데이터 로딩과 화면, `components/`는 공통 UI, `lib/api-client.ts`는 API 호출, `types/`는 응답 타입을 맡는다. `storage/`는 저장 기능이 필요해질 때 추가한다.

## Backend 구조

`app/api/` → `app/services/` → `app/repositories/` 순서로 책임을 분리했다. ORM 모델은 `app/models/`, Session은 `app/db/`, API 스키마는 `app/schemas/`에 둔다. 상태 전환과 권한은 ApprovalService가 검증하고 Repository는 SQLAlchemy 조회·저장만 담당한다.

## AI Provider 구조

Service가 공통 Provider를 호출한다. `AI_PROVIDER`와 API 설정이 없으면 Mock을 사용한다. Router/UI의 직접 Provider 호출은 금지한다. 상세 내용은 [AI Design](./docs/AI_DESIGN.md)을 참고한다.

## Supabase PostgreSQL 연결 구조

FastAPI만 `DATABASE_URL`을 사용한다. migration은 필요 시 별도 `MIGRATION_DATABASE_URL`을 사용한다. Supabase 연결값이 있으면 Psycopg 3로 PostgreSQL에 연결한다. 연결값이 없으면 실행을 중단하지 않고 `backend/data/ms_flowhub.db`에 저장한다. SQLite는 로컬 개발 fallback일 뿐 배포 DB로 사용하지 않는다.

## 데이터베이스 구조

공통(`departments`, `employees`, `notifications`), 결재(`approval_documents`, `approval_histories`), 채용(`recruitment_requests`, `job_postings`, `applicants`), 영업(`customers`, `products`, `sales_opportunities`, `quotations`, `quotation_items`), AI(`ai_generations`)로 나눈다. 상세 설계는 [Data Model](./docs/DATA_MODEL.md)에 있다.

## 환경변수

실제 값은 기록하지 않는다. Backend와 Frontend의 `.env.example`에는 이름과 설명만 있다.

| 이름 | 목적 | 상태 |
|---|---|---|
| `DATABASE_URL` | Supabase PostgreSQL 연결 | 구현 |
| `MIGRATION_DATABASE_URL` | Alembic용 연결 | 예시 작성 |
| `AI_PROVIDER` | Mock/실제 Provider 선택 | 기본값 Mock |
| `AI_API_KEY` | 실제 Provider 인증 | 선택, 비밀 |
| `AI_MODEL` | 실제 모델명 | 선택 |
| `DISCOUNT_APPROVAL_THRESHOLD` | 할인 승인 기준(기본 10%) | 설정 구현 |
| `FRONTEND_ORIGIN` | CORS 허용 origin | 설정 구현 |
| `NEXT_PUBLIC_API_BASE_URL` | Frontend가 호출할 FastAPI 주소 | Frontend 예시 작성 |

## 로컬 실행 방법

Python 3.12와 Node.js가 필요하다. 두 터미널을 프로젝트 루트에서 연다.

Backend:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

- 포털: `http://localhost:3000`
- API 문서: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

환경변수 파일이 없어도 Mock 모드로 실행된다. 실제 설정이 필요하면 `.env.example`을 참고해 저장소에 커밋되지 않는 환경 파일을 별도로 만든다.

## Database Migration 방법

Supabase 연결 정보를 환경변수에 설정한 뒤 Backend에서 실행한다.

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current
```

개발 DB를 되돌리는 검증은 `alembic downgrade base`로 가능하지만 데이터가 삭제되므로 별도 테스트 DB에서만 실행한다. 최초 migration은 `20260730_0001_approval_flow.py`다.

## Seed 실행 방법

로컬 DB는 시작 시 고정 ID로 샘플 부서·직원을 멱등 생성한다. Supabase는 최초 migration이 같은 샘플 기준 데이터를 한 번 추가한다. 재실행 시 로컬 데이터는 중복 생성되지 않는다.

## 로컬 검증 명령

Backend:

```powershell
cd backend
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\pytest.exe
```

Frontend:

```powershell
cd frontend
npm run lint
npm run typecheck
npm run build
npm audit
```

## 주요 API 그룹

현재 동작 API는 Health, Departments, Employees, Dashboard, Approvals다. 전자결재는 목록·상세·작성·수정과 상신·승인·반려 명령을 제공한다. 나머지 그룹은 설계 상태이며 [API Spec](./docs/API_SPEC.md)에 구분한다.

## 프로젝트 디렉터리 구조

현재 주요 구조:

```text
project-root/
├─ .gitignore
├─ AGENTS.md
├─ README.md
├─ UPDATELOG.md
├─ docs/
   ├─ PROJECT_SPEC.md
   ├─ ROADMAP.md
   ├─ USER_FLOWS.md
   ├─ DATA_MODEL.md
   ├─ API_SPEC.md
   ├─ AI_DESIGN.md
   ├─ PROTOTYPE_CHECKLIST.md
   ├─ LEARNING_LOG.md
│  └─ DECISIONS.md
├─ backend/
│  ├─ app/{api,core,db,models,repositories,schemas,services}
│  ├─ tests/
│  ├─ migrations/
│  ├─ alembic.ini
│  ├─ pyproject.toml
│  └─ .env.example
└─ frontend/
   ├─ src/{app,components,features,lib,types}
   ├─ package.json
   ├─ package-lock.json
   └─ .env.example
```

## 테스트 전략

Service 단위 테스트로 상태 전환·권한·금액 계산을 우선 검증하고, TestClient 통합 테스트로 API와 트랜잭션을 확인한다. 테스트 데이터는 시연/운영 데이터와 분리한다. 핵심 부정 사례는 미승인 공고 생성, 미승인 할인 견적 확정, 처리된 결재 재처리, 자기 결재다.

현재 전자결재 테스트는 DRAFT 작성·수정·상신, 승인, 반려 사유, 잘못된 상태 전환, 지정 결재자 권한, 대시보드 집계를 메모리 DB에서 검증한다.

## Troubleshooting

### 로그인 후 다시 `/login`으로 이동하는 경우

#### 문제 원인

Supabase Auth 로그인은 성공했지만 백엔드 `employee_accounts`에 해당 Auth
사용자와 직원 연결이 없거나, migration·Auth Seed가 아직 적용되지 않은
상태일 수 있습니다.

#### 해결 방법

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m app.scripts.seed_auth_accounts
```

`backend/.env`의 Supabase Auth 설정과 `frontend/.env.local`의 공개 키 설정을
확인한 뒤 프론트엔드를 재시작하세요. 키 값 자체는 로그나 코드에 출력하지
않습니다.

### pytest fails before an SQLite fixture is used

#### Problem cause

The production FastAPI application validates Supabase in its lifespan. Reusing
that application in tests made the startup validation run before dependency
overrides could inject the SQLite test session.

#### Solution

Tests now use `create_app(verify_database_on_startup=False)` and override both
`get_db_session` and `get_database_health`. Production startup still requires a
reachable Supabase PostgreSQL database. Run backend tests from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

### Supabase 연결 및 Alembic 오류

#### 문제 원인

잘못된 Supabase 호스트·포트·데이터베이스명, URL 특수문자 미인코딩, Psycopg 드라이버 불일치,
pooler의 `pgbouncer` 옵션 또는 prepared statement 충돌로 연결이 실패할 수 있습니다.

#### 해결 방법

Supabase Connect의 PostgreSQL URI를 다시 복사하고 `DATABASE_URL`을 설정합니다.
Psycopg 3 의존성을 설치하고, `pgbouncer=true`를 제거하며, Alembic은 반드시
`\.venv\Scripts\alembic.exe upgrade head`로 실행합니다.

### pytest가 Supabase 연결 오류로 시작하지 않는 문제

#### 문제 원인

테스트 fixture가 SQLite 세션을 override하기 전에 FastAPI lifespan이 운영용 Supabase health check를 실행합니다.

#### 해결 방법

다음 마일스톤에서 테스트 전용 lifespan 또는 health-check override를 추가합니다. 운영 실행에서는
Supabase 연결 검사를 계속 유지합니다.

### 프론트엔드 실행 위치 및 Next.js workspace 오류

#### 문제 원인

상위 폴더의 `package-lock.json`을 Turbopack이 workspace root로 잘못 인식하거나, frontend 밖에서
명령을 실행하면 경로와 proxy 설정이 어긋날 수 있습니다.

#### 해결 방법

프로젝트 루트 launcher를 사용하거나 `frontend/` 폴더에서 실행합니다.

```powershell
.\run-backend.cmd
.\run-frontend.cmd
```

### `alembic upgrade head`에서 `database "postgres" does not exist`가 발생하는 경우

Supabase의 일반 연결 URL이 아니라 잘못된 호스트·포트·데이터베이스명이 입력된 경우입니다.
Supabase Connect 화면에서 PostgreSQL URI를 다시 복사하고 `backend/.env`의
`DATABASE_URL`과 `MIGRATION_DATABASE_URL`에 설정하세요. 비밀번호의 특수문자는 URL 인코딩해야 합니다.

### `ModuleNotFoundError: No module named 'psycopg2'`

프로젝트는 Psycopg 3를 사용합니다. backend 가상환경에서 의존성을 다시 설치하고
URL은 `postgresql://` 형식으로 두면 애플리케이션이 `postgresql+psycopg://`로 정규화합니다.

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### `invalid connection option "pgbouncer"` 또는 `DuplicatePreparedStatement`

Supabase pooler URI의 `pgbouncer=true` 옵션은 애플리케이션 URL에서 제거해야 합니다.
현재 연결 설정은 Psycopg prepared statement를 비활성화해 transaction pooler와 호환되도록 처리합니다.

### `pytest`가 테스트 DB를 만들었는데도 Supabase 연결 오류로 실패하는 경우

현재 FastAPI lifespan이 테스트 fixture의 dependency override보다 먼저 Supabase health check를
실행합니다. 따라서 SQLite 테스트 세션이 준비되어도 앱 시작 단계에서 실패할 수 있습니다.
테스트 fixture에서 lifespan을 비활성화하거나 테스트 설정에서 DB health check를 명시적으로 우회하는
작업이 다음 마일스톤입니다. 운영 실행에서는 Supabase 연결 검사를 유지해야 합니다.

### 백엔드·프론트엔드 실행 위치가 헷갈리는 경우

프로젝트 루트에서 아래 launcher를 사용하세요. 직접 실행할 때만 각각 `backend/`, `frontend/`로 이동합니다.

```powershell
.\run-backend.cmd
.\run-frontend.cmd
```

### Next.js가 상위 폴더를 workspace root로 잘못 선택하는 경우

상위 사용자 폴더에 다른 `package-lock.json`이 있으면 Turbopack이 잘못된 루트를 탐색해 접근 거부가 발생할 수 있다. `frontend/next.config.ts`의 `turbopack.root`를 Frontend 실행 폴더로 제한해 해결했다. Frontend 명령은 반드시 `frontend/`에서 실행한다.

### Python 3.12를 찾을 수 없는 경우

프로젝트 기준은 Python 3.12다. `py -0p`로 설치된 버전을 확인하고 Python 3.12 설치 후 가상환경을 다시 만든다. 이번 최초 검증 환경에는 3.11만 있어 코드 호환 검증은 3.11 가상환경에서 수행했으며 Ruff 대상은 `py312`로 유지했다.

### npm audit의 ESLint 개발 의존성 경고

production 의존성은 audit 0건이다. 전체 audit에는 ESLint 전이 의존성 `brace-expansion` 관련 high 경고가 남아 있다. 공식 수정 버전 5.0.8을 현재 ESLint 체인에 강제 적용하면 lint가 실행되지 않아 override하지 않았다. 사용자 입력을 glob 패턴으로 전달하지 말고 ESLint 생태계의 호환 업데이트 후 재검토한다.

## 프로토타입 완료 조건

- 두 핵심 시나리오를 처음부터 끝까지 시연
- Supabase PostgreSQL 저장, FastAPI 단일 업무 API 경계
- 멱등 Seed와 Mock AI의 키 없는 동작
- 금지된 상태 전환 및 권한 위반 차단
- 핵심 Backend 테스트 통과
- 문서와 실제 구현 상태 일치

## 제외 기능과 한계

실제 인증/Supabase Auth, 운영급 권한, 실제 이메일, PDF·OCR, RAG·벡터 DB, n8n, 다단계 결재, WebSocket, 실제 개인정보·기밀, Docker, 모바일, 완전한 ERP/ATS/CRM, 자동 채용 판단, 실제 견적 발송은 제외한다.

## 이후 확장 계획

프로토타입 안정화 후 인증·세분화 권한, 다단계 결재, 실제 이메일, 운영 DB 분리, 감사·관측성, CI/CD와 배포, 필요성이 검증된 문서 검색 기능을 순차 검토한다. 완성형 서비스와 실제 배포는 별도 마일스톤으로 관리한다.
# Employee organization seed

Run migrations, then seed the organization data from `backend`:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m app.scripts.seed_organization
```

The simplest backend command from the repository root is:

```powershell
.\run-backend.cmd
```

The simplest frontend command from the repository root is:

```powershell
.\run-frontend.cmd
```

The seed is idempotent: departments and teams are matched by code and employees by
employee number. It supports both the configured Supabase PostgreSQL database and
the local SQLite fallback. Start the backend with `.\.venv\Scripts\uvicorn.exe app.main:app --reload`
and the frontend with `npm run dev`; open `/employees` to verify the data.

## Supabase-only database policy

MS FlowHub now requires Supabase PostgreSQL. Set `DATABASE_URL` in `backend/.env`,
run Alembic migrations, and then run the organization seed. SQLite fallback and
the previous local `backend/data/ms_flowhub.db` database are no longer used.
