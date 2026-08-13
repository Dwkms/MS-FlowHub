# 작업 인계 문서 — 생성형 AI 자동화 (2026-08-12)

> 이 문서만 읽고 이어서 작업할 수 있게 작성했습니다. 설계 근거는 [`AI_AUTOMATION_PLAN.md`](AI_AUTOMATION_PLAN.md)를 보세요.
> 마지막 갱신: 2026-08-13 · 기능·운영 검증 기준 커밋 `b84b8fb`

## 한 줄 요약

**Prompt 0~4 완료.** 공통 AI 기반, 전자결재 AI 초안, 채용 정보 구체화와 OpenAI 채용 포스터 생성이 동작합니다. 2026-08-13 재점검 결과 **P0 0건 · P1 0건**이며 자동 로그아웃 실제 시간 검증까지 통과해 Feature Freeze와 머지·배포 게이트가 모두 `GO`입니다.

## ⚠ 지금 바로 이어서 할 일

### 1) Render 배포 게이트 방식 결정

아직 Render 설정은 바꾸지 않았습니다. Backend와 Frontend 모두 `master` push 즉시 배포되는
`Auto-Deploy: On Commit` 상태입니다. 권장안은 두 서비스의 Render Dashboard 설정을
`Auto-Deploy: After CI Checks Pass`로 바꾸는 것입니다.

- 목적: GitHub Actions의 Backend·Frontend CI가 모두 성공한 커밋만 운영 배포
- 코드·DB·환경변수·서비스 URL 변경 없음
- Deploy Hook이나 GitHub Secret 추가 불필요
- 부작용: CI 시간만큼 배포가 늦어지고, 한쪽 CI 실패가 Backend·Frontend 배포를 모두 막음
- 주의: Alembic migration은 이 설정으로 자동화되지 않으므로 DB 변경 시 계속 먼저 수동 적용

사용자 결정 전에는 Render 설정을 임의로 변경하지 않습니다.

#### 이 게이트가 보증하는 범위

통과 기준은 [`ci.yml`](../.github/workflows/ci.yml)의 두 잡뿐입니다 — Backend는 Ruff check·format·pytest,
Frontend는 lint·typecheck·`next build`. `push: [master]`에 path 필터가 없어 모든 master 커밋에서
실행되므로, "체크가 올라오지 않아 배포가 영구 대기"하는 상태는 생기지 않습니다.

[`e2e.yml`](../.github/workflows/e2e.yml)은 `workflow_dispatch` 전용이라 **게이트에 포함되지 않습니다.**
따라서 이 게이트는 "명백한 파손이 배포되지 않는다"까지만 보증하고, 실제 Supabase에 붙는 동작은
보증하지 않습니다. 완전한 배포 보호가 아니라 1차 안전장치입니다.

#### 실패 모드가 바뀝니다

전환 후 위험은 "잘못된 코드가 배포됨"에서 **"배포가 조용히 일어나지 않음"** 으로 이동합니다.
알아둘 두 가지입니다.

- **push는 한 번만.** `ci.yml`의 `concurrency`가 `cancel-in-progress: true`이므로 master에 연달아
  push하면 앞 커밋 CI가 **취소**되고, 취소는 성공이 아니라서 그 커밋은 배포되지 않습니다. 최신
  커밋만 배포되니 결과는 맞지만, 검증 중에 이걸 모르면 게이트 고장으로 오판합니다.
- **정상과 지연을 구분하는 기준**: CI 약 3~5분 → 커밋의 checks 전부 성공 → Render 배포가 1~2분 내
  시작. checks가 전부 성공인데 **10분을 넘겨 배포가 없으면** 그때가 이상 신호입니다. GitHub 커밋의
  checks와 Render Events 탭을 함께 봅니다.

#### `[skip render]` 마커와의 관계

커밋 메시지에 `[skip render]`를 넣으면 **게이트와 무관하게 그 커밋의 배포가 건너뛰어집니다.**
`e389eec`("docs: refresh feature freeze handoff [skip render]")에서 실제로 쓴 마커이고, 저장소
문서에는 아직 기록이 없었습니다.

게이트 전환과 상충하지 않습니다. 목적이 다릅니다.

| 수단 | 성격 | 의미 |
|---|---|---|
| `After CI Checks Pass` | 상시 게이트 | 검증되지 않은 커밋은 배포하지 않는다 |
| `[skip render]` | 커밋별 선택 | 이 커밋은 배포할 필요가 없다 (문서 변경 등) |

**단, 게이트 검증용 커밋에는 절대 붙이면 안 됩니다.** 붙이면 배포가 시작되지 않는데, 그것이
게이트 차단인지 마커 때문인지 구분할 수 없어 검증 자체가 무의미해집니다.

#### 이상 시 복구 순서

`On Commit` 복구는 1차 조치가 **아닙니다.**

1. Render **Manual Deploy** — 게이트를 유지한 채 해당 커밋만 내보내 배포를 정상화
2. 원인 확인 (CI 실패인지, 체크 미보고인지, Render 쪽 대기인지)
3. 재현되면 그때 두 서비스를 `On Commit`으로 복구

`On Commit`으로 되돌려도 **이미 push된 커밋이 소급 배포되지는 않습니다.** 어느 경로든 Manual
Deploy가 필요하므로, 일시적 문제 때문에 보호장치를 먼저 버릴 이유가 없습니다.

#### 검증하지 않고 남기는 것

프리즈 중 master에 의도적으로 깨진 커밋을 올리지 않기로 했으므로, **"CI 실패 → 배포 차단"은
실증하지 않습니다.** 아래 체크리스트로 확인되는 것은 정상 경로(CI 성공 → 배포)뿐이고, 차단
동작은 Render의 문서화된 동작을 **신뢰하는** 것입니다. 실증이 필요하면 프리즈 이후 폐기용
브랜치·서비스에서 합니다.

### 2) Feature Freeze 유지

현재 판정은 `P0 0건 · P1 0건`, `FEATURE FREEZE READY: YES`,
`MERGE / RELEASE GATE: GO`입니다. 신규 기능은 추가하지 않고 회귀 결함만 수정합니다.

### 3) 실제 Claude 호출 검증 — **완료 (2026-08-12)**

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

### 4) Prompt 5 판정 (Feature Freeze)

`FEATURE FREEZE READY: YES` — **P0 0건 · P1 0건**입니다. 자동 로그아웃의 실제 시간 경과 수동 확인까지 통과했습니다. 지금부터 새 기능은 추가하지 않고 회귀 결함만 수정합니다.

---

## 완료된 것

| 단계 | 내용 | 커밋 |
|---|---|---|
| Prompt -1 | 저장소 점검. 로컬이 2커밋 뒤처지고 Alembic이 깨져 있던 것 복구 | PR #4 |
| Prompt 0 | `docs/AI_AUTOMATION_PLAN.md` 24개 항목 설계 | PR #5 |
| Prompt 1 | Provider·Mock·Claude·Structured Output·`ai_generations`·일일 한도 | PR #5 |
| Prompt 2 | 전자결재 AI 초안 API + 화면 | PR #7 이전 완료 |
| Prompt 3 | 채용 요청·공고 정보 구체화와 AI Context 연동 | `32523cb` |
| Prompt 4 | OpenAI 채용 포스터 2안 생성·비교·선택·확대·PNG 다운로드 | `32523cb` |
| Prompt 5 | 전체 회귀 점검과 Feature Freeze 판정 | `24c9c84`, `b84b8fb` |

**검증 상태**: Ruff check·format 통과, pytest **201 passed**, Frontend lint·typecheck·production build 통과. GitHub Actions CI 성공.

**운영 DB**: migration `20260813_0023` 적용 완료. 코드 head = DB current = `20260813_0023`.

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

후속 채용 정보 구체화에서 **`20260813_0023`**, `down_revision = "20260812_0022"` migration을 추가했고 운영 DB까지 적용했습니다. `recruitment_requests`의 신규 6개 칼럼은 모두 nullable이라 기존 데이터와 호환됩니다.

## 비용 안전장치 — 인계 시 확인할 것

Anthropic 텍스트 생성과 OpenAI 이미지 생성은 모두 호출 비용이 발생하므로 Console 한도와 애플리케이션 한도를 함께 유지합니다.

```
□ Console: Auto-reload OFF      ← 이게 켜져 있으면 후불과 같아진다
□ Console: Spend limit
□ 코드: max_tokens 8000, timeout 15s, max_retries 2
□ 앱: 사용자당 5회 / 전역 30회 (최근 24시간, 환경변수 조정 가능)
□ 이미지: 일반 사용자당 2회 / 전역 5회 (최근 24시간, SUPER_ADMIN은 횟수 제한 제외)
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
| `app/domain/openai_image_provider.py` | 실제 OpenAI 이미지 Provider (`gpt-image-2`) |
| `app/domain/job_poster_prompt.py` | 승인된 채용 정보 기반 포스터 프롬프트 조립 |
| `app/domain/ai_prompts.py` | 시스템 프롬프트 (환각 방지 1차 방어선) |
| `app/domain/ai_context.py` | Context Builder (순수 함수, 개인정보 차단 지점) |
| `app/schemas/ai.py` | Structured Output + 요청·응답 스키마 |
| `app/services/ai_generation_service.py` | 한도 → 호출 → 검증 → 기록 |
| `app/repositories/ai_generation_repository.py` | 기록, 최근 24시간 카운트 |
| `app/models/ai_generation.py` | `ai_generations` |
| `app/api/ai.py` | AI 라우터 |
| `app/scripts/try_ai_draft.py` | 실호출 수동 확인 도구(앱·DB 없이 Provider만 호출) |
| `frontend/src/features/ai/` | 공통 API 모듈, 전자결재 초안·채용 포스터 패널 |

## 알아둘 상태

- `docs/JIRA_UPDATE_2026-08-08.md`가 **미커밋으로 남아 있습니다.** 표 구분선 자동정렬만 바뀐 것이고 내용 변경은 0입니다. AI 작업과 무관해 계속 제외했습니다. **이 파일은 더미 파일로 삭제할 예정이므로 커밋하지 않습니다**(2026-08-13 사용자 확정). 배포 게이트 검증용 커밋으로도 쓰지 않습니다.
- 모델 기본값은 `claude-opus-5`. `AI_MODEL` 환경변수로 교체 가능합니다. 더 싼 후보(GPT-5.6 Terra/Luna)는 언어·지시 벤치마크 데이터가 없어 한국어 품질이 미검증이라 선택하지 않았습니다.
- **Playwright E2E는 추가하지 않기로 했습니다.** 프론트에 단위 테스트 프레임워크가 없고, E2E는 실제 Supabase에 접속합니다.

## 남은 로드맵

```
Prompt 0~4   구현 완료
Prompt 5     Feature Freeze 판정 완료 (P0 0건 · P1 0건)
다음 결정    Render Auto-Deploy: On Commit → After CI Checks Pass  (1차 안전장치)
프리즈 이후  GitHub branch protection: master 직접 push 금지 + PR 필수 CI  (상위 보호)
```

초기 SVG 템플릿 계획 대신 OpenAI `gpt-image-2`로 포스터 2안을 만들고 사용자가 비교·선택·확대·다운로드하는 방식으로 구현했습니다. 생성 결과는 현재 페이지 메모리에만 유지되며 공고 첨부에는 자동 반영하지 않습니다.

## 검증 명령

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest -q          # 201 passed
.\.venv\Scripts\python.exe -m alembic current    # 20260813_0023 (head)

cd ..\frontend
npm run lint; npm run typecheck; npm run build
```

---

## 2026-08-13 작업 상세 기록

### 0) 완료 — PR #7 머지

Prompt 5 수동 검수에서 찾은 결함 6건과 개선 3건은 `d0dadd8`로 커밋해 PR #7로 머지했습니다.
당시 `master`는 `2197fa3`이었으며, 이후 2026-08-13 기능과 프리즈 검증은 `32523cb`~`b84b8fb`에 반영했습니다.

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

#### 완료된 백엔드

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

#### 완료된 프론트엔드

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

**원격 확인 완료**: 기능 백업 `32523cb`, 프리즈 확정 `24c9c84`, 운영 검증 기록 `b84b8fb`를 `origin/master`에 푸시했습니다. 최신 `b84b8fb`의 GitHub Actions CI도 성공했습니다.

### 3) Prompt 5 재판정 → Feature Freeze

2026-08-13 전체 재검증 결과는 아래와 같습니다.

| 항목 | 결과 |
|---|---|
| P0 | 0건 |
| P1 | 0건 |
| 코드 Feature Freeze | **READY: YES** |
| 머지·배포 | **GO** — 자동 로그아웃 닫힘·열림 기준 수동 확인 통과 |

- 운영 DB는 Alembic `20260813_0023 (head)`입니다.
- Backend는 Ruff check·format check와 pytest **201 passed**, Frontend는 lint·typecheck·production build를 통과했습니다.
- E2E 최고관리자 로그인, 대시보드 조회, 포스터 API의 최고관리자 허용·일반 직원 차단을 실제 API로 확인했습니다. 이 점검에서는 유료 이미지 생성을 호출하지 않았습니다.
- GitHub Actions CI 성공 후 Render 운영 Backend health·Frontend 로그인·Frontend API 프록시가 모두 200을 반환했고 CORS도 정상입니다. 운영 E2E 최고관리자 대시보드·공고 조회, 없는 공고 포스터 요청 404와 일반 직원 403을 확인했으며 유료 이미지 호출은 0회입니다.
- 현재 실행 환경에는 자동 브라우저 대상이 없어 자동 화면 회귀는 실행하지 못했습니다. 대신 아래 자동 로그아웃 시나리오를 사용자가 실제 Chrome에서 확인해 모두 통과했습니다.

```text
NEXT_PUBLIC_SESSION_TIMEOUT_MINUTES=2로 프론트 재시작
1) 로그인 → 모든 탭을 완전히 닫음 → 3분 뒤 재접속: 로그아웃이어야 함
2) 로그인 → 탭을 열어 둔 채 3분 이상 대기: 로그인 유지여야 함
```

검증 결과 모든 탭을 닫고 3분 뒤 재접속했을 때 로그인 화면으로 이동했고, 탭을 열어 둔 채 3분 이상 대기했을 때는 로그인 상태가 유지됐습니다. `MERGE / RELEASE GATE: GO`입니다.

---

## 현재 Git 상태 (2026-08-13)

```
branch          master
코드 검증 기준   b84b8fb        (이후 커밋은 모두 문서 변경만)
원격 상태        origin/master = e389eec  [skip render]로 배포 건너뜀
미푸시           1건 — 이 문서의 배포 게이트 절차 추가
                 Render 설정 전환 후 게이트 검증용으로 push할 커밋
기능 변경        모두 커밋·푸시 완료
```

작업 폴더에는 의도적으로 제외한 아래 두 변경만 남아 있습니다.

- `frontend/next-env.d.ts` — dev/build가 번갈아 바꾸는 생성 파일이므로 커밋 제외
- `docs/JIRA_UPDATE_2026-08-08.md` — 표 자동정렬만 바뀐 보류 문서이고 **더미 파일로 삭제 예정**이므로 커밋 제외

실제 `.env`와 OpenAI API Key는 커밋되지 않았습니다. E2E 전용 계정 두 개만 생성했으며 기존 관리자 계정은 변경하지 않았습니다.

## 다음 작업 체크리스트

Render 배포 게이트 전환 절차입니다. 배경과 판단 근거는 위 "1) Render 배포 게이트 방식 결정"을 보세요.

1. 전환 전 **현재 Render 설정값을 캡처하거나 기록** (Backend·Frontend 각각. 복구 기준점)
2. Backend Auto-Deploy를 `After CI Checks Pass`로 변경
3. Frontend도 동일하게 변경 — **두 서비스를 모두 바꾼 뒤에** 4번으로 갑니다. 한쪽만 바꾸고
   push하면 검증이 성립하지 않고, 스키마·API 불일치가 오히려 더 잘 생깁니다
4. 안전한 커밋을 **한 번만** push. migration도 코드 변경도 없는 것으로 고르고, 커밋 메시지에
   **`[skip render]`를 넣지 않습니다** (붙이면 배포가 건너뛰어져 검증이 성립하지 않음)
5. GitHub Actions CI가 **먼저** 성공하는지 확인
6. 그 **후에야** Backend·Frontend 배포가 시작되는지 확인 (green 후 1~2분 내 시작, 10분 초과 시 이상)
7. 배포 후 Backend `/health`, Frontend `/login`, Frontend API 프록시, CORS 재확인
8. 이상 시 Manual Deploy → 원인 확인 → 재현되면 `On Commit` 복구 (위 "이상 시 복구 순서")
9. DB migration이 추가되는 후속 작업에서는 배포 전에 운영 DB에 `alembic upgrade head` 적용
10. 프리즈 중 발견되는 P0/P1만 수정하고 P2/P3 개선 요청은 Jira 백로그로 이동

## 프리즈 이후 (지금 하지 않음)

- **master 직접 push 금지 + PR 필수 CI (GitHub branch protection)** — Render 게이트는 하류 방어이고,
  잘못된 커밋이 애초에 master에 들어오지 않게 막는 상위 보호 장치입니다. 커밋 이력상 PR 머지(#3~#7)를
  쓰고 있으므로 남은 구멍은 직접 push 경로입니다.
  **프리즈 중에는 켜지 않습니다.** P0 핫픽스도 PR을 거쳐야 해 대응이 느려지고, 그 트레이드오프는
  프리즈가 풀린 뒤 판단할 문제입니다.
