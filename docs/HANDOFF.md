# 작업 인계 문서 (Claude → Codex)

> 이 문서는 AI 간 작업 인계를 위한 임시 기록입니다. 2026-08-08 CI/CD·대시보드 작업이 끝나면
> 내용을 `UPDATELOG.md`에 정리하고 이 파일은 삭제합니다.

## 오늘(2026-08-08) 작업 기준

원래 계획은 Claude 메모리에 저장되어 있었습니다: 사용자가 2026-08-07에 미리 전달한 프롬프트로,
우선순위는 **1) CI/CD 안정화 → 2) 업무 데이터 대시보드 설계 → 3) (시간 되면) 1차 구현 → 4) Jira·문서 정리**입니다.
RAG, 전자결재 AI 요약, ATS AI는 이 작업 범위에서 **명시적으로 금지**되어 있습니다.

## 완료된 것 (커밋 `5915d56`, master에 push됨, 작업 트리 깨끗함)

### 1단계: CI/CD 현재 상태 조사

- `.github` 디렉터리 없었음 → CI 전무, Render Auto-Deploy(On Commit)로 push마다 자동 배포되는 구조였음
- 발견한 문제:
  - Python 버전 불일치: 로컬 venv 3.11.6, `backend/pyproject.toml`은 `requires-python = ">=3.12"` → **사용자가 3.12로 확정**
  - Playwright가 Windows 전용(`.\run-backend.cmd`, `.venv/Scripts/python.exe` 하드코딩)이라 CI 러너(Ubuntu)에서 실행 불가
  - E2E가 실제 운영 Supabase에 접속해 계정을 만들고 지움
- 좋은 소식: Backend pytest는 인메모리 SQLite+가짜 Storage라 Supabase 정보 불필요, Frontend build도 Supabase 환경변수 없이 성공 → **CI에 Secret 불필요**

### 2단계: GitHub Actions CI 구축

- `.github/workflows/ci.yml` 신규 — `push`(master)/`pull_request`마다 실행
  - `backend` job: Python 3.12, `pip install -e ".[dev]"`, `ruff check`, `ruff format --check`, `pytest`
  - `frontend` job: Node 24, `npm ci`, `lint`, `typecheck`, `build`
  - 두 job 모두 dependency 캐시 적용, Secret 없음

### 3단계: Playwright CI 전략

- **결론: E2E는 자동 실행에 넣지 않음.** 서비스 롤 키로 실제 Supabase 프로덕션에 접속하는 위험 때문에 `workflow_dispatch`(수동 트리거) 전용 `.github/workflows/e2e.yml`로 분리
  - 필요한 GitHub Secrets(아직 등록 안 됨, e2e.yml 실행하려면 사용자가 직접 등록해야 함):
    `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `SUPABASE_JWKS_URL`, `E2E_EMPLOYEE_PASSWORD`, `E2E_SUPER_ADMIN_PASSWORD`, `E2E_PASSWORD_CHANGE_NEW_PASSWORD`
  - E2E는 전용 직원 2명(`E2E0001`/`E2E0002`, `@msflowhub.test`)만 만들고 지우도록 이미 분리돼 있음 확인(운영 직원 46명과 충돌 없음)
- 크로스플랫폼 대응 (로컬 Windows 동작은 그대로 유지, 검증 완료):
  - `frontend/e2e/backend-script.ts` 신규 — `E2E_PYTHON` 환경변수로 Python 실행 경로 오버라이드 가능(기본값은 기존과 동일하게 `.venv/Scripts/python.exe`)
  - `frontend/playwright.config.ts` — `E2E_BACKEND_COMMAND`로 백엔드 기동 명령 오버라이드 가능(기본값 `.\run-backend.cmd`)
  - `global-setup.ts`/`global-teardown.ts`는 `backend-script.ts` 헬퍼 재사용하도록 정리
  - **로컬에서 E2E 6개 재검증 통과함** (`npx playwright test --reporter=list`)

### 4단계: Render 배포 점검

- `curl https://ms-flowhub.onrender.com/health` → 200, `data_source: supabase`
- 프론트→백엔드 프록시(`https://ms-flowhub-frontend.onrender.com/api/v1/departments`) → 200
- CORS 헤더(`access-control-allow-origin`, `allow-credentials`) 정상
- Render 서비스는 손대지 않음(계획대로 무리한 변경 없음)

## 미완료 / 다음에 할 것

### 5단계: CI 실제 실행 결과 확인 — 바로 여기서 이어가면 됨

`5915d56` 커밋 push로 CI가 트리거됐는데, **저장소가 비공개라 Claude가 Actions 결과를 직접 못 봄**.
`gh` CLI가 있다면 아래로 확인:

```
gh run list --limit 5
gh run view <run-id> --log
```

실패하면 원인 분석 후 수정. 특히 확인할 것: Python 3.12에서 `pip install -e ".[dev]"`가 3.11 로컬과 동일하게 통과하는지(버전 차이로 인한 미묘한 차이 가능성).

### 5단계 이후: CI→Render 게이트 연결 여부 결정 (사용자 미확정)

현재는 CI 성공 여부와 무관하게 Render가 push마다 배포함. "CI 실패해도 배포되는 구조를 어떻게 개선할지 제안하라"는 요구사항이 있었는데 아직 제안·결정 안 함.
후보안: Render Auto-Deploy를 Off로 바꾸고 GitHub Actions에서 CI 통과 후 Render Deploy Hook을 호출하는 방식. **Render 설정 변경이라 사용자 승인 필요.**

### 6단계: 대시보드 지표 조사 — 데이터 부족 이슈, 사용자 판단 필요

실제 DB 조사 결과(2026-08-08 기준):
- 전자결재: **1건**뿐 (APPROVED, 인사팀)
- 채용 요청 1건, 공고 1건(DRAFT 고정), 지원자 3명(HIRED/OFFERED/REJECTED 각 1)
- 근태: 8/1~8/7 데이터만 있고 **오늘(당일) 근태는 0건** — 매일 `seed_organization` 재실행 필요한 구조로 보임
- 근태 변경 이력 11건

구현 가능하다고 확인한 지표(실제 컬럼 존재, 계산법까지 확인됨):
- 상태별/부서별 결재 건수, 평균 결재 처리 시간(`submitted_at`~`processed_at`)
- 지원자 전형 단계 분포, 공고별 지원자 수, 채용 요청 건수
- 오늘 근무 상태 분포, 부서별 근무 상태, 기간별 근태 변경 건수(단, 당일 근태 시딩 필요)

**구현 보류 권고**: "활성 채용공고 수"는 `job_postings.status`가 생성 시 `DRAFT` 고정이라 상태 전이 API가 없어 "활성" 구분 불가.

**사용자에게 확인 필요했던 것 (아직 미결정)**: 업무 데이터가 이렇게 적은 상태로 대시보드를 만들지(그래프가 막대 1개짜리가 됨), 아니면 데모 데이터를 더 채우고 진행할지. Mock 데이터 신규 생성은 금지 조건이므로, 채운다면 기존 seed 스크립트 확장 또는 실제 사용 시나리오로 데이터를 쌓는 방식이어야 함.

### 7~8단계: 대시보드 UI 기획/구현 — 미착수

### 10~11단계: Jira 목록, 문서 정리 — 미착수

## 검증 명령 모음

```powershell
# Backend
cd backend
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
.venv\Scripts\python.exe -m pytest -q

# Frontend
cd frontend
npm run lint
npm run typecheck
npm run build

# E2E (로컬 Windows, .env.e2e 필요)
cd frontend
npx playwright test --reporter=list
```

## 지켜야 할 제약 (AGENTS.md + 어제 프롬프트 공통)

- 오늘(8/7) 완료한 FAQ(18개)·매뉴얼(9개) UI/Seed 재작성 금지
- 기존 Supabase 데이터 삭제, Alembic 초기화 금지
- 운영 직원 46명을 E2E 데이터로 사용 금지
- Secret을 저장소에 기록 금지
- Render 서비스 임의 삭제 금지
- RAG, LLM API, 전자결재 AI, ATS AI 구현 금지
- 실행하지 않은 테스트를 성공했다고 보고 금지
