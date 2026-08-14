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
- 자리 비움 자동 로그아웃: 화면을 닫아둔 시간이 30분을 넘으면 다시 접속할 때 세션을 끊습니다. 창을 열어두면 조작이 없어도 유지됩니다.
- Supabase access token을 공통 API Client가 `Authorization: Bearer` 헤더로 전달
- FastAPI의 Supabase JWT 검증과 `employee_accounts` 기반 직원·역할 연결
- 비활성 계정 또는 직원 연결이 없는 인증 계정의 업무 API 접근 차단

### 직원·조직과 근태

- 46명 조직 Seed와 부서·팀·직급 기반 직원 목록
- 이름·사번·이메일 검색, 부서·재직 상태·근무 상태 필터
- Playwright E2E 전용 계정은 일반 로그인에서 직원 목록과 선택지에 표시하지 않고 E2E 계정으로 로그인한 경우에만 표시
- 날짜별 근무 상태 등록과 병가·결근·휴직 사유 등록
- 공개 사유와 관리자·인사 담당자 전용 비공개 상세 사유 분리
- 데스크톱 조직도와 모바일 전용 직원 목록·하단 메뉴 반응형 UI

### 전자결재와 채용 요청

- 일반 품의 문서 작성, 수정, 상신, 승인, 반려, 삭제, 처리 이력
- 작성자·결재자·관리자 권한에 따른 결재 처리 제한
- 채용 요청에 고용 형태·경력·학력·근무지·급여·마감일·지원 방법을 입력하고 상신, 결재 승인 후 같은 사실을 담은 채용공고 생성
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
- `전체 채용공고 현황`은 모든 공고의 지원자를 합산해 `서류전형 → 1차면접 → 2차면접 → 최종입사`로 표시합니다. 지원 접수·서류 검토는 서류전형, 제안은 2차면접에 합산하며 불합격은 진행 단계 수치에서 제외합니다.
- 최근 업무에는 전자결재와 채용 요청만 표시

### 직원 매뉴얼과 FAQ

- 각 매뉴얼이 설명하는 실제 앱 화면을 캡처해 카드 대표 이미지로 사용하는 이미지 중심 목록
- 제목·내용 검색과 카테고리 필터, 카드 이미지 확대 보기(ESC·바깥 클릭으로 닫기)
- 직원 이용 가이드 PDF 다운로드
- `SUPER_ADMIN`, `HR_ADMIN`의 매뉴얼·카테고리 작성·수정·삭제 (카드의 편집 아이콘은 관리자에게만 노출)
- `TEAM_ADMIN`, `EMPLOYEE`의 공개 매뉴얼 조회
- 6개 카테고리와 9개 핵심 매뉴얼 Seed (PDF 가이드 구조에 맞춰 정리)
- 매뉴얼 상세 페이지(`/manuals/{slug}`)에서 본문 전문과 이미지 확인
- 별도 FAQ 화면(`/faq`)에서 자주 묻는 질문 21개를 Accordion으로 확인하며, 인증된 모든 역할이 조회 가능

### AX 직원 도우미

우측 하단 플로팅 버튼에서 열리는 사내 도우미입니다. **등록된 매뉴얼·FAQ에서 질문에 맞는 문서를 찾아 원문을 보여주며, LLM을 호출하지 않습니다.** 문서에 없는 내용은 추측하지 않고 "찾지 못했다"고 답합니다.

- 응답 5종: 확정 답변 / 후보 제시(접전 시) / 근거 없음 / 정책 고정 응답 / v1 범위 밖 안내
- 매칭: 글자 1+2gram + IDF 가중 포함률 + 카테고리 부스트 (`app/domain/ax_search.py`)
- 역할별 매뉴얼 공개 범위(`target_roles`)를 검색 후보 단계에서 필터링
- 답변 카드에서 근거 매뉴얼을 새 탭으로 열거나 관련 업무 화면으로 이동
- 패널·버튼을 끌어 옮길 수 있고 위치는 브라우저에 저장 (대화 내용은 저장하지 않음)
- 질문 로그는 익명으로 남기며, 상위 후보 3개를 함께 기록해 매칭 실패 원인을 분석
- 기획·측정 근거: [`docs/PLAN.md`](docs/PLAN.md#9-ax-직원-도우미--2026-08-09--08-10)

### 생성형 AI 초안·채용 포스터

전자결재에서는 Claude가 사용자가 검토할 문안 초안을 만들고, 채용공고에서는 OpenAI가 승인된 채용정보를 담은 세로형 포스터 이미지를 만듭니다. AI는 문서를 저장하거나 업무 상태를 바꾸지 않습니다.

- 전자결재: 작성자·직급·부서·팀 등 DB 사실과 사용자 입력을 합쳐 제목·본문 생성. `[적용]`은 폼만 채우며 저장은 사용자가 직접 실행
- 채용공고: 승인된 채용 요청의 직무·인원·업무·역량·근무지·급여·마감일·지원 방법을 읽어 PNG 포스터 미리보기 생성. 한 화면에서 여러 시안을 데스크톱은 좌우로, 모바일은 한 장씩 비교·선택하고, 이미지를 눌러 확대 검토한 뒤 선택본을 다운로드하며 팀 소개 입력은 사용하지 않음
- 값이 없으면 Context에 키를 만들지 않습니다. 주지 않은 사실은 존재조차 알리지 않는 것이 가장 확실한 환각 차단입니다.
- `AI_PROVIDER=mock`이 기본값이라 **API 키 없이도 전체 흐름을 개발·시연**할 수 있습니다. Mock 결과에는 "샘플 응답" 배지가 붙습니다.
- 비용 방어: 최근 24시간 기준 전역·사용자당 호출 한도, 호출당 토큰 상한, 짧은 입력 사전 차단. `SUPER_ADMIN`은 검수용 반복 생성을 위해 횟수 제한에서 제외되지만 호출 비용은 계속 발생합니다.
- `ai_generations` 테이블에 AI 최초본과 사람이 수정한 최종본을 나눠 기록하고 토큰 수를 남겨 실지출을 쿼리로 계산합니다.
- 생성 이미지는 화면에서 확인하고 PNG로 내려받을 수 있습니다. 확인 전용 응답이므로 기존 첨부 포스터나 공고를 자동으로 덮어쓰지 않습니다.
- 생성 시안은 현재 화면 메모리에만 유지되므로 메뉴를 벗어나면 사라집니다. 보관할 시안은 화면을 나가기 전에 선택해 다운로드합니다.
- 이미지 생성은 `IMAGE_AI_PROVIDER=openai`일 때만 활성화되고, 일반 계정에는 최근 24시간 기준 사용자당 2회·전역 5회의 별도 기본 한도를 적용합니다. `SUPER_ADMIN` 호출은 두 한도와 일반 계정의 전역 집계에서 제외합니다.
- 설계 근거: [`docs/PLAN.md`](docs/PLAN.md#10-생성형-ai-초안-생성--2026-08-12)

## 기술 구성

| 영역 | 사용 기술 |
|---|---|
| Frontend | Next.js 16 App Router, React 19, TypeScript |
| 스타일 | `src/app/globals.css`의 시맨틱 클래스와 CSS 변수. Tailwind v4가 설치·import돼 있으나 유틸리티 클래스는 사실상 사용하지 않습니다 |
| Backend | FastAPI, SQLAlchemy 2.0(동기 Session), Pydantic |
| Database | Supabase PostgreSQL, Alembic, Psycopg 3 |
| Authentication | Supabase Auth, JWT/JWKS |
| AI | Anthropic(초안), OpenAI(포스터 이미지) |
| Testing | Pytest, Ruff, Playwright(수동 실행) |

## 역할과 권한

| 역할 | 주요 권한 |
|---|---|
| `SUPER_ADMIN` | 전체 직원·조직 관리, 역할 변경, 모든 결재 처리, 매뉴얼 관리 |
| `HR_ADMIN` | 직원·조직·근태 관리, 비공개 사유 조회, 매뉴얼 관리 |
| `TEAM_ADMIN` | 팀장. 소속 **부서 전체**의 직원 상태 관리와 결재 처리 |
| `PART_ADMIN` | 파트장. **자기 파트만** 관리. 결재자로 지정 가능 |
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
| `backend/.env` | `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL` | 생성형 AI 초안. 기본값 `mock`은 키가 필요 없고, `claude`인데 키가 없으면 오류로 처리합니다 |
| `backend/.env` | `AI_MAX_TOKENS`, `AI_TIMEOUT_SECONDS`, `AI_DAILY_LIMIT_PER_USER`, `AI_DAILY_LIMIT_GLOBAL` | AI 비용 상한. 한도는 최근 24시간 기준이며 전역 한도가 실질적 방어선입니다 |
| `backend/.env` | `IMAGE_AI_PROVIDER`, `OPENAI_API_KEY`, `IMAGE_AI_MODEL`, `IMAGE_AI_SIZE`, `IMAGE_AI_QUALITY`, `IMAGE_AI_TIMEOUT_SECONDS` | 채용 포스터 이미지 생성. 기본값 `disabled`는 호출하지 않고 `openai`에서만 유료 API를 사용합니다 |
| `backend/.env` | `IMAGE_AI_DAILY_LIMIT_PER_USER`, `IMAGE_AI_DAILY_LIMIT_GLOBAL` | 채용 포스터 이미지 생성의 최근 24시간 비용 한도. 기본값 2회·5회 |
| `frontend/.env.local` | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | 브라우저 Supabase Auth 클라이언트 |
| `frontend/.env.local` | `BACKEND_URL` | Next.js 개발 프록시 대상, 기본값은 `http://127.0.0.1:8000` |
| `frontend/.env.local` | `NEXT_PUBLIC_SESSION_TIMEOUT_MINUTES` | 선택. 자리 비움 자동 로그아웃 기준, 기본값 30분 |

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

# 기존 계정에 영향 없이 QA파트 3명만 계정·권한 연결
.\.venv\Scripts\python.exe -m app.scripts.provision_qa_part_accounts

# 직원 매뉴얼과 FAQ
.\.venv\Scripts\python.exe -m app.scripts.seed_manuals
.\.venv\Scripts\python.exe -m app.scripts.seed_faqs
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

Playwright E2E는 로그인·세션 유지·로그아웃·권한 범위·직원 필터·전자결재 승인·비밀번호 변경을 검증합니다. 2026-08-13 기준 전체 정적 검사와 빌드를 통과했으며, Backend 회귀 테스트는 201개입니다.

### AX 도우미 손으로 시험하기

자동화 테스트가 정해둔 질문만 확인한다면, 아래 도구는 생각나는 대로 질문을 던져볼 수 있습니다. API와 같은 서비스 로직을 타며 실제 DB의 매뉴얼·FAQ를 사용합니다. 시험 질문은 로그에 남지 않습니다.

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.try_ax_chat                 # 대화형
.\.venv\Scripts\python.exe -m app.scripts.try_ax_chat "반차 어떻게 써요?"
.\.venv\Scripts\python.exe -m app.scripts.try_ax_chat --role SUPER_ADMIN
```

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
│  │  ├─ domain/         # 순수 규칙·상수·AI Provider (DB·HTTP 비의존)
│  │  ├─ security/       # 토큰 검증·ActorContext·역할 상수
│  │  ├─ core/  db/      # 설정, 엔진·세션
│  │  └─ scripts/        # Seed와 운영 보조 스크립트
│  ├─ migrations/
│  └─ tests/
├─ frontend/
│  ├─ src/app/           # Next.js App Router
│  ├─ src/features/      # 기능별 UI·API 호출
│  ├─ src/components/    # 공통 UI
│  ├─ src/lib/           # 공통 API·Supabase 클라이언트
│  ├─ src/types/         # 백엔드 스키마 대응 타입
│  └─ e2e/               # Playwright 시나리오
├─ docs/
├─ AGENTS.md             # AI 에이전트 규칙과 Context Map
├─ CLAUDE.md             # AGENTS.md를 가리키는 포인터
├─ README.md
├─ TROUBLESHOOTING.md
└─ UPDATELOG.md
```

구조와 데이터 흐름의 상세는 [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)에 있습니다.

## 관련 문서

문서 전체 안내는 [docs/README.md](./docs/README.md)에 있습니다.
AI 에이전트로 작업한다면 [AGENTS.md](./AGENTS.md)의 Context Map부터 보세요.

- [기능 기획 기록](./docs/PLAN.md) — 무엇을 왜 만들었는지 (시간순)
- [현재 구현 상태](./docs/CURRENT_STATE.md) — 무엇이 되고 무엇이 안 되는지
- [시스템 구조](./docs/ARCHITECTURE.md) — 요청 흐름, 계층, 배포
- [업무 도메인과 규칙](./docs/DOMAIN.md) — 권한, 상태 전이
- [데이터 모델](./docs/DATA_MODEL.md)
- [API](./docs/API_SPEC.md)
- [코드 작성 규칙](./docs/CODING_RULES.md)
- [기능 로드맵](./docs/ROADMAP.md)
- [설계 결정 기록](./docs/DECISIONS.md)
- [배포 기획 (Render)](./docs/DEPLOYMENT_PLAN.md)
- [AI 설계와 구현 기준](./docs/AI_DESIGN.md)
- [업데이트 로그](./UPDATELOG.md)

초기 기획 원문과 인계 문서는 [docs/archive](./docs/archive/README.md)에 보존되어 있습니다. 무엇이 어디로 요약됐는지는 그 폴더의 안내 문서에 정리돼 있습니다.

## 문제 해결

로그인, JWT `401`, 권한 `403`, migration 누락, E2E 테스트 계정, AI 포스터 timeout·임시 미리보기, 대시보드 집계 등 실제 작업 중 확인한 오류와 해결 방법은 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)를 참고하세요.
