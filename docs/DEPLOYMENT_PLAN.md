# 배포 기획 (Render)

> 상태: 착수 전 기획 문서입니다. 2026-08-06 배포 작업의 체크리스트로 사용합니다. 실제 배포가 끝나면 이 문서 대신 README의 실행 방법을 기준으로 삼고, 이 문서는 `docs/archive`로 옮깁니다.

## 1. 배포 구조 결정

프론트엔드(Next.js)와 백엔드(FastAPI)를 모두 **Render**에 올립니다. Vercel은 프론트엔드에는 적합하지만, 현재 백엔드가 요청마다 동기 SQLAlchemy 세션으로 Supabase PostgreSQL에 직접 연결하는 상시 서버 구조라 Vercel의 서버리스 Python 함수와는 맞지 않습니다(커넥션 풀 고갈, 실행시간 제한 위험). Render는 두 서비스 모두 상시 서버(Web Service)로 올릴 수 있어 지금 코드를 거의 고치지 않고 배포할 수 있고, 관리 화면도 하나로 모입니다.

```
Render
 ├─ ms-flowhub-backend  (FastAPI, Python Web Service)
 └─ ms-flowhub-frontend (Next.js, Node Web Service)
DB: 기존 Supabase PostgreSQL 그대로 사용 (별도 이전 없음)
Storage: 기존 Supabase Storage 비공개 버킷 그대로 사용
```

## 2. 사전 확인 (이미 해결된 배포 리스크)

- 채용 포스터 파일이 로컬 디스크가 아니라 Supabase Storage에 저장되도록 이미 전환했습니다. Render의 파일시스템은 재배포 시 초기화되므로, 이 전환이 없었다면 배포 후 첨부 파일이 사라지는 문제가 있었을 것입니다. → **해결됨**
- 현재 Supabase Alembic head(`20260805_0015`)가 이미 적용되어 있어, 배포 당일 별도 migration 없이 시작할 수 있습니다.
- `app/main.py`에 모듈 레벨 `app = create_app()`이 있어 `uvicorn app.main:app`으로 바로 실행할 수 있습니다.
- `frontend/package.json`에 `start` 스크립트(`next start`)가 이미 있어 별도 설정 없이 실행할 수 있습니다.

## 3. Render 백엔드 서비스 설정

| 항목 | 값 |
|---|---|
| Root Directory | `backend` |
| Build Command | `pip install .` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |

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
| Root Directory | `frontend` |
| Build Command | `npm install && npm run build` |
| Start Command | `npm run start -- -p $PORT` |

### 환경변수

| 변수 | 값 |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | 기존 `frontend/.env.local`과 동일 |
| `BACKEND_URL` | 백엔드 Render URL (예: `https://ms-flowhub-backend.onrender.com`) — `next.config.ts`의 `/api/*` rewrite 대상 |
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
- 자동 CI(GitHub Actions로 push마다 pytest/lint 실행)는 이번 배포 범위에 포함하지 않습니다. 필요하면 이후 별도 작업으로 진행합니다.
