# MS FlowHub

## 현재 구현 상태

- Supabase PostgreSQL과 Alembic migration만 사용합니다.
- Supabase Auth 로그인, 로그아웃, 비밀번호 변경, 보호 경로 세션 검사를 제공합니다.
- `employee_accounts`로 Auth 사용자와 직원·역할을 연결합니다. 46개 직원 계정의 연결과
  seed 재실행 시 중복이 생기지 않음을 확인했습니다.
- 공통 API Client가 Supabase access token을 `Authorization: Bearer` 헤더에 자동 포함하고,
  백엔드는 토큰으로 현재 사용자를 식별합니다. 업무 API는 `actor_id` 같은 사용자 식별 query를
  인증 수단으로 사용하지 않습니다.
- 역할은 `SUPER_ADMIN`, `HR_ADMIN`, `TEAM_ADMIN`, `EMPLOYEE`이며, 직원 관리·근태 상태·전자결재·채용
  요청에 역할 및 팀 범위 권한을 적용합니다.
- 직원·조직 관리에는 46명 조직 데이터, 조직도, 재직·당일 근무 상태 필터, 날짜별 근태,
  구조화된 사유(`reason_category`, `reason_summary`, `private_note`)가 구현되어 있습니다.

- 직원 매뉴얼은 검색·카테고리·텍스트 본문·이미지 요약을 제공합니다. `SUPER_ADMIN`과
  `HR_ADMIN`만 작성·수정·삭제하고, `TEAM_ADMIN`과 `EMPLOYEE`는 공개 매뉴얼을 조회합니다.

변경 이력과 실제 검증 결과는 [UPDATELOG](./UPDATELOG.md)에 유지합니다.

## Supabase PostgreSQL 연결

FastAPI와 Alembic은 Supabase PostgreSQL 연결만 사용합니다. `MIGRATION_DATABASE_URL`이
있으면 Alembic이 우선 사용하고, 없으면 `DATABASE_URL`을 사용합니다. 연결 정보는 저장소에
기록하지 말고 `backend/.env.example`을 참고해 로컬 `backend/.env`에 설정합니다.

> v0.5.10: 이미지 첨부파일은 확대 미리보기와 다운로드를, 문서 파일은 다운로드를 제공한다.

개발 서버 proxy는 기본적으로 `http://127.0.0.1:8000`의 FastAPI를 사용한다. 포트 충돌이 있을 때만 `frontend/.env.local`에 `BACKEND_URL=http://127.0.0.1:8001`처럼 로컬 대상 주소를 지정할 수 있다.

## 채용 포스터 첨부 (v0.5.7)

채용 요청을 임시 저장할 때 요청 작성자 또는 관리자는 JPG, PNG, WEBP, PDF 형식의 포스터를 최대 5MB까지 첨부할 수 있다. 결재 승인으로 생성된 채용공고는 첨부 파일 이름과 열기 링크를 함께 보여 준다.

포스터 파일은 현재 `backend/data/uploads/recruitment-posters/`에 저장하고, 요청과 파일
메타데이터는 Supabase PostgreSQL에 저장합니다. 프론트엔드는 FastAPI API로만 파일을 요청합니다.

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

- 직원·부서, 조직도, 근태·재직 상태와 사유를 조회·관리한다.
- 전자결재 문서를 작성·수정·상신·승인·반려·삭제하고, 목록·상세·처리 이력·대시보드 집계를 제공한다.
- 채용 요청을 작성·상신하고, 결재 결과에 따라 채용공고를 생성하며 포스터를 첨부·조회·다운로드한다.
- SQLAlchemy 2.0 동기 Session, Alembic migration, 멱등 조직·Auth seed를 사용한다.
- Supabase Auth와 Bearer JWT 인증, 역할 및 팀 범위 권한 검사를 적용한다.

## 사용자 역할

`SUPER_ADMIN`, `HR_ADMIN`, `TEAM_ADMIN`, `EMPLOYEE` 역할을 사용한다. 프론트엔드가 보낸
사용자 ID를 신뢰하지 않고, FastAPI가 Bearer JWT와 `employee_accounts` 연결로 현재 사용자를
식별한다. 직원 관리·역할 변경·근태 상태·전자결재 처리에는 역할 및 팀 범위 권한을 적용한다.

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

FastAPI는 `DATABASE_URL`로 Psycopg 3와 Supabase PostgreSQL에 연결한다. migration은 필요 시
별도 `MIGRATION_DATABASE_URL`을 사용한다. 연결값이 없거나 연결에 실패하면 서버 시작 시
오류를 반환하며, 로컬 SQLite 데이터베이스로 전환하지 않는다.

## 데이터베이스 구조

공통(`departments`, `employees`, `notifications`), 결재(`approval_documents`, `approval_histories`), 채용(`recruitment_requests`, `job_postings`, `applicants`), 영업(`customers`, `products`, `sales_opportunities`, `quotations`, `quotation_items`), AI(`ai_generations`)로 나눈다. 상세 설계는 [Data Model](./docs/DATA_MODEL.md)에 있다.

## 환경변수

실제 값은 기록하지 않습니다. 환경변수는 역할별 파일로 분리합니다.

- `backend/.env`: DB 연결, 서버 전용 Supabase Auth 키, seed 비밀번호
- `frontend/.env.local`: 브라우저 공개 Supabase 값과 Frontend proxy 설정
- `frontend/.env.e2e`: Playwright 테스트 전용 계정 정보

| 파일 | 이름 | 목적 |
|---|---|---|
| Backend | `DATABASE_URL`, `MIGRATION_DATABASE_URL` | Supabase PostgreSQL·Alembic 연결 |
| Backend | `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_JWKS_URL` | 서버의 Supabase Auth 검증 |
| Backend만 | `SUPABASE_SECRET_KEY` | Auth 관리 API·seed 전용 비밀키. Frontend 사용 금지 |
| Backend | `AUTH_SEED_DEFAULT_PASSWORD`, `E2E_AUTH_*_PASSWORD` | 개발·E2E seed 전용 비밀번호 |
| Frontend | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | 브라우저 Supabase Auth 클라이언트 |
| Frontend | `NEXT_PUBLIC_API_BASE_URL`, `BACKEND_URL` | API base URL·로컬 proxy 대상 |
| E2E | `E2E_*` | Playwright 테스트 전용 계정·임시 비밀번호 |
| Backend | `FRONTEND_ORIGIN`, `DISCOUNT_APPROVAL_THRESHOLD` | CORS·업무 규칙 설정 |
| Backend | `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL` | AI Provider 선택·인증 |

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

`.env.example`을 참고해 저장소에 커밋되지 않는 환경 파일을 별도로 만들고, Supabase 연결·인증
환경변수를 설정한 뒤 실행합니다.

## Database Migration 방법

Supabase 연결 정보를 환경변수에 설정한 뒤 Backend에서 실행한다.

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current
```

개발 DB를 되돌리는 검증은 `alembic downgrade base`로 가능하지만 데이터가 삭제되므로 별도 테스트 DB에서만 실행한다. 최초 migration은 `20260730_0001_approval_flow.py`다.

## Seed 실행 방법

Supabase에 migration을 적용한 뒤 조직 seed와 Auth seed를 실행합니다. 같은 seed를 다시 실행해도
부서·직원·Auth 계정 연결이 중복 생성되지 않도록 구성되어 있습니다.

직원 매뉴얼 migration 적용 후에는 아래 명령으로 초기 7개 카테고리와 15개 공개 매뉴얼을 등록합니다.
같은 명령을 다시 실행해도 slug와 카테고리 ID를 기준으로 갱신되어 중복 생성되지 않습니다.

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.seed_manuals
```

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

## Playwright E2E 실행 방법

E2E는 기존 직원과 분리된 일반 직원·SUPER_ADMIN 테스트 계정만 사용합니다.
`npm run test:e2e`는 시작 전 두 테스트 계정을 자동 생성하고, 테스트 성공·실패 후 종료 단계에서
자동 삭제합니다. 따라서 평상시 직원·조직 관리 화면에는 테스트 계정이 남지 않습니다.

처음 한 번만 `backend/.env`에 `E2E_AUTH_EMPLOYEE_PASSWORD`와
`E2E_AUTH_SUPER_ADMIN_PASSWORD`를 설정합니다. 수동으로 계정만 준비해야 할 때는 아래 명령을 사용합니다.

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.seed_e2e_auth_accounts
```

중단된 수동 테스트 계정을 직원 목록에서 제거하려면 아래 정리 명령을 실행합니다. 이 명령은
Playwright 전용 직원 2명과 비활성 인증 테스트 계정 1명만 삭제합니다.

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.cleanup_test_auth_accounts
```

그다음 `frontend/.env.e2e.example`을 `frontend/.env.e2e`로 복사하고, 두 계정의
비밀번호와 비밀번호 변경용 임시 비밀번호를 입력합니다. `.env.e2e`는 Git에 포함되지 않습니다.

`frontend/`에서 E2E를 실행하면 Playwright가 백엔드와 프론트엔드를 준비합니다. 이미 실행 중인
서버가 있으면 그것을 재사용합니다.

```powershell
npm run test:e2e
```

실패한 테스트의 trace와 screenshot은 `frontend/test-results/`에 남습니다. 테스트 전용
계정 외의 실제 직원 계정, 비밀번호, access token은 E2E 환경변수에 사용하지 않습니다.

## 주요 API 그룹

현재 동작 API는 Health, Auth, Departments, Employees, Dashboard, Approvals, Recruitment다.
전자결재는 목록·상세·작성·수정·삭제와 상신·승인·반려를 제공하고, 채용은 요청·공고·포스터
첨부와 조회를 제공한다. 상세 계약은 [API Spec](./docs/API_SPEC.md)에 정리한다.

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

`backend/.env`의 Supabase Auth 설정과 `frontend/.env.local`의 공개 설정을
확인한 뒤 백엔드와 프론트엔드를 재시작하세요. 키 값 자체는 로그나 코드에
출력하지 않습니다.

### `Invalid login credentials`가 표시되는 경우

#### 문제 원인

이메일 또는 비밀번호가 Supabase Auth에 등록된 값과 다르거나, 비밀번호 변경 후
이전 비밀번호를 입력한 경우입니다.

#### 해결 방법

로그인 이메일을 다시 확인하고 현재 비밀번호를 입력합니다. 비밀번호를 잊은 경우
로그인 화면의 **비밀번호 변경** 화면에서 변경 절차를 진행합니다. 비밀번호를
화면 캡처나 로그에 기록하지 않습니다.

### 로그인은 됐지만 백엔드에 `401 Unauthorized`가 표시되는 경우

#### 문제 원인

브라우저에는 이전 로그인 세션의 토큰이 남아 있는데 백엔드가 재시작되지
않았거나, Supabase 프로젝트의 JWT 서명 방식과 JWKS 공개 키 검증 설정이
일시적으로 맞지 않을 때 보호된 API 요청이 401로 거부될 수 있습니다.

#### 해결 방법

1. 실행 중인 백엔드 터미널에서 `Ctrl + C`를 누른 뒤, 프로젝트 루트에서
   `.\run-backend.cmd`를 다시 실행합니다.
2. 브라우저에서 로그아웃한 후 새로고침하고 다시 로그인합니다. 새 세션 토큰으로
   다시 요청하기 위해서입니다.
3. 계속되면 `backend/.env`의 `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`,
   `SUPABASE_JWKS_URL`이 같은 Supabase 프로젝트를 가리키는지 확인합니다.

백엔드는 JWKS 공개 키 검증을 먼저 사용하고, 프로젝트 서명 설정과의 호환 문제가
있을 때만 Supabase 사용자 조회로 토큰을 다시 검증합니다. `Authorization: Bearer`
뒤의 토큰, 비밀번호, Supabase 키는 화면 캡처나 로그에 공유하지 마세요.

### API 요청이 `401 Unauthorized` 또는 `403 Forbidden`으로 실패하는 경우

#### 문제 원인

`401`은 Authorization 헤더가 없거나 만료·검증 실패한 토큰으로 보호 API를 호출한 경우입니다.
`403`은 로그인은 되었지만 역할 또는 팀 범위 권한이 없는 경우입니다. 일반 직원은 직원 관리 변경을
할 수 없고, `TEAM_ADMIN`은 다른 팀 직원의 상태를 변경할 수 없으며, 문서 작성자는 자기 문서를
승인·반려할 수 없습니다.

#### 해결 방법

1. DevTools Network에서 해당 요청의 Request Headers에 `Authorization: Bearer ...`가 있는지 확인합니다.
2. 토큰이 없다면 로그아웃 후 다시 로그인합니다.
3. 토큰이 있는데도 `403`이면 현재 계정의 역할, 대상 직원의 팀, 결재 문서의 작성자·결재자 정보를 확인합니다.
4. API 호출에 `actor_id`, `author_id`, `employee_id`, `requester_id`를 인증 목적의 query/body 값으로 추가하지 않습니다.

토큰 전문은 확인하거나 공유하지 말고, 상태 코드와 요청 경로만 확인합니다.

### 전자결재·채용 요청 작성 후 Network 요청을 찾기 어려운 경우

#### 문제 원인

Network 목록은 화면에서 실제로 발생한 요청 이름만 표시합니다. 전자결재는 `approvals`와
`submit`, 채용 요청은 `recruitment-requests`로 표시됩니다.

#### 해결 방법

1. Network에서 `Fetch/XHR`를 선택하고 목록을 지웁니다.
2. 전자결재는 저장 또는 상신, 채용은 작성 또는 상신을 한 번 다시 실행합니다.
3. `method:POST`로 필터링한 뒤 해당 행을 선택합니다.
4. **Payload**에서 입력값을, **Headers**에서 Authorization 헤더의 존재만 확인합니다.

### `pytest` 실행 시 Supabase 연결 오류가 발생하는 경우

#### 문제 원인

테스트는 운영 Supabase 연결 대신 테스트용 세션과 health check override를 사용합니다. 이 설정이
적용되지 않은 앱을 사용하면 테스트 시작 단계에서 Supabase 연결을 시도해 실패할 수 있습니다.

#### 해결 방법

`backend/`에서 프로젝트 테스트 명령을 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m pytest
```

테스트 코드를 추가할 때는 기존 `tests/conftest.py`의 테스트 앱과 dependency override를 사용합니다.

### Supabase 연결 및 Alembic 오류

#### 문제 원인

잘못된 Supabase 호스트·포트·데이터베이스명, URL 특수문자 미인코딩, Psycopg 드라이버 불일치,
pooler의 `pgbouncer` 옵션 또는 prepared statement 충돌로 연결이 실패할 수 있습니다.

#### 해결 방법

Supabase Connect의 PostgreSQL URI를 다시 복사하고 `DATABASE_URL`을 설정합니다.
Psycopg 3 의존성을 설치하고, `pgbouncer=true`를 제거하며, Alembic은 반드시
`\.venv\Scripts\alembic.exe upgrade head`로 실행합니다.

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

### 백엔드·프론트엔드 실행 위치가 헷갈리는 경우

프로젝트 루트에서 아래 launcher를 사용하세요. 직접 실행할 때만 각각 `backend/`, `frontend/`로 이동합니다.

```powershell
.\run-backend.cmd
.\run-frontend.cmd
```

### Next.js가 상위 폴더를 workspace root로 잘못 선택하는 경우

상위 사용자 폴더에 다른 `package-lock.json`이 있으면 Turbopack이 잘못된 루트를 탐색해 접근 거부가 발생할 수 있다. `frontend/next.config.ts`의 `turbopack.root`를 Frontend 실행 폴더로 제한해 해결했다. Frontend 명령은 반드시 `frontend/`에서 실행한다.

## 프로토타입 완료 조건

- 두 핵심 시나리오를 처음부터 끝까지 시연
- Supabase PostgreSQL 저장, FastAPI 단일 업무 API 경계
- 멱등 Seed와 Mock AI의 키 없는 동작
- 금지된 상태 전환 및 권한 위반 차단
- 핵심 Backend 테스트 통과
- 문서와 실제 구현 상태 일치

## 제외 기능과 한계

실제 이메일, PDF·OCR, RAG·벡터 DB, n8n, 다단계 결재, WebSocket, 실제 개인정보·기밀,
Docker, 모바일, 완전한 ERP/ATS/CRM, 자동 채용 판단, 실제 견적 발송은 제외한다.

## 이후 확장 계획

프로토타입 안정화 후 다단계 결재, 실제 이메일, 감사·관측성, CI/CD와 배포,
필요성이 검증된 문서 검색 기능을 순차 검토한다. 완성형 서비스와 실제 배포는
별도 마일스톤으로 관리한다.
