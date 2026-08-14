# MS FlowHub 문제 해결

프로젝트에서 실제로 확인한 오류와 해결 방법을 기록합니다. 기능 사용 중 문제가 생기면 증상에 해당하는 항목부터 확인하세요.

## 목차

- [채용 요청 작성이 500으로 끝남](#채용-요청-작성이-500으로-끝남)
- [AI 채용 포스터 생성이 500으로 끝남](#ai-채용-포스터-생성이-500으로-끝남)
- [AI 포스터 시안이 메뉴 이동 후 사라짐](#ai-포스터-시안이-메뉴-이동-후-사라짐)
- [채용공고의 주요 업무와 역량이 두 번 표시됨](#채용공고의-주요-업무와-역량이-두-번-표시됨)
- [대시보드의 2차면접과 최종입사 인원이 예상과 다름](#대시보드의-2차면접과-최종입사-인원이-예상과-다름)
- [로그인 후 다시 로그인 화면으로 이동](#로그인-후-다시-로그인-화면으로-이동)
- [Invalid login credentials](#invalid-login-credentials)
- [로그인 후 백엔드 401 Unauthorized](#로그인-후-백엔드-401-unauthorized)
- [업무 API의 401 또는 403](#업무-api의-401-또는-403)
- [E2E 테스트 계정이 직원 목록에 보임](#e2e-테스트-계정이-직원-목록에-보임)
- [로그인 직후 Cannot read properties of undefined](#로그인-직후-cannot-read-properties-of-undefined)
- [Pytest Starlette TestClient 경고](#pytest-starlette-testclient-경고)
- [Supabase Storage 객체를 찾지 못했는데 HTTP 404가 아닌 400 응답](#supabase-storage-객체를-찾지-못했는데-http-404가-아닌-400-응답)
- [AX 도우미가 "관련 매뉴얼이나 FAQ를 찾지 못했습니다"만 반복](#ax-도우미가-관련-매뉴얼이나-faq를-찾지-못했습니다만-반복)
- [AX 도우미가 후보만 제시하고 답을 확정하지 않음](#ax-도우미가-후보만-제시하고-답을-확정하지-않음)
- [메뉴를 이동하면 도우미 대화가 사라짐](#메뉴를-이동하면-도우미-대화가-사라짐)
- [화면은 뜨는데 API만 502 (운영)](#화면은-뜨는데-api만-502-운영)
- [master에 반영했는데 운영에 배포되지 않음](#master에-반영했는데-운영에-배포되지-않음)
- [검증이 실패했는데 커밋·push가 그대로 나감](#검증이-실패했는데-커밋push가-그대로-나감)
- [alembic 실행 시 ImportError: cannot import name '<model>'](#alembic-실행-시-importerror-cannot-import-name-model)
- [E2E 종료 후 테스트 계정이 지워지지 않음](#e2e-종료-후-테스트-계정이-지워지지-않음)
- [문서 링크 검사에서 Join-Path가 빈 경로로 실패](#문서-링크-검사에서-join-path가-빈-경로로-실패)
- [PowerShell 검색 문자열의 Markdown 백틱 때문에 파서 오류](#powershell-검색-문자열의-markdown-백틱-때문에-파서-오류)
- [샌드박스에서 Alembic current가 Permission denied로 실패](#샌드박스에서-alembic-current가-permission-denied로-실패)
- [저장소 루트에서 Alembic을 실행하면 migrations 경로를 찾지 못함](#저장소-루트에서-alembic을-실행하면-migrations-경로를-찾지-못함)
- [PowerShell 다중 속성 정렬의 잘못된 매개 변수 구문](#powershell-다중-속성-정렬의-잘못된-매개-변수-구문)

## 화면은 뜨는데 API만 502 (운영)

로그인 화면은 정상으로 뜨는데 포털에 들어가면 직원·전자결재·채용 목록이 전부 비거나 오류가 납니다. 개발자 도구 Network에서 `/api/v1/...` 요청만 **502**입니다.

### 원인

Render 무료 플랜에서 **백엔드가 잠들어 있는 상태**입니다. 프론트엔드는 별도 서비스라 깨어 있고, `next.config.ts`의 `/api/:path*` rewrite가 잠든 백엔드에 연결하지 못해 502를 냅니다.

**콜드스타트를 기다리지 않고 즉시 실패합니다.** 2026-08-13 측정에서 502가 **0.4초** 만에 돌아왔고, 타임아웃을 240초로 늘려도 같았습니다. `next.config.ts`의 `proxyTimeout: 180_000`은 연결이 된 뒤의 응답 대기에만 적용되므로 이 경우를 늘려주지 않습니다.

### 판별

백엔드를 직접 호출해 구분합니다.

```powershell
Invoke-WebRequest https://ms-flowhub.onrender.com/health -UseBasicParsing
```

| 결과 | 의미 |
|---|---|
| 첫 호출이 수십 초 걸린 뒤 200 | 잠들어 있었을 뿐. 깨어났으니 화면을 새로고침하면 정상 |
| 바로 200 | 백엔드는 정상. 502의 원인이 다른 곳(프론트 `BACKEND_URL` 설정 등) |
| 404 + 응답 헤더 `x-render-routing: no-server` | **주소가 틀렸습니다.** 그 호스트에는 서비스가 없습니다 |

세 번째가 특히 헷갈립니다. `ms-flowhub-backend.onrender.com`은 [`DEPLOYMENT_PLAN.md`](docs/DEPLOYMENT_PLAN.md)의 계획 단계 예시일 뿐 **실재하지 않는 주소**입니다. 실제 백엔드는 **`https://ms-flowhub.onrender.com`**(서비스 이름 `MS-FlowHub`)입니다.

### 해결

백엔드를 한 번 깨우면 됩니다. 위 `/health`를 호출하거나 브라우저로 열고, 200을 받은 뒤 화면을 새로고침합니다. 장애가 아니라 무료 플랜의 정상 동작입니다.

상시 대응이 필요하면 유료 인스턴스로 올리거나 주기적으로 `/health`를 호출해 깨워두는 방법이 있습니다. 현재는 도입하지 않았습니다.

## master에 반영했는데 운영에 배포되지 않음

머지하고 push했는데 Render가 옛 커밋에 머물러 있습니다. Events에 아무 기록이 없거나 `Deploy skipped`만 남습니다.

### 원인

두 서비스의 **Root Directory가 각각 `backend`·`frontend`** 입니다. Render는 그 디렉터리 안에 변경이 없으면 auto-deploy를 건너뜁니다. 판정 기준은 **push의 tip 커밋**입니다.

2026-08-14에 실제로 겪은 경우입니다.

```
136bbd7  Merge branch 'feat/part-admin-role'   ← backend·frontend 변경 있음
e7235e8  docs: 파트장 체계 반영과 프리즈 해제 기록  ← 문서 5개뿐  (push의 tip)
```

**코드 머지와 문서 커밋을 한 번에 push했고 tip이 문서라 배포가 통째로 건너뛰어졌습니다.** CI는 통과했는데 운영은 그대로였습니다.

`Deploy skipped` 이벤트가 **항상 남지도 않습니다.** 같은 날 문서 push 여러 건 중 두 건만 기록됐습니다. 이벤트가 없다고 "아직 처리 중"으로 보면 안 됩니다.

### 한쪽 서비스만 배포되는 경우

`backend/`만 바꾼 커밋은 Backend만 배포되고 Frontend는 옛 코드로 남습니다. 백엔드가 새 역할을 알고 프론트는 모르는 **불일치 상태**가 됩니다.

### 판별

Render 각 서비스 상단의 커밋 해시를 봅니다. `master` 최신과 다르면 그 서비스는 배포되지 않은 것입니다.

### 해결

- **이미 벌어졌다면**: 해당 서비스에서 `Manual Deploy` → `Deploy latest commit`. master 최신을 배포하므로 밀린 변경이 함께 나갑니다. CI를 통과한 커밋이라면 게이트 우회가 아니라 못 받은 트리거를 보충하는 것입니다.
- **예방**: **코드 커밋을 push의 마지막에 둡니다.** 문서와 코드를 함께 올릴 때는 코드 push를 먼저 하고 문서를 뒤에 올리거나, 최소한 tip이 코드 커밋이 되게 합니다.

## 검증이 실패했는데 커밋·push가 그대로 나감

`pytest`가 실패했는데 커밋과 push가 진행됐습니다.

### 원인

파이프가 종료 코드를 덮어씁니다.

```bash
pytest -q 2>&1 | tail -2 && git commit ...   # tail의 종료 코드(0)가 쓰인다
```

`&&` 체인은 마지막 명령의 종료 코드를 보므로, `tail`이 성공하면 pytest 실패가 묻힙니다. 2026-08-14에 이 방식으로 깨진 커밋 `9a7864b`가 실제로 push됐습니다.

### 해결

출력을 파일로 받고 종료 코드를 직접 확인합니다.

```bash
pytest -q > /tmp/pt.txt 2>&1; echo "exit=$?"; tail -2 /tmp/pt.txt
```

`exit=0`을 눈으로 확인한 뒤에 커밋합니다. 요약만 보려고 파이프를 쓸 때는 `set -o pipefail`을 켜거나 커밋 명령과 분리해서 실행합니다.

### 결과적으로 확인된 것

이 사고 덕분에 배포 게이트의 **차단 동작이 실증됐습니다.** CI가 실패한 `9a7864b`는 배포되지 않았고, 수정본 `dda951e`만 Live가 됐습니다.

## alembic 실행 시 ImportError: cannot import name '<model>'

`alembic upgrade head`가 마이그레이션을 시작하기도 전에 죽습니다.

```
File "backend\migrations\env.py", line 8, in <module>
    from app.models import approval, auth, manual, notification, organization, recruitment
ImportError: cannot import name 'notification' from 'app.models'
```

### 원인

**모델 파일을 지웠는데 `backend/migrations/env.py`의 import를 안 고친 것입니다.**

`env.py`는 autogenerate가 `Base.metadata`를 채우도록 모든 모델 모듈을 한 줄로 import합니다.
이 줄은 `# noqa: F401`이 붙어 있어 **Ruff가 미사용 import로 잡아주지 않습니다.** 그래서
`ruff check`·`pytest`가 전부 통과해도 alembic만 따로 깨집니다.

2026-08-14 알림 기능 제거 때 실제로 겪었습니다. 코드·테스트·배포까지 다 통과한 뒤
migration 적용 단계에서야 드러났습니다.

### 판별

모델을 지웠으면 `env.py`의 import 목록과 실제 모델 파일을 대조합니다.

```bash
grep -n "from app.models import" backend/migrations/env.py
ls backend/app/models/
```

`alembic current`가 가장 확실합니다. env.py를 그대로 불러오므로 import가 깨져 있으면 여기서 바로 터집니다.

### 해결

`env.py`의 import 목록에서 지운 모델을 빼면 됩니다.

**모델을 삭제할 때 함께 볼 곳** — 셋 다 `# noqa`가 붙어 Ruff에 안 걸립니다.

| 파일 | 역할 |
|---|---|
| `backend/app/models/__init__.py` | 모델 패키지 export |
| `backend/migrations/env.py` | autogenerate용 메타데이터 수집 |
| `backend/tests/conftest.py` | 테스트 DB 테이블 생성 |

## E2E 종료 후 테스트 계정이 지워지지 않음

`npm run test:e2e`가 테스트는 전부 통과하는데 마지막 정리에서 실패합니다.

```
psycopg.errors.ForeignKeyViolation: update or delete on table "approval_documents"
violates foreign key constraint "recruitment_requests_approval_document_id_fkey"
Error: app.scripts.cleanup_test_auth_accounts 실행에 실패했습니다.
```

정리가 멈췄으므로 **E2E 계정이 운영 DB에 그대로 남습니다.**

### 원인

**E2E 계정으로 화면을 수동 조작하면 업무 데이터가 생깁니다.**

E2E 계정은 자동 테스트용이지만, 사람이 그 계정으로 로그인해 채용 요청을 만들면 결재 문서·
채용 요청·공고·지원자·AI 기록이 그 계정 이름으로 남습니다. 직원을 참조하는 FK는 대부분
`RESTRICT`라, 그 데이터가 있는 한 계정을 지울 수 없습니다.

2026-08-14에 겪은 실제 상황입니다. 참조가 6개 테이블에 걸쳐 23건 있었습니다.

```
approval_histories.actor_id        9건
ai_generations.created_by_id       6건
approval_documents.author_id       3건
approval_documents.approver_id     2건
employee_accounts.employee_id      2건   (CASCADE)
recruitment_requests.requester_id  1건
```

작성자 한 곳만 바꿔서는 해결되지 않습니다. 다음 FK에서 다시 막힙니다.

### 판별

계정을 지우기 전에 참조를 세어 봅니다.

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.cleanup_test_auth_accounts --e2e-only
```

현재 스크립트는 **연쇄 삭제로 밀어붙이지 않고** 어떤 테이블에 몇 건이 남았는지 출력하고
중단합니다. 출력된 목록이 곧 처리해야 할 대상입니다.

### 해결

업무 데이터가 시연에 필요한지 먼저 판단합니다.

**보존할 경우** — 해당 레코드의 작성자를 실제 직원으로 옮깁니다. 옮길 곳은 업무 흐름상
자연스러운 사람이어야 합니다. 백엔드 개발자 채용 요청이면 개발팀장이 요청하고 대표이사가
결재하는 형태가 맞습니다.

**주의**: 결재자와 같은 사람으로 옮기면 안 됩니다. 이 프로젝트는 "작성자와 결재자는 같을 수
없다"와 "본인 문서 자가승인 금지"를 업무 규칙으로 막고 있어서, 코드가 막는 상태를 데이터로
만들어 두면 나중에 읽는 사람이 규칙을 오해합니다.

이관은 **단일 트랜잭션**으로 묶고 마지막에 참조가 0건인지 확인한 뒤 커밋합니다. 하나라도
남으면 전체를 롤백해야 합니다. 절반만 바뀐 상태가 가장 나쁩니다.

**버릴 경우** — 연결된 공고·지원자까지 함께 사라진다는 점을 확인하고 지웁니다. 대시보드
ATS 지표가 그 데이터로 계산되므로 지우면 0이 됩니다.

### 예방

**E2E 계정으로 수동 검증을 하지 마세요.** 화면을 손으로 확인할 때는 실제 직원 계정을 씁니다.
E2E 계정은 자동 테스트가 만들고 지우는 용도입니다.

`E2E 결재 `로 시작하는 문서만 자동 삭제 대상입니다. 그 밖의 제목을 가진 문서는 사람이 만든
것으로 보고 스크립트가 건드리지 않습니다.

## 채용 요청 작성이 500으로 끝남

### 원인

애플리케이션 모델에는 최소 경력·학력·근무지·급여·모집 마감일·지원 방법 칼럼이 있지만 실제 DB에 migration `20260813_0023`이 적용되지 않으면, 채용 요청을 저장하는 SQL이 존재하지 않는 칼럼을 참조해 `500`이 발생합니다. 폼이나 API 로직의 문제가 아닙니다.

### 해결

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current
```

`current` 결과가 `20260813_0023 (head)`인지 확인한 뒤 Backend를 다시 시작합니다. 같은 증상이 나오면 코드를 먼저 수정하지 말고 애플리케이션이 사용하는 `DATABASE_URL`과 migration 대상 DB가 같은지 확인합니다.

## AI 채용 포스터 생성이 500으로 끝남

### 원인

로컬 Frontend가 `/api` 요청을 Next.js rewrite로 전달할 때 기본 프록시 timeout이 이미지 생성 시간보다 짧으면 발생합니다. OpenAI와 Backend에서는 이미지 생성과 사용 기록 저장이 성공했어도 Next.js가 먼저 연결을 끊어 화면에는 `500`과 `socket hang up`이 나타날 수 있습니다.

### 해결

`frontend/next.config.ts`의 `experimental.proxyTimeout`을 Backend의 `IMAGE_AI_TIMEOUT_SECONDS`보다 길게 유지합니다. 현재 값은 각각 180초와 120초입니다. 설정 변경 후 Frontend를 다시 시작합니다.

이 오류 직후 생성 버튼을 연속으로 누르면 이미 성공한 요청에 이어 새 유료 호출이 발생할 수 있습니다. 먼저 `frontend/.next/dev/logs/next-development.log`에서 `socket hang up` 여부와 `ai_generations`의 최근 `JOB_POSTER` 기록을 확인합니다.

## AI 포스터 시안이 메뉴 이동 후 사라짐

### 원인

생성 이미지는 Base64 미리보기로 응답해 현재 화면의 상태에만 보관합니다. `ai_generations`에는 형식·크기 같은 메타데이터만 기록하고 이미지 원문은 저장하지 않으며, 기존 채용 포스터 첨부 파일을 자동으로 덮어쓰지도 않습니다. 따라서 메뉴를 벗어나 컴포넌트가 종료되면 시안이 사라지는 것이 현재 설계상 정상입니다.

### 대응

마음에 드는 시안을 선택한 뒤 화면을 나가기 전에 PNG로 다운로드합니다. 메뉴 재진입 후 복구가 필요하다면 별도 Storage 저장·조회·삭제 정책과 DB 연결 칼럼을 먼저 설계해야 합니다.

## 채용공고의 주요 업무와 역량이 두 번 표시됨

### 원인

공고 화면이 `주요 업무`·`필수 역량`·`우대 사항`을 전용 블록으로 표시하면서, 자동 조립된 `공고 본문`에도 같은 세 항목이 들어가 중복되었습니다.

### 해결

새 공고 본문을 만들 때 세 항목을 다시 붙이지 않도록 조립 규칙을 변경했습니다. 이미 저장된 공고는 원문을 훼손하지 않고 화면 표시 단계에서 중복 블록만 제외합니다.

## 대시보드의 2차면접과 최종입사 인원이 예상과 다름

### 원인

`전체 채용공고 현황`은 현재 선택한 공고 한 건이 아니라 모든 채용공고의 지원자를 합산합니다. 화면의 네 단계는 실제 상태를 다음처럼 묶습니다.

- `APPLIED`, `SCREENING` → 서류전형
- `INTERVIEW` → 1차면접
- `OFFERED` → 2차면접
- `HIRED` → 최종입사
- `REJECTED` → 진행 단계 집계에서 제외

따라서 다른 공고에 제안·입사 상태 지원자가 있으면 2차면접과 최종입사 수가 현재 보고 있는 공고보다 크게 보일 수 있으며, 불합격자가 두 단계로 들어간 것은 아닙니다.

### 확인 방법

지원자 관리에서 채용공고 필터를 하나씩 선택해 상태별 인원을 확인하고 전체 합계와 비교합니다. 신규 지원자 등록이 대시보드에 반영되는지는 Backend 회귀 테스트로도 고정되어 있습니다.

## 로그인 후 다시 로그인 화면으로 이동

### 원인

Supabase Auth 로그인에는 성공했지만 `employee_accounts`에 인증 사용자와 직원의 연결이 없거나, 계정·직원이 비활성 상태일 때 발생합니다. FastAPI는 연결되지 않은 인증 계정의 업무 API 접근을 차단합니다.

### 해결

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m app.scripts.seed_auth_accounts
```

그 뒤 `backend/.env`의 Supabase 설정과 `frontend/.env.local`의 공개 Supabase 설정이 같은 프로젝트를 가리키는지 확인하고, 백엔드와 프론트엔드를 다시 시작합니다.

## Invalid login credentials

### 원인

입력한 이메일 또는 비밀번호가 Supabase Auth에 저장된 값과 다르거나, 비밀번호를 변경한 뒤 이전 비밀번호를 입력한 경우입니다.

### 해결

- 이메일 주소와 현재 비밀번호를 다시 확인합니다.
- 초기 Seed 계정이라면 `AUTH_SEED_DEFAULT_PASSWORD` 값을 확인합니다.
- 비밀번호를 변경한 경우 로그인 화면의 **비밀번호 변경**에서 현재 비밀번호를 기준으로 다시 설정합니다.

비밀번호와 access token은 화면 캡처, 소스 코드, 로그에 남기지 않습니다.

## 로그인 후 백엔드 401 Unauthorized

### 원인

브라우저에 이전 세션 token이 남아 있거나, 백엔드가 재시작 전 환경변수를 사용 중이거나, Supabase JWT/JWKS 설정이 서로 다른 프로젝트를 가리킬 때 발생할 수 있습니다.

### 해결

1. 브라우저에서 로그아웃한 뒤 다시 로그인합니다.
2. 백엔드 터미널에서 종료한 뒤 프로젝트 루트의 `run-backend.cmd`를 다시 실행합니다.
3. `backend/.env`의 `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_JWKS_URL`이 같은 Supabase 프로젝트인지 확인합니다.
4. 브라우저 DevTools Network에서 업무 API 요청에 `Authorization: Bearer ...` 헤더가 포함됐는지 확인합니다.

## 업무 API의 401 또는 403

### 원인

- `401 Unauthorized`: 로그인 세션 또는 Bearer token이 없거나 유효하지 않습니다.
- `403 Forbidden`: 로그인은 성공했지만 역할 또는 팀 범위에 맞지 않는 요청입니다.

### 해결

- 401은 로그아웃·재로그인과 Supabase 환경변수 일치 여부를 먼저 확인합니다.
- 403은 현재 계정의 역할과 대상 직원·결재 문서의 권한 범위를 확인합니다.
- 권한은 프론트엔드 버튼 표시와 별개로 백엔드에서 다시 검증되므로, URL 또는 Network 요청을 직접 바꿔도 우회할 수 없습니다.

## E2E 테스트 계정이 직원 목록에 보임

### 원인

Playwright E2E 테스트는 로그인·권한 시나리오를 위해 전용 일반 직원과 SUPER_ADMIN 계정을 테스트 시작 전에 만듭니다. 테스트가 강제 종료되면 종료 정리 단계가 실행되지 않을 수 있습니다.

### 해결

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.cleanup_test_auth_accounts --e2e-only
```

정상적으로 `npm run test:e2e`를 끝까지 실행하면 `globalTeardown`이 전용 직원과 Auth 계정을 자동으로 삭제합니다.

## 로그인 직후 Cannot read properties of undefined

### 원인

안내용 mock 사용자를 제거한 뒤, 로그인 화면에서 업무 홈으로 이동하는 순간 실제 인증 직원 정보가 준비되기 전에 상단 사용자 영역이 렌더링되어 발생했던 오류입니다.

### 해결 결과

`AuthSessionGuard`가 현재 경로의 인증과 직원 동기화가 끝난 뒤에만 업무 화면을 렌더링하도록 변경했습니다. Playwright로 로그인·새로고침 세션 유지·로그아웃을 다시 검증했습니다.

## Pytest Starlette TestClient 경고

### 증상

Pytest 실행 시 Starlette `TestClient` 내부의 오래된 `httpx` 연동 방식에 대한 deprecation 경고가 1개 표시될 수 있습니다.

### 원인과 대응

프로젝트의 FastAPI 업무 코드 오류가 아니라 테스트 라이브러리 내부의 호환성 경고입니다. 현재 백엔드 테스트는 정상 통과합니다. FastAPI·Starlette·httpx 의존성을 함께 올리는 별도 의존성 업데이트 작업에서 호환성 확인 후 정리합니다.

## Supabase Storage 객체를 찾지 못했는데 HTTP 404가 아닌 400 응답

### 증상

`urlopen`으로 Supabase Storage Object API(`/storage/v1/object/...`)를 직접 호출할 때, 버킷이나 객체가 없으면 예상과 달리 `HTTPError`의 `code`가 `404`가 아니라 `400`으로 옵니다.

### 원인

Supabase Storage는 없음 상태를 HTTP 상태 코드가 아니라 응답 본문(JSON)의 `code`(`NoSuchBucket`, `NoSuchKey`)와 `statusCode`(문자열 `"404"`) 필드로 표현합니다. `error.code`만 확인하면 없음 상태를 감지하지 못합니다.

### 해결

`app/core/supabase_storage.py`와 `app/scripts/setup_storage_bucket.py`는 `HTTPError` 발생 시 `error.code == 404`뿐 아니라 응답 본문에 `NoSuchKey`, `NoSuchBucket`, `"404"`가 포함되는지 함께 확인해 없음 상태를 판단합니다. Supabase Storage REST API를 새로 호출하는 코드를 추가할 때는 이 패턴을 재사용하세요.

## AX 도우미가 "관련 매뉴얼이나 FAQ를 찾지 못했습니다"만 반복

### 원인

두 가지가 있습니다.

1. **문서에 그 내용이 실제로 없는 경우.** 도우미는 등록된 매뉴얼·FAQ에서만 답을 찾습니다. 문서에 없는 사실은 어떤 검색 방식으로도 만들어낼 수 없습니다.
2. **질문 표현이 문서 어휘와 다른 경우.** 예를 들어 FAQ가 "기능"이라고만 적혀 있으면 "메뉴"로 물었을 때 매칭되지 않습니다.

### 해결

먼저 어느 쪽인지 구분합니다.

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.try_ax_chat "문제가 된 질문"
```

- 관련 없는 문서가 상위에 뜬다면 **표현 차이**입니다. 해당 FAQ·매뉴얼 문구에 직원이 실제로 쓰는 단어를 자연스럽게 반영한 뒤 `python -m app.scripts.seed_faqs`로 반영합니다. 키워드를 억지로 나열하지 말고 문장을 다듬는 방향으로 고칩니다.
- 아무 문서도 걸리지 않는다면 **문서 부재**입니다. FAQ를 새로 추가해야 합니다. 이때 기존 항목의 `display_order`가 밀리지 않도록 `FAQS` 목록 **끝에** 추가하세요.

운영 DB에 반영하기 전에는 무엇이 바뀌는지 먼저 확인하는 것을 권장합니다. Seed는 upsert 전용이며 DELETE를 수행하지 않습니다.

`ax_chat_logs` 테이블의 `top_candidates`에 상위 후보 3개가 남으므로, 쌓인 로그로도 같은 구분을 할 수 있습니다.

## AX 도우미가 후보만 제시하고 답을 확정하지 않음

### 원인

오답을 내지 않기 위한 의도된 동작입니다. 1위 점수가 확신 임계값(0.30)을 넘고 2위와의 차이가 마진(0.05) 이상일 때만 확정 답변을 냅니다. 접전이면 확신하지 않고 후보를 제시합니다.

내용이 비슷한 FAQ가 둘 이상일 때 자주 발생합니다. 예를 들어 "채용 요청 작성"은 `recruitment-create`와 `recruitment-posting-created` 두 문서가 모두 높은 점수를 받습니다.

### 대응

- 사용자 입장에서는 후보를 누르면 그 질문으로 다시 물어 확정 답변을 받을 수 있습니다.
- 자주 반복된다면 두 FAQ의 질문 문구를 서로 더 구분되게 다듬습니다.
- **임계값을 임의로 낮추지 마세요.** 값은 실제 문서와 무관 질문 11개로 실측해 오답 0건을 제약으로 정한 것입니다. 근거는 `docs/archive/AX_FAQ_CHATBOT_PLAN.md` 4장을 참고하고, 바꿀 때는 같은 방식으로 다시 측정하세요.

## 메뉴를 이동하면 도우미 대화가 사라짐

### 원인

`AuthSessionGuard`는 경로가 바뀔 때마다 세션을 다시 확인하며, 확인이 끝나기 전에는 children 대신 로딩 화면을 렌더링합니다. 이때 `PortalShell`과 그 하위 컴포넌트가 통째로 언마운트되므로, 도우미 상태를 그 안에 두면 메뉴를 옮길 때마다 초기화됩니다.

### 해결 결과

도우미 상태를 `AxAssistantProvider`로 분리해 `AuthSessionGuard` **바깥**(`app/layout.tsx`)에 두었습니다. 세션 가드는 보안 로직이라 변경하지 않았습니다.

전역에 떠 있으면서 화면 전환에도 살아남아야 하는 UI를 새로 추가할 때는 같은 위치에 두어야 합니다.

## 문서 링크 검사에서 Join-Path가 빈 경로로 실패

### 증상

루트의 `README.md`·`UPDATELOG.md`처럼 디렉터리 부분이 없는 상대경로를 대상으로 Markdown 링크를
검사할 때, PowerShell `Join-Path`가 `Path` 인수의 빈 문자열을 거부하며 검사가 중단됩니다.

### 원인

`Split-Path -Parent README.md`의 결과는 빈 문자열입니다. 이를 그대로 `Join-Path`의 기준 경로로
넘겼기 때문입니다. `docs/*.md`처럼 상위 디렉터리가 있는 파일에서는 발생하지 않습니다.

### 판별

오류 메시지에 `Join-Path: 'Path' 매개 변수가 빈 문자열`이 표시되고 대상 파일이 저장소 루트의
Markdown인지 확인합니다. 프로젝트의 Markdown 링크나 애플리케이션 코드 오류는 아닙니다.

### 해결

`Split-Path -Parent` 결과가 비어 있으면 현재 작업 폴더를 기준 경로로 사용합니다. 진단 스크립트는
루트 파일과 하위 폴더 파일을 구분해 기준 경로를 정한 뒤 다시 실행합니다.

## PowerShell 검색 문자열의 Markdown 백틱 때문에 파서 오류

### 증상

PowerShell에서 `rg` 검색식을 큰따옴표로 감싸고 그 안에 Markdown 인라인 코드의 백틱을 넣으면
`문자열에 " 종결자가 없습니다`라는 파서 오류로 명령이 실행되지 않습니다.

### 원인

백틱은 PowerShell의 이스케이프 문자입니다. Markdown의 백틱까지 검색하려고 큰따옴표 문자열 안에
그대로 넣으면 뒤따르는 문자를 이스케이프해 문자열 경계가 깨질 수 있습니다.

### 판별

애플리케이션 실행 전 PowerShell 파서 단계에서 실패하고, 명령 문자열에 큰따옴표와 백틱이 함께
있는지 확인합니다. `rg`나 검색 대상 파일의 오류는 아닙니다.

### 해결

검색에 백틱이 꼭 필요하지 않다면 제거합니다. 필요하면 작은따옴표 문자열을 쓰거나 백틱을 명시적으로
이스케이프합니다. 이번 문서 점검은 백틱 없는 검색어로 다시 실행했습니다.

## 샌드박스에서 Alembic current가 Permission denied로 실패

### 증상

`python -m alembic current`가 Supabase pooler의 5432 포트에 연결할 때
`psycopg.OperationalError`와 Windows 소켓 오류 `10013 Permission denied`로 실패합니다.

### 원인

DB나 migration 오류가 아니라 실행 샌드박스가 외부 PostgreSQL 연결을 차단한 경우입니다.
같은 명령을 네트워크 접근이 허용된 환경에서 실행하면 정상 연결됩니다.

### 판별

Ruff와 pytest는 통과하지만 Alembic의 최초 DB 연결에서만 `10013`이 발생하는지 확인합니다.
네트워크 접근을 허용해 같은 명령을 다시 실행했을 때 revision이 출력되면 샌드박스 제한입니다.

### 해결

외부 DB 조회가 필요한 검증 명령만 네트워크 접근 승인을 받아 다시 실행합니다. 2026-08-14 재실행에서는
`20260814_0024 (head)`가 출력되어 code head와 운영 DB current가 일치함을 확인했습니다.

## 저장소 루트에서 Alembic을 실행하면 migrations 경로를 찾지 못함

### 증상

저장소 루트에서 `python -m alembic -c backend/alembic.ini heads`를 실행하면
`FAILED: Path doesn't exist: migrations`가 출력됩니다.

### 원인

`backend/alembic.ini`의 migration 경로가 `migrations`라는 상대경로입니다. 설정 파일만 지정하고
작업 폴더를 루트에 두면 Alembic이 루트의 `migrations`를 찾습니다.

### 판별

`backend/migrations`는 실제로 존재하고, `backend`에서 같은 명령을 실행했을 때 revision이 정상
출력되는지 확인합니다. migration 파일 누락이 아니라 실행 위치 문제입니다.

### 해결

문서의 검증 명령처럼 먼저 `cd backend`한 뒤 `python -m alembic heads` 또는
`python -m alembic current`를 실행합니다. 올바른 작업 폴더에서 code head는
`20260814_0024 (head)`로 확인됐습니다.

## PowerShell 다중 속성 정렬의 잘못된 매개 변수 구문

### 증상

CSV 그룹 집계를 `Sort-Object Count -Descending, Name`으로 정렬하려 하면
`매개 변수 목록에 인수가 없습니다`라는 파서 오류가 발생합니다.

### 원인

`-Descending`은 쉼표로 다음 속성을 이어 쓰는 위치 매개 변수 구문과 함께 사용할 수 없습니다.
속성마다 정렬 방향을 지정하려면 계산된 속성 해시 테이블을 사용해야 합니다.

### 판별

CSV를 읽기 전 PowerShell 파서 단계에서 실패하고 오류 위치가 `-Descending, Name`의 쉼표를
가리키는지 확인합니다. CSV 내용이나 인코딩 문제는 아닙니다.

### 해결

`Sort-Object -Property @{Expression='Count';Descending=$true},
@{Expression='Name';Descending=$false}` 형식으로 속성별 방향을 지정해 다시 실행합니다.
