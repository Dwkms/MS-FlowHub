# MS FlowHub

MS FlowHub는 직원·조직 관리, 근태 상태, 전자결재, 채용 요청과 직원 매뉴얼을 제공하는 사내 업무 포털입니다.
실제 로그인은 Supabase Auth를 사용하고, 업무 데이터는 Supabase PostgreSQL에서 관리합니다.

> 변경 이력은 [UPDATELOG.md](./UPDATELOG.md), 오류 대응 방법은 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)에서 확인할 수 있습니다.

## 배포된 환경

- Frontend: https://ms-flowhub-frontend.onrender.com
- Backend API: https://ms-flowhub.onrender.com (`/health`로 상태 확인)
- 둘 다 Render Free 플랜이라 유휴 시 슬립 상태가 되며, 첫 접속에 콜드스타트로 수십 초가 걸릴 수 있습니다.
- 배포 구성과 절차는 [DEPLOYMENT_PLAN.md](./docs/DEPLOYMENT_PLAN.md)를 참고하세요.

## 목차

- [배포된 환경](#배포된-환경)
- [현재 구현 상태](#현재-구현-상태)
- [기술 구성](#기술-구성)
- [역할과 권한](#역할과-권한)
- [실행 방법](#실행-방법)
- [환경변수](#환경변수)
- [데이터베이스와 Seed](#데이터베이스와-seed)
- [테스트와 검증](#테스트와-검증)
- [프로젝트 구조](#프로젝트-구조)
- [관련 문서](#관련-문서)
- [문제 해결](#문제-해결)

## 현재 구현 상태

### 인증과 권한

- Supabase Auth 로그인, 로그아웃, 세션 유지, 비밀번호 변경
- Supabase access token을 공통 API Client가 `Authorization: Bearer` 헤더로 전달
- FastAPI의 Supabase JWT 검증과 `employee_accounts` 기반 직원·역할 연결
- 비활성 계정 또는 직원 연결이 없는 인증 계정의 업무 API 접근 차단

### 직원·조직과 근태

- 46명 조직 Seed와 부서·팀·직급 기반 직원 목록
- 이름·사번·이메일 검색, 부서·재직 상태·근무 상태 필터
- 날짜별 근무 상태 등록과 병가·결근·휴직 사유 등록
- 공개 사유와 관리자·인사 담당자 전용 비공개 상세 사유 분리
- 데스크톱 조직도와 모바일 전용 직원 목록·하단 메뉴 반응형 UI

### 전자결재와 채용 요청

- 일반 품의 문서 작성, 수정, 상신, 승인, 반려, 삭제, 처리 이력
- 작성자·결재자·관리자 권한에 따른 결재 처리 제한
- 채용 요청 작성·상신, 결재 승인 후 채용공고 생성
- JPG, PNG, WEBP, PDF 형식의 채용 포스터 첨부·미리보기·다운로드

### 채용 지원자 관리 (ATS Lite)

- 채용공고별 지원자 등록·수정·삭제, 이름·이메일 검색, 공고/단계 필터
- 지원 접수 → 서류 검토 → 1차 면접 → 2차 면접 → 채용 확정/불합격 전형 단계 변경과 이력 조회
- `SUPER_ADMIN`, `HR_ADMIN`의 등록·수정·삭제·단계 변경, `TEAM_ADMIN`의 본인 부서 공고 조회, `EMPLOYEE` 접근 차단
- 같은 공고 내 이메일 중복 등록, 불합격 사유 미입력, 종료 단계 재변경을 서버에서 차단
- 이력서 파일 첨부, 외부 공개 지원 화면, 이메일·면접 일정 발송, AI 자동 평가는 이후 확장 범위

### 대시보드

- 로그인한 직원 기준의 결재 대기·상신 결재·생성된 채용공고 수를 실제 DB 데이터로 표시
- 값이 있는 지표 카드는 전자결재 또는 채용공고 화면으로 이동
- 최근 업무에는 전자결재와 채용 요청만 표시
- 상단 알림 아이콘은 알림 조회·읽음 처리 기능 구현 전까지 비활성 상태

### 직원 매뉴얼 MVP

- 카테고리, 목록 검색, 중요 문서 상단 고정, 최근 수정일 표시
- 텍스트 본문과 이미지·PDF URL 자산을 함께 제공하는 상세 화면
- `SUPER_ADMIN`, `HR_ADMIN`의 매뉴얼·카테고리 관리
- `TEAM_ADMIN`, `EMPLOYEE`의 공개 매뉴얼 조회
- 7개 카테고리와 15개 초기 매뉴얼 Seed

## 기술 구성

| 영역 | 사용 기술 |
|---|---|
| Frontend | Next.js App Router, TypeScript, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy 2.0, Pydantic |
| Database | Supabase PostgreSQL, Alembic, Psycopg 3 |
| Authentication | Supabase Auth, JWT/JWKS |
| Testing | Pytest, Ruff, Playwright |

## 역할과 권한

| 역할 | 주요 권한 |
|---|---|
| `SUPER_ADMIN` | 전체 직원·조직 관리, 역할 변경, 모든 결재 처리, 매뉴얼 관리 |
| `HR_ADMIN` | 직원·조직·근태 관리, 비공개 사유 조회, 매뉴얼 관리 |
| `TEAM_ADMIN` | 같은 팀의 허용된 직원 상태 관리와 지정 결재 처리 |
| `EMPLOYEE` | 본인 범위 조회·근태 상태 등록·결재 문서 작성·공개 매뉴얼 조회 |

권한은 프론트엔드 표시뿐 아니라 FastAPI 서비스와 의존성에서 다시 검증합니다.

## 실행 방법

### 처음 한 번 준비

```powershell
# Backend
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env

# Frontend
cd ..\frontend
npm install
Copy-Item .env.example .env.local
```

`backend/.env`와 `frontend/.env.local`에 필요한 Supabase 값을 입력한 뒤 실행합니다.

### 개발 서버 실행

프로젝트 루트에서 각각 실행합니다.

```powershell
.\run-backend.cmd
.\run-frontend.cmd
```

- Frontend: `http://localhost:3000`
- Backend API: `http://127.0.0.1:8000`

## 환경변수

값 자체는 저장소에 기록하지 않습니다. 예시는 [backend/.env.example](./backend/.env.example), [frontend/.env.example](./frontend/.env.example)을 기준으로 설정합니다.

| 위치 | 필수 변수 | 용도 |
|---|---|---|
| `backend/.env` | `DATABASE_URL` | Supabase PostgreSQL 애플리케이션 연결 |
| `backend/.env` | `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `SUPABASE_JWKS_URL` | 서버의 Auth 검증·계정 Seed·Storage(채용 포스터) 연동 |
| `backend/.env` | `AUTH_SEED_DEFAULT_PASSWORD`, `E2E_AUTH_*_PASSWORD` | 개발·E2E 전용 Seed 비밀번호 |
| `frontend/.env.local` | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | 브라우저 Supabase Auth 클라이언트 |
| `frontend/.env.local` | `BACKEND_URL` | Next.js 개발 프록시 대상, 기본값은 `http://127.0.0.1:8000` |

`SUPABASE_SECRET_KEY`, 데이터베이스 URL, 실제 비밀번호, access token은 Frontend 환경변수·소스 코드·로그에 넣지 않습니다.

## 데이터베이스와 Seed

### Migration 적용

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
```

### 초기 데이터 준비

```powershell
# 직원·조직과 Auth 계정
.\.venv\Scripts\python.exe -m app.scripts.seed_organization
.\.venv\Scripts\python.exe -m app.scripts.seed_auth_accounts

# 직원 매뉴얼
.\.venv\Scripts\python.exe -m app.scripts.seed_manuals
```

Seed는 반복 실행해도 중복 생성되지 않도록 작성되어 있습니다. E2E는 테스트 시작 전에 전용 계정을 만들고 종료 후 자동으로 삭제합니다.

### Supabase Storage 버킷 준비

채용 포스터는 로컬 디스크가 아닌 Supabase Storage의 비공개 버킷에 저장됩니다. 처음 한 번만 실행하면 됩니다.

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.setup_storage_bucket
```

이미 버킷이 있으면 아무 작업도 하지 않으므로 반복 실행해도 안전합니다.

## 테스트와 검증

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest
```

### Frontend

```powershell
cd frontend
npm run lint
npm run typecheck
npm run build
npm run test:e2e
```

Playwright E2E는 로그인·세션 유지·로그아웃·권한 범위·직원 필터·전자결재 승인·비밀번호 변경을 검증합니다.

## 프로젝트 구조

```text
MS FlowHub/
├─ backend/
│  ├─ app/
│  │  ├─ api/            # FastAPI Router와 의존성
│  │  ├─ services/       # 업무 규칙과 트랜잭션
│  │  ├─ repositories/   # SQLAlchemy 데이터 접근
│  │  ├─ models/         # ORM 모델
│  │  ├─ schemas/        # Pydantic API 스키마
│  │  └─ scripts/        # Seed와 운영 보조 스크립트
│  ├─ migrations/
│  └─ tests/
├─ frontend/
│  ├─ src/app/           # Next.js App Router
│  ├─ src/features/      # 기능별 UI·API 호출
│  ├─ src/components/    # 공통 UI
│  ├─ src/lib/           # 공통 API·Supabase 클라이언트
│  └─ e2e/               # Playwright 시나리오
├─ docs/
├─ README.md
├─ TROUBLESHOOTING.md
└─ UPDATELOG.md
```

## 관련 문서

- [API 명세](./docs/API_SPEC.md)
- [데이터 모델](./docs/DATA_MODEL.md)
- [기능 로드맵](./docs/ROADMAP.md)
- [프로젝트 명세](./docs/PROJECT_SPEC.md)
- [설계 결정 기록](./docs/DECISIONS.md)
- [배포 기획 (Render)](./docs/DEPLOYMENT_PLAN.md)
- [AI 확장 설계 (미구현)](./docs/AI_DESIGN.md)
- [업데이트 로그](./UPDATELOG.md)

과거 기획·스냅샷 문서(구현 요약, 사용자 흐름 초안, 프로토타입 체크리스트, ATS MVP 착수 전 기획)는 [docs/archive](./docs/archive)에 보존되어 있습니다.

## 문제 해결

로그인, JWT `401`, 권한 `403`, E2E 테스트 계정, Pytest 경고 등 실제 작업 중 확인한 오류와 해결 방법은 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)를 참고하세요.
