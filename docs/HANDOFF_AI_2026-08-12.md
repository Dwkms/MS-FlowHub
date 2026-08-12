# 작업 인계 문서 — 생성형 AI 자동화 (2026-08-12)

> 이 문서만 읽고 이어서 작업할 수 있게 작성했습니다. 설계 근거는 [`AI_AUTOMATION_PLAN.md`](AI_AUTOMATION_PLAN.md)를 보세요.

## 한 줄 요약

**Prompt 0~3 완료.** 공통 AI 기반, 전자결재 AI 초안, 채용공고 AI 초안이 동작하며 **실제 `claude-opus-5` 호출까지 검증했습니다.** 다음은 **Prompt 5(Feature Freeze 판정)**. 포스터(Prompt 4)는 Freeze 밖으로 뺐습니다.

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

### 3) Prompt 5 착수 (Feature Freeze 판정)

새 기능을 만들지 않고 전체를 점검합니다. **P0과 P1이 0개일 때만** `FEATURE FREEZE READY: YES`입니다.

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

### 0) PR 머지 후 로컬 정리 — 먼저 할 것

수동 검수에서 찾은 결함·개선은 **커밋·푸시 완료**했습니다(`d0dadd8`, 브랜치
`fix/ai-review-findings`). PR만 만들어 머지하면 됩니다.

```
https://github.com/Dwkms/MS-FlowHub/pull/new/fix/ai-review-findings
```

머지 후:

```powershell
git switch master
git pull --ff-only
git branch -d fix/ai-review-findings
```

미커밋으로 남는 것은 `docs/JIRA_UPDATE_2026-08-08.md` 하나뿐입니다(표 자동정렬, 내용 변경 0).

### 1) 기능 1 — 세션 자동 로그아웃 (보안)

**원인**: `supabase-browser.ts`가 옵션 없이 `createClient()`를 호출해 `persistSession: true`가 적용됩니다. 세션이 localStorage에 남고 토큰이 자동 갱신돼 다음날도 로그인 상태입니다.

**방식**: "브라우저를 닫았는지"는 감지 불가하지만 감지할 필요도 없습니다. **마지막 활동 시각만 기록**하면 닫혀 있던 시간도 무동작으로 계산됩니다.

- 활동(클릭·키·스크롤) 시 `localStorage.lastActiveAt` 갱신
- 마운트 · 탭 복귀(`visibilitychange`) · 1분 타이머로 경과 확인 → 초과 시 `signOut()`
- 만료 1분 전 경고 모달, 여러 탭 동기화(`storage` 이벤트)
- 로그인 화면에 "장시간 미사용으로 로그아웃되었습니다" 안내
- `NEXT_PUBLIC_IDLE_LOGOUT_MINUTES` **기본 30분** (5분은 시연 중 끊김)

**범위**: 프론트 신규 1파일 + `auth-session-guard.tsx` 확장. 백엔드 변경 없음.

### 2) 기능 2 — 채용공고 작성 구체화

**A. 자유 입력 → 드롭다운** (지금 "정규직/정규/풀타임"이 제각각 들어가고 그대로 AI Context로 감)

| 항목 | 선택지 |
|---|---|
| 고용 형태 | 정규직 / 계약직 / 인턴 / 파트타임 / 프리랜서 |
| 경력 수준 | 신입 / 경력무관 / 1년↑ / 3년↑ / 5년↑ / 10년↑ |
| 학력 *(신규)* | 학력무관 / 고졸↑ / 초대졸↑ / 대졸↑ / 석사↑ |

**B. AI 패널에서 매번 재입력하던 값을 DB로** — 이게 핵심

`work_location` · `salary` · `application_deadline` · `apply_method`(드롭다운) · `education_level`

→ 채용 요청 작성 시 한 번 입력 → **결재자가 근무지·급여·마감일을 보고 승인** → AI가 자동으로 가져감. AI 패널 입력칸이 5개에서 1개(팀 소개)로 줄어듭니다.

**범위**: migration 1개(칼럼 5개, 전부 nullable) + 백엔드 4곳 + 프론트 3화면 + 테스트.
기존 자유 입력 데이터와 충돌하지 않도록 **기존 값은 두고 신규 입력만 제한**합니다.

**착수 전 확정 필요**: 위 드롭다운 선택지 목록.

### 3) Prompt 5 재판정 → Feature Freeze

기능 1·2는 신규 기능이라 Freeze가 밀립니다. 완료 후 Prompt 5를 다시 돌려 판정합니다.
(직전 판정은 `P0 0건 · P1 0건`으로 YES였습니다.)
