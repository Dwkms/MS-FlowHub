# MS FlowHub 문제 해결

프로젝트에서 실제로 확인한 오류와 해결 방법을 기록합니다. 기능 사용 중 문제가 생기면 증상에 해당하는 항목부터 확인하세요.

## 목차

- [로그인 후 다시 로그인 화면으로 이동](#로그인-후-다시-로그인-화면으로-이동)
- [Invalid login credentials](#invalid-login-credentials)
- [로그인 후 백엔드 401 Unauthorized](#로그인-후-백엔드-401-unauthorized)
- [업무 API의 401 또는 403](#업무-api의-401-또는-403)
- [E2E 테스트 계정이 직원 목록에 보임](#e2e-테스트-계정이-직원-목록에-보임)
- [로그인 직후 Cannot read properties of undefined](#로그인-직후-cannot-read-properties-of-undefined)
- [Pytest Starlette TestClient 경고](#pytest-starlette-testclient-경고)
- [Supabase Storage 객체를 찾지 못했는데 HTTP 404가 아닌 400 응답](#supabase-storage-객체를-찾지-못했는데-http-404가-아닌-400-응답)

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
