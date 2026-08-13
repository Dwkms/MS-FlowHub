# Architecture

실제 코드 기준 구조입니다. 문서와 코드가 다르면 코드가 기준입니다.
업무 규칙은 [`DOMAIN.md`](DOMAIN.md), 데이터 구조는 [`DATA_MODEL.md`](DATA_MODEL.md)를 보세요.

## 요청 흐름

```
브라우저
  │  Supabase Auth로 로그인 → access token
  ▼
Next.js (frontend, Root Directory = frontend)
  │  next.config.ts rewrite:  /api/:path*  →  ${BACKEND_URL}/api/:path*
  ▼
FastAPI (backend, Root Directory = backend)
  │  api/        Router · 의존성 주입만
  │  services/   업무 규칙 · 트랜잭션 경계
  │  repositories/ SQLAlchemy 데이터 접근
  ▼
Supabase PostgreSQL  (Alembic으로 스키마 관리)
```

프론트엔드는 업무 테이블에 직접 접근하지 않습니다. Supabase를 직접 부르는 곳은 **로그인 뿐**이며
(`lib/supabase-browser.ts`), 나머지 데이터는 전부 위 프록시를 지나 FastAPI로 갑니다.

## 인증과 권한

1. 브라우저가 Supabase Auth로 로그인하고 access token을 받는다
2. 프론트엔드가 `Authorization: Bearer <token>`으로 API를 호출한다
3. `security/supabase_auth.py`가 JWKS로 토큰을 검증해 `auth_user_id`를 얻는다
4. `api/dependencies.py:get_authenticated_actor`가 `employee_accounts`를 조회해
   `ActorContext(employee_id, role, auth_user_id)`를 만든다
5. 권한 판정은 Service 계층에서 다시 한다. 화면 표시만으로 막지 않는다

역할 값과 관리 범위는 [`DOMAIN.md`](DOMAIN.md#역할과-권한)에 있습니다.

## Backend 계층

| 디렉터리 | 책임 | 파일 수 |
|---|---|---|
| `app/api/` | Router, 의존성 주입, 응답 반환. 업무 규칙 없음 | 11 |
| `app/services/` | 업무 규칙, 상태 전이, 트랜잭션 | 10 |
| `app/repositories/` | SQLAlchemy 조회·저장 | 9 |
| `app/models/` | SQLAlchemy ORM 모델 | 9 |
| `app/schemas/` | Pydantic 요청·응답 스키마 | 9 |
| `app/domain/` | **순수 규칙·상수·AI Provider.** DB·HTTP에 의존하지 않음 | 13 |
| `app/security/` | 토큰 검증, `ActorContext`, 역할 상수 | 4 |
| `app/core/`, `app/db/` | 설정(`pydantic-settings`), 엔진·세션 | 3 / 3 |
| `app/scripts/` | Seed와 운영 보조 스크립트 | 13 |

`app/domain/`은 README의 구조도에 빠져 있던 계층입니다. 여기에 판단 규칙을 모아 두고
Service가 가져다 씁니다 — 예: `employee_status.py`(근태 상태·비공개 사유 열람 역할),
`recruitment_options.py`(채용 선택지 단일 출처), `recruitment_policy.py`(결재자 직급),
`ai_context.py`·`ai_prompts.py`(AI 입력 조립·환각 방지), `ai_provider.py`·`claude_provider.py`·
`openai_image_provider.py`(AI Provider 계약).

ORM 모델과 Pydantic 스키마는 분리합니다. 하나의 업무가 여러 데이터를 바꾸면 Service에서
한 트랜잭션으로 처리합니다.

## Frontend 계층

| 디렉터리 | 책임 |
|---|---|
| `src/app/` | Next.js App Router 페이지. 라우팅과 조립만 |
| `src/features/` | 기능별 UI와 해당 기능의 API 호출 (`features/*/api.ts`) |
| `src/components/` | 공통 UI (`portal-shell.tsx`, `icons.tsx`) |
| `src/lib/` | `api-client.ts`(공통 호출), `supabase-browser.ts`(로그인), `approver-policy.ts` |
| `src/types/` | 백엔드 스키마에 대응하는 타입 |
| `src/storage/` | **비어 있음.** 아래 "확인 필요" 참고 |

**스타일**: `src/app/globals.css` 867줄의 시맨틱 클래스(`.status-detail-panel` 등)와
`:root` CSS 변수가 실질적인 스타일 시스템입니다. Tailwind v4가 설치돼 있고 `globals.css`
첫 줄에서 `@import "tailwindcss"`를 하지만 **유틸리티 클래스는 사실상 쓰지 않습니다.**
새 UI도 기존 시맨틱 클래스 방식을 따르세요.

## 외부 서비스

| 서비스 | 용도 | 키 위치 |
|---|---|---|
| Supabase PostgreSQL | 업무 데이터 | `DATABASE_URL` (backend) |
| Supabase Auth | 로그인·JWT | 서버 `SUPABASE_*`, 브라우저 `NEXT_PUBLIC_SUPABASE_*` |
| Supabase Storage | 채용 포스터 등 첨부 | 서버 전용 |
| Anthropic | 전자결재·채용공고 초안 | `AI_API_KEY` (backend 전용) |
| OpenAI | 채용 포스터 이미지 | `OPENAI_API_KEY` (backend 전용) |

`SUPABASE_SECRET_KEY`, `DATABASE_URL`, AI 키는 **`NEXT_PUBLIC_*`에 절대 넣지 않습니다.**
전체 환경변수 목록은 `backend/.env.example`과 `frontend/.env.example`이 단일 출처입니다.

## 배포 구조

Render Web Service 2개. 상세와 주의사항은 [`DEPLOYMENT_PLAN.md`](DEPLOYMENT_PLAN.md).

| 서비스 | 이름 | Root Directory |
|---|---|---|
| Backend | `MS-FlowHub` | `backend` |
| Frontend | `ms-flowhub-frontend` | `frontend` |

두 서비스 모두 `Auto-Deploy: After CI Checks Pass`입니다.
**Root Directory 밖만 바꾼 커밋(문서 등)은 배포되지 않습니다** — Events에 `Deploy skipped`로 남고
이는 정상 동작입니다.

## 확인 필요

- `src/storage/`가 빈 디렉터리입니다. `AGENTS.md`에는 "`localStorage`는 별도 storage 레이어를
  사용한다"는 규칙이 있지만, 실제로는 `features/auth/session-timeout.ts`와
  `features/ax/ax-assistant-provider.tsx`가 `window.localStorage`를 직접 호출합니다.
  규칙을 되살릴지, 규칙을 현실에 맞출지 정해지지 않았습니다.
