# 작업 인계 문서 — 생성형 AI 자동화 (2026-08-12)

> 이 문서만 읽고 이어서 작업할 수 있게 작성했습니다. 설계 근거는 [`AI_AUTOMATION_PLAN.md`](AI_AUTOMATION_PLAN.md)를 보세요.

## 한 줄 요약

**Prompt 0~4 완료.** 공통 AI 기반, 전자결재 AI 초안, 채용 정보 구체화와 OpenAI 채용 포스터 생성이 동작합니다. 2026-08-13 재점검 결과 **P0 0건 · P1 0건**으로 코드 Feature Freeze에 진입했고, 머지·배포만 자동 로그아웃 닫힘 기준 수동 확인 전까지 보류합니다.

## ⚠ 지금 바로 이어서 할 일

### 1) PR 머지 후 로컬 정리

```powershell
cd "C:\Users\user\Documents\MS FlowHub"
git switch master
git pull --ff-only
git branch -d feat/ai-approval-draft
```

### 2) 실제 Claude 호출 검증 — **완료 (2026-08-12)**

전자결재·채용공고 초안 모두 `claude-opus-5`로 실호출에 성공했습니다. `messages.parse()`에
`output_config`와 `output_format`을 함께 넘기는 조합도 코드 수정 없이 통과했습니다.

재확인이 필요하면 앱을 띄우지 않고 스크립트로 됩니다(DB에 쓰지 않고 일일 한도도 소모하지 않음).

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.try_ai_draft
.\.venv\Scripts\python.exe -m app.scripts.try_ai_draft --feature job-posting
```

**실측 비용**: 전자결재 약 19원, 채용공고 약 24원(건당). 설계 추정치의 약 1/5이며,
`effort: low`가 예상보다 간결하게 쓰는 것이 원인입니다. 충전한 $5로 약 300회 쓸 수 있습니다.

### 3) Prompt 5 판정 (Feature Freeze)

`FEATURE FREEZE READY: YES` — **P0 0건 · P1 0건**입니다. 지금부터 새 기능은 추가하지 않고 회귀 결함만 수정합니다. 다만 자동 로그아웃의 실제 시간 경과 수동 확인이 남아 있으므로 커밋·PR·머지·배포 승인은 보류합니다.

---

## 완료된 것

| 단계 | 내용 | 커밋 |
|---|---|---|
| Prompt -1 | 저장소 점검. 로컬이 2커밋 뒤처지고 Alembic이 깨져 있던 것 복구 | PR #4 |
| Prompt 0 | `docs/AI_AUTOMATION_PLAN.md` 24개 항목 설계 | PR #5 |
| Prompt 1 | Provider·Mock·Claude·Structured Output·`ai_generations`·일일 한도 | PR #5 |
| Prompt 2 | 전자결재 AI 초안 API + 화면 | 이 PR |
| Prompt 3 | 채용공고 AI 초안 + `PATCH /job-postings/{id}` 신설 | 이 PR |

**검증 상태**: ruff check/format 통과, pytest **155개** 통과, 프론트 lint/typecheck/build 통과.

**운영 DB**: migration `20260812_0022` 적용 완료. 코드 head = DB current = `20260812_0022`.

## 이 기능이 무엇인가

전자결재 작성 화면(`/approvals/new`)에서 [AI 초안 생성]을 누르면, **DB에 있는 사실**(작성자·직급·부서·팀)과 **사용자가 입력한 맥락**(요청 목적·주요 내용·금액 등)을 합쳐 AI가 제목과 본문을 씁니다.

```
DB = 사실  /  사용자 = 부족한 맥락  /  AI = 문장화
```

AI는 **어떤 상태도 바꾸지 않습니다.** 초안 생성으로 결재 문서가 생기지 않고, [전자결재에 적용]도 폼을 채울 뿐입니다. 저장은 사용자가 [임시 저장]/[결재 요청]을 눌러야 일어납니다.

## 반드시 유지해야 할 설계 결정

건드리면 안 되는 이유가 있는 것들입니다.

| 결정 | 이유 |
|---|---|
| **Context에 없는 값은 키 자체를 만들지 않는다** | `None`을 넣으면 AI가 "금액: 미정" 같은 문장을 쓸 여지가 생긴다. `ai_context.py`의 `_put()`이 이 규칙을 강제하고 테스트로 고정돼 있다 |
| **Context Builder는 순수 함수, 인자는 명시적** | `EmployeeDetail`에는 이메일·사번·**비공개 근태 사유**가 함께 있다. 객체를 통째로 넘기면 새 필드가 생길 때마다 조용히 AI로 흘러간다 |
| **구조화 결과 조립은 프론트에서** | `ApprovalDocument.content`는 Text 하나다. 백엔드가 미리 합치면 사용자가 `purpose`만 고치는 단위가 사라진다 |
| **Provider는 원시 문자열을 반환, 검증은 Service** | Provider가 검증까지 하면 Mock과 실제 Provider의 계약이 갈라진다 |
| **키 없이 `AI_PROVIDER=claude`면 오류** | 조용히 Mock으로 떨어뜨리면 "AI 붙인 줄 알았는데 샘플이었다"가 된다 |
| **전역 일일 한도가 실질 방어선** | 사용자당 한도만 두면 46명 × 5회 = 230회까지 열린다 |
| **Provider 실패는 200 + `success:false`** | 초안은 부가 기능이다. 5xx로 던지면 기존 작성 흐름까지 막힌다 |

## Prompt 3에서 무엇을 했는가 (완료)

### 채용공고는 사용자가 쓰는 문서가 아닙니다

결재 승인 시 [`process_approval`](../backend/app/services/recruitment_service.py)이 자동으로 `JobPosting`을 만들고, 본문은 `_build_posting_content()`가 **코드로 조립**합니다. 그리고 **공고 수정 API가 없습니다.**

→ **`PATCH /api/v1/job-postings/{id}`를 신설했습니다.** AI 전용 우회로가 아니라 원래 비어 있던 기능입니다.

제약: `title`·`content`만 받고 **`status`는 받지 않습니다.** AI가 공고를 게시 상태로 바꾸는 경로를 원천 차단합니다.

### AI가 "생성"하는 게 아니라 "윤문"합니다

`RecruitmentRequest`에 `responsibilities`, `required_skills`, `preferred_skills`가 **이미 Text로 존재**합니다. 담당자가 쓴 개조식 텍스트를 공고 문장으로 다듬는 것이지, 없는 걸 만드는 게 아닙니다.

DB에 없어 사용자 입력이 필요한 값: 근무 위치, 지원 마감일, 지원 방법, 팀 소개, 급여(선택).

### 재사용할 것

- `JobPostingDraftOutput` 스키마는 `schemas/ai.py`에 **이미 있습니다**
- `ai_prompts.py`의 `_JOB_POSTING_RULES`도 **이미 있습니다**
- `MockAIProvider._mock_job_posting_draft()`도 **이미 동작합니다**
- Prompt 3에서 할 일은 Context Builder + API + 화면 + `PATCH /job-postings/{id}`

### Migration

다음 번호는 **`20260812_0023`**, `down_revision = "20260812_0022"`. 다만 Prompt 3은 **migration이 필요 없을 가능성이 높습니다**(기존 칼럼만 사용).

## 비용 안전장치 — 인계 시 확인할 것

Anthropic API는 **선불 크레딧**이라 AWS식 요금 폭탄이 구조적으로 불가능합니다. 단 조건이 하나 있습니다.

```
□ Console: Auto-reload OFF      ← 이게 켜져 있으면 후불과 같아진다
□ Console: Spend limit
□ 코드: max_tokens 8000, timeout 15s, max_retries 2
□ 앱: 사용자당 5회 / 전역 30회 (최근 24시간, 환경변수 조정 가능)
```

실지출은 앱에서 바로 확인됩니다.

```sql
SELECT SUM(input_tokens)*5/1e6 + SUM(output_tokens)*25/1e6 AS usd
FROM ai_generations WHERE created_at >= now() - interval '30 days';
```

예상 사용량은 월 20~40회(개발은 Mock, 실호출은 검증·시연뿐) → 실측 기준 **월 500~1,000원**입니다.

## 파일 지도

| 경로 | 역할 |
|---|---|
| `app/domain/ai_provider.py` | `AIProvider` 프로토콜, `AIProviderResult`, `MockAIProvider` |
| `app/domain/claude_provider.py` | 실제 Claude Provider (`anthropic` SDK) |
| `app/domain/ai_prompts.py` | 시스템 프롬프트 (환각 방지 1차 방어선) |
| `app/domain/ai_context.py` | Context Builder (순수 함수, 개인정보 차단 지점) |
| `app/schemas/ai.py` | Structured Output + 요청·응답 스키마 |
| `app/services/ai_generation_service.py` | 한도 → 호출 → 검증 → 기록 |
| `app/repositories/ai_generation_repository.py` | 기록, 최근 24시간 카운트 |
| `app/models/ai_generation.py` | `ai_generations` |
| `app/api/ai.py` | AI 라우터 |
| `app/scripts/try_ai_draft.py` | 실호출 수동 확인 도구(앱·DB 없이 Provider만 호출) |
| `frontend/src/features/ai/` | API 모듈, 초안 패널 |

## 알아둘 상태

- `docs/JIRA_UPDATE_2026-08-08.md`가 **미커밋으로 남아 있습니다.** 표 구분선 자동정렬만 바뀐 것이고 내용 변경은 0입니다. AI 작업과 무관해 계속 제외했습니다.
- 모델 기본값은 `claude-opus-5`. `AI_MODEL` 환경변수로 교체 가능합니다. 더 싼 후보(GPT-5.6 Terra/Luna)는 언어·지시 벤치마크 데이터가 없어 한국어 품질이 미검증이라 선택하지 않았습니다.
- **Playwright E2E는 추가하지 않기로 했습니다.** 프론트에 단위 테스트 프레임워크가 없고, E2E는 실제 Supabase에 접속합니다.

## 남은 로드맵

```
Prompt 5   Feature Freeze 판정 (P0/P1이 0개일 때만 YES)
──────── Feature Freeze ────────
Prompt 4   포스터 자동 생성 (SVG 템플릿 + 프론트 Canvas→PNG)
```

포스터를 Freeze 밖으로 뺀 이유: SVG 템플릿 3종 + 한글 줄바꿈 + PNG 변환이 Prompt 2·3을 합친 것보다 크고, 포스터 하나 때문에 Freeze 전체가 밀립니다. 설계는 `AI_AUTOMATION_PLAN.md` §16·§17에 남겨 뒀습니다.

## 검증 명령

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest -q          # 155 passed
.\.venv\Scripts\python.exe -m alembic current    # 20260812_0022 (head)

cd ..\frontend
npm run lint; npm run typecheck; npm run build
```

---

## 이어서 할 일 (2026-08-12 오후 중단 지점)

### 0) 완료 — PR #7 머지

Prompt 5 수동 검수에서 찾은 결함 6건과 개선 3건은 `d0dadd8`로 커밋해 PR #7로 머지했습니다.
현재 `master`는 `2197fa3`이고 origin과 같습니다.

### 1) 기능 1 — 세션 자동 로그아웃 (보안) — **2026-08-13 완료**

**원인**: `supabase-browser.ts`가 옵션 없이 `createClient()`를 호출해 `persistSession: true`가 적용됩니다. 세션이 localStorage에 남고 토큰이 자동 갱신돼 다음날도 로그인 상태입니다.

**착수 후 방식이 바뀌었습니다.** 원래 계획은 "무동작 30분"(창이 열려 있어도 조작이 없으면 로그아웃)이었으나,
요구사항은 **"창을 닫고 30분"** 이었습니다. 둘은 다른 기능입니다. 창을 열어두고 회의 자료를 보는 중에
끊기면 안 되기 때문입니다. 그래서 활동 감지가 아니라 **생존 신호** 방식으로 다시 만들었습니다.

- 화면이 열려 있는 동안 30초마다 `localStorage.msflowhub.lastSeenAt` 갱신 (조작 여부와 무관)
- 창을 닫으면 신호가 끊기므로, **그 공백이 곧 닫혀 있던 시간**
- 마운트 · 탭 복귀(`visibilitychange`) · 30초 타이머에서 공백 확인 → 기준 초과 시 `signOut()`
- 탭을 여러 개 켜두면 남은 탭이 계속 신호를 남기므로, 한 탭만 닫아도 끊기지 않음
- 로그인 화면에 "장시간 접속하지 않아 자동 로그아웃되었습니다" 안내 (`/login?reason=timeout`)
- `NEXT_PUBLIC_SESSION_TIMEOUT_MINUTES` **기본 30분**

**계획 대비 걷어낸 것**: 만료 1분 전 경고 모달, 연장 버튼, 활동 감지(클릭·키·스크롤),
`storage` 이벤트 동기화. 매번 localStorage에서 다시 읽으므로 탭 간 동기화는 저절로 됩니다.

**범위**: 프론트 신규 1파일(`features/auth/session-timeout.ts`) + 세션 가드·로그인 화면·포털 셸 소폭 수정.
백엔드 변경 없음.

**남은 한계**: 브라우저가 백그라운드 탭 타이머를 늦추거나 멈추면, 탭을 열어둔 채 오래 방치했다가
돌아왔을 때도 로그아웃될 수 있습니다. 보안 관점에서는 맞는 동작이라 그대로 뒀습니다.

### 2) 기능 2 — 채용공고 작성 구체화 — **2026-08-13 구현·수동 검증 완료**

#### 확정된 선택지 (2026-08-13 사용자 확정)

| 항목 | 선택지 |
|---|---|
| 고용 형태 | 정규직 / 계약직 / 인턴 / 파트타임 / 프리랜서 |
| 학력 *(신규)* | 학력무관 / 고졸 이상 / 초대졸 이상 / 대졸 이상 / 석사 이상 |
| 지원 방법 *(신규)* | 이메일 / 잡코리아 / 사람인 / 고용24 |

**경력은 설계가 바뀌었습니다.** 원안은 `신입 / 경력무관 / 1년↑ / 3년↑ / 5년↑ / 10년↑`
단일 드롭다운이었으나, 사용자 요청으로 잡코리아식 2단 구조가 됐습니다.

```
○ 신입        →  년수 없음
● 경력        →  [ 3년 이상 ▾ ]   ← 경력을 골랐을 때만 나타남 (1~20년)
○ 경력무관    →  년수 없음
```

라디오(하나만 선택)입니다. 신입+경력 동시 선택은 곧 경력무관이라 선택지가 겹칩니다.

#### 완료된 백엔드 (미커밋)

**migration `20260813_0023`** — `recruitment_requests`에 칼럼 6개, 전부 nullable.

```
experience_years_min  integer       education_level  varchar(50)
work_location         varchar(200)  salary           varchar(200)
application_deadline  date          apply_method     varchar(50)
```

- `app/domain/recruitment_options.py` *(신규)* — 선택지를 `Literal` 단일 출처로 두고
  튜플을 `get_args`로 파생. 목록과 검증 타입이 따로 놀면 한쪽만 고쳐도 안 걸립니다.
  `describe_experience()`가 코드값을 `"경력 3년 이상"`으로 조립합니다.
- `RecruitmentRequestCreate` — 4개 항목을 `Literal`로 제한. 경력을 고르면 년수 필수,
  신입/경력무관이면 남은 년수를 서버가 잘라냅니다.
- 응답에 `experience_label` 추가 — 코드값 해석을 클라이언트로 넘기지 않습니다.
- `_build_posting_content` — 값이 없으면 **줄 자체를 넣지 않습니다.**
- **AI Context가 DB를 우선 씁니다.** 근무지·급여·마감일·지원방법은 `RecruitmentRequest`
  값이 이기고, 사용자 입력(`JobPostingDraftRequest`)은 이 칼럼들이 없던 시절의 요청에만
  쓰입니다. 결재자가 승인한 근무지를 AI 패널에서 조용히 갈아끼울 수 없습니다.

**기존 자유 입력 데이터**: `"Junior"`, `"신입/경력"`은 코드값이 아니라 매핑이 안 됩니다.
`describe_experience()`가 **모르는 값은 버리지 않고 원문 그대로** 돌려줍니다. 기존 화면이
빈칸이 되지 않고 신규 입력만 막힙니다. 테스트로 고정했습니다.

검증: ruff 통과 · pytest **179 passed**(기존 162 + 신규 17).
기존 테스트 27개가 `"Junior"` 같은 픽스처 값으로 실패해 코드값으로 고쳤습니다.

#### 완료된 프론트엔드 (미커밋)

- `features/recruitment/recruitment-options.ts` *(신규)* — 선택지 목록. 백엔드
  `recruitment_options.py`와 값을 맞춥니다. **두 곳에 같은 목록이 있으므로 한쪽만 고치면
  런타임 422가 납니다.**
- 작성 폼 — 고용 형태·학력·지원 방법은 `<select>`, 경력은 라디오 3개 + '경력'일 때만
  최소 년수 `<select>`(1~20년)가 나타납니다. 근무지·급여·마감일 입력칸을 추가했습니다.
- 요청 상세·공고 목록 — `experience_label`을 쓰고 새 필드는 값이 있을 때만 표시합니다.
- AI 패널 — 입력칸 **5개 → 팀 소개 1개**. 나머지는 결재 승인된 채용 요청에서 가져옵니다.
- `globals.css`에 `.experience-field` 계열 스타일 추가.

검증: 프론트 lint·typecheck·build 통과 · 백엔드 pytest 179 passed · ruff 통과.

#### 완료 확인

1. **migration을 운영 Supabase에 적용 완료**
   ```powershell
   cd backend
   .\.venv\Scripts\alembic.exe upgrade head   # 20260813_0023
   ```
   `20260812_0022 → 20260813_0023` 적용 후 `alembic current`에서 head를 확인했습니다.
2. 화면에서 채용 요청 작성 → 결재 승인 → 공고 생성 → 실제 Claude 초안 생성·적용까지 확인했습니다.
   근무지·급여·마감일·지원 방법이 전달됐고, 마감일은 같은 날짜를 한국어 표기로 다듬었습니다.
   생성한 업무 테스트 데이터는 삭제했습니다.
3. UPDATELOG에 기능 2 항목을 기록했습니다.

**남은 것**: 자동 로그아웃 닫힘 기준 수동 확인, 커밋 → PR → 머지.

### 3) Prompt 5 재판정 → Feature Freeze

2026-08-13 전체 재검증 결과는 아래와 같습니다.

| 항목 | 결과 |
|---|---|
| P0 | 0건 |
| P1 | 0건 |
| 코드 Feature Freeze | **READY: YES** |
| 머지·배포 | **HOLD** — 자동 로그아웃 닫힘 기준 수동 확인 후 해제 |

- 운영 DB는 Alembic `20260813_0023 (head)`입니다.
- Backend는 Ruff check·format check와 pytest **201 passed**, Frontend는 lint·typecheck·production build를 통과했습니다.
- E2E 최고관리자 로그인, 대시보드 조회, 포스터 API의 최고관리자 허용·일반 직원 차단을 실제 API로 확인했습니다. 이 점검에서는 유료 이미지 생성을 호출하지 않았습니다.
- 현재 실행 환경에는 자동 브라우저 대상이 없어 이번 회차의 화면 회귀 검증은 실행하지 못했습니다. 앞선 사용자 수동 확인 결과를 유지하되, 정확한 자동 로그아웃 시간 경과 시나리오는 아래 절차로 최종 확인해야 합니다.

```text
NEXT_PUBLIC_SESSION_TIMEOUT_MINUTES=2로 프론트 재시작
1) 로그인 → 모든 탭을 완전히 닫음 → 3분 뒤 재접속: 로그아웃이어야 함
2) 로그인 → 탭을 열어 둔 채 3분 이상 대기: 로그인 유지여야 함
```

이 수동 항목이 통과하면 `MERGE / RELEASE GATE: GO`로 바꾸고 커밋·PR·머지를 진행합니다. 실패하면 새 기능을 추가하지 않고 해당 결함만 수정한 뒤 P0/P1을 다시 판정합니다.

---

## 현재 미커밋 상태 (2026-08-13)

```
기능 1  frontend/src/features/auth/session-timeout.ts  (신규)
        auth-session-guard · login-form · portal-shell · supabase-browser · login/page
        frontend/.env.example
기능 2  backend/app/domain/recruitment_options.py      (신규)
        backend/tests/test_recruitment_options.py      (신규)
        migrations/versions/20260813_0023_*.py         (신규, 운영 적용 완료)
        models/schemas/repositories/services · 테스트 픽스처 4개
문서    README.md · UPDATELOG.md · 이 문서
```

`frontend/next-env.d.ts`는 dev/build가 번갈아 바꾸는 생성 파일이라 커밋에서 빼면 됩니다.
`docs/JIRA_UPDATE_2026-08-08.md`는 표 자동정렬만 된 상태로 계속 보류 중입니다.
