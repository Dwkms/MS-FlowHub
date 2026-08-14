# 배포 기획 (Render)

> 상태: 2026-08-06 배포 완료 후 실제 Render 운영 설정과 주의사항을 함께 기록합니다.

## 1. 배포 구조 결정

프론트엔드(Next.js)와 백엔드(FastAPI)를 모두 **Render**에 올립니다. Vercel은 프론트엔드에는 적합하지만, 현재 백엔드가 요청마다 동기 SQLAlchemy 세션으로 Supabase PostgreSQL에 직접 연결하는 상시 서버 구조라 Vercel의 서버리스 Python 함수와는 맞지 않습니다(커넥션 풀 고갈, 실행시간 제한 위험). Render는 두 서비스 모두 상시 서버(Web Service)로 올릴 수 있어 지금 코드를 거의 고치지 않고 배포할 수 있고, 관리 화면도 하나로 모입니다.

```
Render
 ├─ MS-FlowHub          (FastAPI, Python Web Service)
 └─ ms-flowhub-frontend (Next.js, Node Web Service)
DB: 기존 Supabase PostgreSQL 그대로 사용 (별도 이전 없음)
Storage: 기존 Supabase Storage 비공개 버킷 그대로 사용
```

## 2. 사전 확인 (이미 해결된 배포 리스크)

- 채용 포스터 파일이 로컬 디스크가 아니라 Supabase Storage에 저장되도록 이미 전환했습니다. Render의 파일시스템은 재배포 시 초기화되므로, 이 전환이 없었다면 배포 후 첨부 파일이 사라지는 문제가 있었을 것입니다. → **해결됨**
- 2026-08-14 기준 Supabase Alembic head는 `20260814_0024`이며 code head와 운영 DB current가 같습니다.
- `app/main.py`에 모듈 레벨 `app = create_app()`이 있어 `uvicorn app.main:app`으로 바로 실행할 수 있습니다.
- `frontend/package.json`에 `start` 스크립트(`next start`)가 이미 있어 별도 설정 없이 실행할 수 있습니다.

## 3. Render 백엔드 서비스 설정

| 항목 | 값 |
|---|---|
| 서비스 이름 | **`MS-FlowHub`** (계획 단계의 가칭 `ms-flowhub-backend`가 아닙니다) |
| 서비스 URL | **`https://ms-flowhub.onrender.com`** |
| Root Directory | `backend` |
| Build Command | `pip install .` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |
| Auto-Deploy | `After CI Checks Pass` (2026-08-13 전환) |
| Build Filters | Included·Ignored 모두 비어 있음 |

> **URL 주의.** 아래 환경변수 표의 `ms-flowhub-backend.onrender.com`은 계획 당시의 예시이고
> **실재하지 않는 호스트**입니다. 그 주소로 요청하면 Render가 `x-render-routing: no-server`와
> 함께 404를 돌려줍니다. 실제 백엔드는 위 `ms-flowhub.onrender.com`입니다.
> (2026-08-13 확인: `/health` → `{"status":"ok","data_source":"supabase","service":"MS FlowHub"}`)

### 환경변수 (Render 대시보드에 등록)

| 변수 | 값 |
|---|---|
| `DATABASE_URL` | 기존 `backend/.env`의 값과 동일 |
| `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `SUPABASE_JWKS_URL` | 기존 값과 동일 |
| `FRONTEND_ORIGIN` | 프론트엔드 Render URL (예: `https://ms-flowhub-frontend.onrender.com`) |
| `AI_PROVIDER` | 미설정 시 기본값(`mock`) 사용, 변경 불필요 |

`SUPABASE_SECRET_KEY`와 `DATABASE_URL`은 절대 프론트엔드 서비스나 `NEXT_PUBLIC_*` 변수에 넣지 않습니다.

## 4. Render 프론트엔드 서비스 설정

| 항목 | 값 |
|---|---|
| 서비스 URL | **`https://ms-flowhub-frontend.onrender.com`** (실재 확인됨) |
| Root Directory | `frontend` |
| Build Command | `npm install && npm run build` |
| Start Command | `npm run start -- -p $PORT` |
| Auto-Deploy | `After CI Checks Pass` (2026-08-13 전환) |

### 환경변수

| 변수 | 값 |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | 기존 `frontend/.env.local`과 동일 |
| `BACKEND_URL` | 백엔드 Render URL = **`https://ms-flowhub.onrender.com`** — `next.config.ts`의 `/api/*` rewrite 대상 |
| `NEXT_PUBLIC_API_BASE_URL` | 비워둠 (Next.js 프록시를 그대로 사용) |

## 5. 배포 순서

1. 백엔드 서비스를 먼저 생성·배포하고 `/health`가 `{"status":"ok"}`를 반환하는지 확인한다.
2. 프론트엔드 서비스를 생성·배포하며 `BACKEND_URL`에 1번의 백엔드 URL을 넣는다.
3. 백엔드의 `FRONTEND_ORIGIN`을 2번의 프론트엔드 URL로 갱신하고 백엔드를 재시작한다(CORS).
4. Supabase 대시보드 Auth 설정의 허용 URL 목록에 프론트엔드 도메인을 추가한다(로그인 리디렉션 대비).

## 6. 배포 후 스모크 테스트

- 로그인 → 대시보드 로딩 → 지표·최근 업무 표시
- 직원·조직 관리: 목록 조회, 이름 클릭 → 상세, 근무 상태 변경
- 전자결재: 문서 작성 → 상신 → 승인
- 채용 요청 → 포스터 첨부 → 채용공고 생성 → 지원자 등록 (Supabase Storage 왕복 확인)
- 직원 매뉴얼 조회
- 브라우저 개발자 도구에서 CORS 오류, 401/403이 없는지 확인

## 7. 알려진 제약

- Render 무료 플랜은 일정 시간 요청이 없으면 서비스가 잠들고, 다음 요청 시 콜드스타트(수십 초)가 발생합니다. 배포 실패가 아니라 무료 플랜의 정상 동작입니다.
- **백엔드가 잠든 동안 프론트엔드의 `/api/*` 프록시는 기다리지 않고 즉시 502를 반환합니다.** 로그인 화면은 200으로 뜨는데 데이터 조회만 실패하므로 장애로 오인하기 쉽습니다. 상세와 판별법은 [`TROUBLESHOOTING.md`](../TROUBLESHOOTING.md)의 "화면은 뜨는데 API만 502"를 보세요.
- **문서만 바꾼 커밋은 두 서비스 모두 배포되지 않습니다.** Root Directory가 각각 `backend`·`frontend`이고, Render는 Root Directory 안에 변경이 없으면 auto-deploy를 건너뜁니다(Events에 `Deploy skipped`). Build Filter나 `[skip render]` 마커와는 무관한 별개 동작입니다.
- 자동 CI는 [`ci.yml`](../.github/workflows/ci.yml)로 도입했고, 2026-08-13부터 두 서비스의 Auto-Deploy가 `After CI Checks Pass`입니다. E2E([`e2e.yml`](../.github/workflows/e2e.yml))는 수동 실행 전용이라 이 게이트에 포함되지 않습니다.
