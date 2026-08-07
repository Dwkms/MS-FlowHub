# CI 구성 및 E2E 시나리오 확장 기획

> 상태: 착수 전 기획 문서입니다. 2026-08-07 작업 대상인 `MFH-28`(CI/CD 기본 구성)과 `MFH-25`(Playwright E2E 확장)의 범위와 순서를 정리합니다. 작업이 끝나면 결과를 `UPDATELOG.md`에 기록하고 이 문서는 `docs/archive`로 옮깁니다.

## 1. 작업 순서와 이유

`MFH-28`(CI) → `MFH-25`(E2E) 순서로 진행합니다. CI 파이프라인을 먼저 만들어두면, 이후 추가하는 E2E 시나리오를 어떤 형태로 자동화에 편입할지 기준이 정해진 상태에서 작성할 수 있습니다.

## 2. 사전 조사 결과 (중요)

작업 범위를 정하기 전에 현재 구성을 확인한 결과, **E2E 테스트는 지금 상태로는 GitHub Actions에서 실행할 수 없습니다.**

| 위치 | 내용 | 문제 |
|---|---|---|
| `frontend/playwright.config.ts` | `webServer` 명령이 `.\run-backend.cmd` | Windows 배치 파일이라 Ubuntu 러너에서 실행 불가 |
| `frontend/e2e/global-setup.ts` | `.venv/Scripts/python.exe` 경로 하드코딩 | Linux venv는 `.venv/bin/python`이라 경로 불일치 |
| `frontend/e2e/global-setup.ts` | 실행 시 실제 Supabase에 Auth 계정 생성·삭제 | CI에서 매 push마다 운영 Supabase를 건드리게 됨 |

반면 **Backend pytest는 CI에서 바로 실행 가능합니다.** `tests/conftest.py`가 인메모리 SQLite와 가짜 Storage fixture를 쓰기 때문에 Supabase 접속 정보가 전혀 필요 없습니다.

이 조사 결과에 따라 아래와 같이 범위를 나눕니다.

## 3. MFH-28 — GitHub Actions CI 구성

### 목표

`master` 브랜치 push와 Pull Request마다 코드 품질 검사를 자동 실행해, 배포된 서비스가 깨지는 변경을 사전에 잡습니다.

### 실행 대상 (1차 범위)

| Job | 명령 | 비밀값 필요 |
|---|---|---|
| backend | `ruff check .` | 없음 |
| backend | `ruff format --check .` | 없음 |
| backend | `pytest` | 없음 (SQLite + 가짜 Storage) |
| frontend | `npm run lint` | 없음 |
| frontend | `npm run typecheck` | 없음 |
| frontend | `npm run build` | 확인 필요 (아래 참고) |

### 워크플로우 설계

- 파일: `.github/workflows/ci.yml`
- 트리거: `push`(master), `pull_request`
- Job 2개를 병렬 실행 (backend / frontend)
- backend: `actions/setup-python@v5`, Python 3.12, `pip install -e ".[dev]"`
- frontend: `actions/setup-node@v4`, Node 20, `npm ci`
- 의존성 캐시(pip, npm)를 적용해 실행 시간을 줄임

### 작업 중 확인할 것

- **`npm run build`에 Supabase 환경변수가 필요한지 확인.** `src/lib/supabase-browser.ts`는 함수 내부에서 환경변수를 검사하므로 빌드는 통과할 가능성이 높지만, `NEXT_PUBLIC_*` 값은 빌드 시점에 번들에 포함되는 성질이 있어 실제로 돌려봐야 확실합니다. 필요하면 CI 전용 더미값을 workflow의 `env`로 주입합니다(실제 키를 CI에 넣지 않습니다).

### 이번 범위에서 제외

- **E2E 자동 실행은 제외합니다.** 위 2절의 제약(Windows 경로, 운영 Supabase 접근) 때문에 별도 대응이 필요하고, 매 push마다 실제 Auth 계정을 만들고 지우는 것은 위험합니다.
- 배포 자동화(CD)도 제외합니다. Render가 이미 `master` push마다 자동 배포(Auto-Deploy: On Commit)하고 있어 중복입니다.

## 4. MFH-25 — Playwright E2E 시나리오 확장

### 현재 상태

`e2e/auth-rbac.spec.ts`에 6개 시나리오(로그인 실패, 로그인·세션 유지·로그아웃, 권한 범위, 직원 필터, 전자결재 승인, 비밀번호 변경)가 있고 전부 통과합니다. 최근 추가한 **ATS 지원자 관리와 Supabase Storage 포스터 업로드는 Backend pytest와 수동 검증만 있고 E2E 공백**입니다.

### 추가할 시나리오

**시나리오 A — ATS 지원자 관리** (`e2e/ats-applicant.spec.ts`)

1. `SUPER_ADMIN` 계정으로 로그인
2. `/applicants` 이동, 채용공고 선택
3. 지원자 등록(이름·이메일·경력 요약)
4. 목록에 등록한 지원자가 보이는지 확인
5. 전형 단계 변경(지원 접수 → 서류 검토), 이력에 기록되는지 확인
6. 같은 공고에 같은 이메일로 재등록 시 차단되는지 확인
7. 테스트 종료 시 등록한 지원자 삭제

**시나리오 B — 채용 포스터 Storage 업로드** (`e2e/recruitment-poster.spec.ts`)

1. `SUPER_ADMIN` 계정으로 로그인
2. 채용 요청 작성 + 포스터 이미지 첨부
3. 상세 화면에서 포스터 미리보기·다운로드가 동작하는지 확인
4. 테스트 종료 시 채용 요청 삭제(연결된 Storage 파일도 함께 삭제됨)

### 데이터 정리 전략

두 시나리오 모두 **실제 Supabase에 데이터를 만듭니다.** 기존 `global-teardown.ts`는 E2E 전용 Auth 계정만 정리하므로, 테스트가 만든 업무 데이터는 각 spec 내부에서 정리해야 합니다.

- 지원자: 테스트 마지막 단계에서 화면의 삭제 기능으로 제거
- 채용 요청: 관리자 삭제 시 연결된 채용공고·알림·Storage 포스터가 함께 정리되는 것이 이미 구현되어 있어 그대로 활용
- 식별용 이름·이메일에 타임스탬프를 붙여 기존 데이터와 충돌하지 않게 함

### 선택 작업 (시간이 남으면)

`playwright.config.ts`의 `.\run-backend.cmd`와 `global-setup.ts`의 `.venv/Scripts/python.exe`를 OS에 따라 분기하도록 정리하면, 나중에 E2E를 CI에 편입할 수 있는 기반이 됩니다. 이번 범위의 필수 항목은 아닙니다.

## 5. 예상 소요

| 작업 | 예상 |
|---|---|
| MFH-28 CI 구성 | 2~3시간 |
| MFH-25 E2E 시나리오 2개 | 2~3시간 |

## 6. 다음 순번

- 다일 휴가 및 휴가 승인 흐름 — 이번 주에는 착수하지 않습니다. 2026-08-08부터 AX 자동화 분석·기획을 시작할 예정이라, 그 이후 순번으로 미룹니다.
