# 생성형 AI 업무 자동화 계획

> 상태: 설계 확정. 구현 전 단계입니다. 이 문서는 실제 코드(`3b1e2cb` 기준)를 읽고 작성했으며, 제안한 이름이 현재 코드와 다를 경우 **현재 코드를 기준으로** 조정했습니다.
>
> 기존 AX 직원 도우미(`docs/AX_FAQ_CHATBOT_PLAN.md`)는 매뉴얼·FAQ 검색 기능이며 LLM을 사용하지 않습니다. 이 문서의 생성형 AI는 **별도 계층**이고, AX 도우미를 LLM 챗봇으로 바꾸지 않습니다.

## 0. 한 줄 요약

DB에 이미 있는 사실과 사용자가 채운 맥락을 모아 **문장만** AI에게 맡기고, 결과는 사람이 확인·수정한 뒤 명시적으로 적용한다. AI는 어떤 업무 상태도 바꾸지 않는다.

---

## 1. 현재 구현 분석

### 1-1. 전자결재

| 항목 | 실제 코드 |
|---|---|
| 모델 | [`ApprovalDocument`](../backend/app/models/approval.py#L9-L41) |
| 본문 필드 | **`content` Text 하나뿐.** 목적·상세·기대효과 같은 분리된 칼럼 없음 |
| 문서 유형 | `GENERAL` / `RECRUITMENT_REQUEST` / `EXPENSE` / `QUOTATION_DISCOUNT` **4종 고정** ([schemas/approval.py:7](../backend/app/schemas/approval.py#L7)) |
| 작성 화면 | [`approval-form.tsx`](../frontend/src/features/approvals/approval-form.tsx) — 제목·문서종류·기안부서·결재자·내용. 기안자는 읽기 전용 |
| 생성 API | `POST /api/v1/approvals` → `ApprovalCreate(title, document_type, content, department_id, approver_id)` |

작성 폼이 존재하고 사용자가 `content`를 직접 입력한다. **AI 초안을 적용할 자리가 이미 있다.**

### 1-2. 채용

| 항목 | 실제 코드 |
|---|---|
| 요청 모델 | [`RecruitmentRequest`](../backend/app/models/recruitment.py#L19-L60) — `position_title`, `headcount`, `employment_type`, `experience_level`, `reason`, `responsibilities`, `required_skills`, `preferred_skills`, `desired_start_date` |
| 공고 모델 | [`JobPosting`](../backend/app/models/recruitment.py#L63-L78) — **`title` + `content` Text 둘뿐** |
| 공고 생성 | 결재 승인 시 [`process_approval`](../backend/app/services/recruitment_service.py#L224-L247)이 자동 호출 → `_create_posting` |
| 공고 본문 | [`_build_posting_content`](../backend/app/services/recruitment_service.py#L400)이 **코드로 조립**. 사람이 쓴 문장이 아님 |
| 공고 수정 | **엔드포인트 없음.** 생성 후 제목·본문을 바꿀 방법이 전혀 없다 |

**이것이 이 설계에서 가장 중요한 발견이다.** 채용공고는 사용자가 작성하는 문서가 아니라 승인 시점에 기계가 조립하는 문자열이다. 따라서 "AI 초안 → 미리보기 → 수정 → 공고에 적용"을 하려면 **공고를 수정할 수 있는 경로를 먼저 만들어야 한다**(§14 참조).

### 1-3. 포스터

| 항목 | 실제 코드 |
|---|---|
| 저장 위치 | `RecruitmentRequest`의 `poster_original_name` / `poster_stored_name` / `poster_content_type` / `poster_size` — **요청당 한 벌** |
| 허용 형식 | `{"image/jpeg", "image/png", "image/webp", "application/pdf"}` ([recruitment_service.py:32](../backend/app/services/recruitment_service.py#L32)). **SVG 없음** |
| Storage | [`supabase_storage.py`](../backend/app/core/supabase_storage.py) — `urllib` 기반, 버킷 `recruitment-posters` |
| 업로드 API | `POST /api/v1/recruitment-requests/{id}/poster` (multipart) |

포스터 슬롯이 하나이므로 AI 생성 포스터를 저장하면 **수동 업로드본을 덮어쓴다**.

### 1-4. AI 관련 기존 자산

| 항목 | 상태 |
|---|---|
| `Settings.ai_provider` / `ai_api_key` / `ai_model` | [config.py:26-28](../backend/app/core/config.py#L26-L28)에 **이미 존재**. 사용하는 코드는 없음 |
| `ai_generations` 테이블 | 없음 |
| AIProvider 코드 | 없음 |
| `docs/AI_DESIGN.md` | 설계만 존재. 필드 이름의 기준으로 삼는다 |
| 런타임 HTTP 클라이언트 | **없음.** `httpx`는 dev 의존성. 외부 API 호출은 `urllib.request` 패턴 사용 중 |

### 1-5. 조직

`Department` / `Team` / `Employee` 모두 존재. `Employee`에 `position`, `job_title`, `department_id`, `team_id`, `work_location`이 있어 AI Context의 사실 재료로 쓸 수 있다.

---

## 2. 범위

1. 전자결재 AI 초안 생성 (`APPROVAL_DRAFT`)
2. 채용공고 AI 초안 생성 (`JOB_POSTING_DRAFT`)
3. 공통 AI 기반 — Provider, Mock, Structured Output, `ai_generations`

---

## 3. 제외 범위

| 제외 항목 | 이유 |
|---|---|
| **채용 포스터 자동 생성** | Feature Freeze **밖**으로 결정. SVG 템플릿 3종·한글 줄바꿈·PNG 변환이 1·2번을 합친 것보다 크다. Freeze 통과 후 별도 진행 (§16, §17에 설계만 남긴다) |
| AX 도우미 LLM 전환 | v1은 검색 기반 유지. v2 판단은 운영 로그 근거 |
| 지원자 평가·순위·자동 탈락 | Human-in-the-loop 원칙 위반 |
| 면접 질문 생성, 경력 요약 | `AI_DESIGN.md`의 확장 후보. 이번 범위 아님 |
| RAG·벡터 DB·n8n | `DECISIONS.md` 결정 유지 |
| 스트리밍 응답 | 초안 생성은 단발 요청이라 불필요 |
| 재생성 이력 UI | `ai_generations`에 행은 쌓되 화면은 만들지 않음 |

---

## 4. 전체 Architecture

```
Router          POST /api/v1/ai/approval-drafts
  ↓             권한 검사, 요청 스키마 검증
AIGenerationService
  ├─ Repository        DB 사실 조회 (Employee, Department, Team, RecruitmentRequest)
  ├─ AIContextBuilder  DB 사실 + 사용자 입력 → Context (평문 dict)
  ├─ AIProvider        Context → LLM → 원시 문자열
  ├─ Pydantic Schema   원시 문자열 → 구조화 검증
  └─ AiGenerationRepository   ai_generations 기록
  ↓
Response        구조화 초안 + generation_id
  ↓
Frontend        미리보기 → 사용자 수정 → [적용] → 기존 폼 채우기
```

기존 `Router → Service → Repository` 계층을 그대로 따른다. AX 계층([`ax_service.py`](../backend/app/services/ax_service.py))이 가장 최근 패턴이므로 이를 참고한다.

**Provider는 DB를 모른다.** Provider가 받는 것은 정리된 dict뿐이고, Employee·Approval·Recruitment 모델을 import하지 않는다.

### 파일 배치

| 경로 | 역할 |
|---|---|
| `app/domain/ai_provider.py` | `AIProvider` 프로토콜, `AIProviderResult`, `MockAIProvider` |
| `app/domain/ai_context.py` | Context 조립 순수 함수 (DB 세션 없음) |
| `app/services/ai_generation_service.py` | 조회·Context·Provider·검증·기록 조율 |
| `app/repositories/ai_generation_repository.py` | `ai_generations` CRUD |
| `app/models/ai_generation.py` | `AiGeneration` 모델 |
| `app/schemas/ai.py` | 요청/응답 + Structured Output 스키마 |
| `app/api/ai.py` | 라우터 (`prefix="/ai"`) |

`app/domain/`에 Provider를 두는 것은 `ax_search.py`·`ax_rules.py`가 이미 도메인 순수 로직 자리로 쓰이고 있기 때문이다.

---

## 5. 데이터 흐름

```
1. 사용자가 작성 화면에서 [AI 초안 생성] 클릭
2. 부족한 맥락을 입력 (요청 목적, 주요 내용, 금액 등)
3. POST /api/v1/ai/approval-drafts
4. Service가 로그인 사용자·부서·팀·직급을 DB에서 조회
5. Context Builder가 DB 사실 + 사용자 입력을 합침
6. Provider 호출 → 원시 응답
7. Pydantic 검증 → 실패 시 성공 처리하지 않음
8. ai_generations에 generated_output 기록
9. 응답 반환 (업무 테이블은 아직 아무 변화 없음)
10. 사용자가 미리보기에서 수정
11. [전자결재에 적용] → 폼의 title·content 채움
12. 사용자가 [임시 저장] 또는 [결재 요청]을 눌러야 비로소 DB 저장
```

9단계까지 `approval_documents`는 **한 행도 변하지 않는다**.

---

## 6. DB에서 자동 조회할 데이터

### 전자결재

| 값 | 출처 |
|---|---|
| 기안자 이름·직급·직무 | `Employee.name` / `position` / `job_title` |
| 부서명 | `Department.name` |
| 팀명 | `Team.name` (없으면 생략) |
| 작성일 | 서버 현재 날짜 |

### 채용공고

| 값 | 출처 |
|---|---|
| 직무명 | `RecruitmentRequest.position_title` |
| 채용 인원 | `headcount` |
| 고용 형태 | `employment_type` |
| 경력 요건 | `experience_level` |
| 채용 사유 | `reason` |
| 주요 업무 | `responsibilities` |
| 필수/우대 역량 | `required_skills` / `preferred_skills` |
| 입사 희망일 | `desired_start_date` |
| 요청 부서 | `Department.name` |
| 요청자 | `Employee.name` |

`required_skills`·`preferred_skills`·`responsibilities`는 **이미 사용자가 쓴 텍스트**다. AI는 이것을 없는 것처럼 새로 만들지 않고 **공고 문장으로 다듬는다**.

---

## 7. 사용자가 추가 입력할 데이터

### 전자결재 (신규 DB 칼럼 없음 — §12 참조)

| 항목 | 필수 | 비고 |
|---|---|---|
| 문서 유형 | ✔ | 기존 4종에서 선택 |
| 요청 목적 | ✔ | |
| 주요 내용 | ✔ | |
| 금액 | | 입력 시에만 본문에 등장 |
| 수량 | | |
| 희망 시점 | | |
| 추가 설명 | | |

### 채용공고

| 항목 | 비고 |
|---|---|
| 근무 위치 | DB에 없음 |
| 지원 마감일 | DB에 없음 |
| 지원 방법 | DB에 없음 |
| 팀 소개 | 선택 |
| 급여·처우 | 선택. 입력 없으면 "협의 후 결정" 등 사실을 만들지 않는 표현만 허용 |

---

## 8. AI가 생성할 데이터

### `ApprovalDraftOutput`

| 필드 | 설명 | 길이 상한 |
|---|---|---|
| `title` | 문서 제목 | 200자 (모델 제약과 동일) |
| `purpose` | 요청 목적 문단 | 500자 |
| `details` | 주요 내용 문단 | 1500자 |
| `expected_effect` | 기대 효과 문단 | 500자 |

### `JobPostingDraftOutput`

| 필드 | 길이 상한 |
|---|---|
| `headline` | 200자 |
| `introduction` | 600자 |
| `responsibilities` | 문자열 배열, 최대 8개 · 각 200자 |
| `requirements` | 문자열 배열, 최대 8개 · 각 200자 |
| `preferred_qualifications` | 문자열 배열, 최대 6개 · 각 200자 |
| `team_or_recruitment_description` | 600자 |
| `closing_message` | 300자 |

`title` 200자 상한은 `ApprovalDocument.title`·`JobPosting.title`이 `String(200)`이기 때문이다. 스키마에서 막지 않으면 DB 저장 시점에 터진다.

---

## 9. AI가 생성하면 안 되는 데이터

금액 · 날짜 · 수량 · 채용 인원 · 급여 · 복리후생 · 회사 정책 · 자격증 요구사항 · 고용 형태 · 근무 위치 · 지원 마감일 · 결재자 · 예산 · 구매처 · 승인 여부 · 합격 여부.

강제 방법 3중:

1. **프롬프트 명시** — "제공되지 않은 수치·날짜·고유명사를 만들지 마라. 없으면 해당 문장을 쓰지 마라."
2. **Context에서 제외** — 주지 않은 값은 AI가 알 수 없다.
3. **테스트로 검증** — 금액을 주지 않은 Context로 Mock이 아닌 스키마 검증 경로를 태워, 출력에 숫자+통화 패턴이 나타나지 않는지 확인한다.

세 번째는 실제 LLM에서 100% 보장할 수 없다. 그래서 **사용자가 반드시 미리보기에서 확인한 뒤 적용**하는 구조가 최종 방어선이다.

---

## 10. Provider 설계

```python
class AIProviderResult:
    content: str          # 원시 응답 문자열
    provider: str
    model_name: str | None
    success: bool
    error_message: str | None

class AIProvider(Protocol):
    def generate(self, feature_type: str, context: dict, schema_hint: str) -> AIProviderResult: ...
```

| Provider | 조건 |
|---|---|
| `MockAIProvider` | `AI_PROVIDER=mock`(기본값) 또는 `AI_API_KEY` 미설정 |
| 실제 LLM Provider | `AI_PROVIDER`가 실제 값 + `AI_API_KEY` 존재 |

`ax_search.KeywordSearcher`를 `get_ax_service`에서 한 줄로 주입하는 방식과 동일하게, `get_ai_generation_service`에서 Provider를 선택한다.

### 공식 SDK 1개 추가

`urllib`로 직접 호출해 의존성을 0으로 유지하는 안을 먼저 검토했으나 **철회한다.** Structured Output 검증·재시도·타입 정의를 직접 구현하는 비용이 의존성 1개보다 크다.

`pyproject.toml`에 **`anthropic`** 을 추가한다. SDK가 제공하는 것:

- `client.messages.parse(output_config={"format": ...})` — Pydantic 모델로 응답 자동 검증
- JSON Schema가 지원하지 않는 문자열 제약(`max_length` 등)을 SDK가 클라이언트에서 검증하므로 §8의 길이 상한이 그대로 작동한다
- 429·5xx·네트워크 오류 자동 재시도(기본 2회)
- `anthropic.APITimeoutError` 등 타입 있는 예외
- `response.usage`로 실제 소비 토큰 수 반환 (§13 비용 추적에 사용)

```python
client = Anthropic(
    api_key=settings.ai_api_key,
    timeout=15.0,     # 무한 대기 차단
    max_retries=2,    # 무한 재시도 차단
)
response = client.messages.parse(
    model=settings.ai_model or "claude-opus-5",
    max_tokens=8000,  # 출력이 입력보다 5배 비싸다 → 건당 비용 상한
    thinking={"type": "adaptive"},
    output_config={"effort": "low"},
    system=PROMPT,
    messages=[{"role": "user", "content": json.dumps(context, ensure_ascii=False)}],
)
```

`effort`는 `low`로 시작한다. 초안 생성은 짧고 사용자가 화면에서 기다리는 작업이라 지연이 품질보다 중요하다. `thinking`을 끄면 응답에 내부 태그가 새는 사례가 보고돼 있으므로 켠 채로 effort를 낮춘다.

### 모델 선정

| 모델 | 종합 지능 | 언어·지시 | 입력 $/1M | 출력 $/1M |
|---|---|---|---|---|
| **`claude-opus-5`** (채택) | 1위 | 4위 | 5 | 25 |
| GPT-5.6 Sol | 3위 | 7위 | 5 | 30 |
| GPT-5.6 Terra | 7위 | 데이터 없음 | 2 | 12 |
| `claude-sonnet-5` | 10위 | 18위 | 3 | 15 |
| GPT-5.6 Luna | 15위 | 데이터 없음 | 0.20 | 1.20 |

**`claude-opus-5`를 기본값으로 한다.** 두 지표 모두 상위권이고, 같은 급인 Sol보다 저렴하다. 더 싼 후보(Terra·Luna)는 언어·지시 벤치마크 데이터가 없어 한국어 문장 품질이 미검증이다.

이 프로젝트의 실사용량은 **월 20~40회**(개발은 Mock, 실호출은 검증·시연뿐)이므로 모델 간 월 비용 차이는 몇백 원 수준이다. 비용이 아니라 품질로 정한다.

**실측(2026-08-12, `claude-opus-5`, `effort: low`)**: 전자결재 1건 입력 1,316 / 출력 286 토큰 → 약 19원. 채용공고 1건 입력 1,902 / 출력 299 토큰 → 약 24원. 설계 시 추정치(81원·119원)의 약 1/5이다. `effort: low`가 예상보다 훨씬 간결하게 쓰는 것이 원인이므로, 출력 토큰을 과대추정하지 않도록 이 실측값을 기준으로 삼는다.

`AI_MODEL` 환경변수로 교체 가능하게 두어, 실제 샘플을 본 뒤 더 싼 모델로 내릴지 판단한다.

### 실패 처리

| 실패 | 처리 |
|---|---|
| API 오류 (4xx/5xx) | `success=false`, 정리된 메시지. 원시 응답 노출 금지 |
| Timeout | `Anthropic(timeout=15.0)`. 초과 시 `anthropic.APITimeoutError` |
| 크레딧 소진 | 인증 오류로 실패 처리. **선불이라 카드가 추가로 긁히지 않는다**(§19) |
| 응답 파싱 오류 | JSON이 아니면 실패 |
| Structured Output 위반 | Pydantic `ValidationError` → 실패 |
| Provider 미설정 | 명시적 오타는 설정 오류(500), 기본값 누락은 Mock |

**어떤 실패도 기존 전자결재·채용 기능을 건드리지 않는다.** AI 엔드포인트는 업무 테이블에 쓰지 않으므로 rollback할 것도 없다.

---

## 11. Context Builder

```python
def build_approval_context(*, author, department, team, user_input) -> dict
def build_job_posting_context(*, request, department, requester, user_input) -> dict
```

DB 세션을 받지 않는 **순수 함수**로 만든다. Service가 조회한 모델 인스턴스를 넘겨받아 dict를 만든다. 테스트에서 DB 없이 검증할 수 있다.

Context에 넣지 않는 것: 이메일, 전화번호, 사번, 근태 사유, 비공개 상세 사유, 다른 직원 정보, 지원자 개인정보, 토큰·키·환경변수.

---

## 12. Structured Output Schema

Pydantic v2 모델로 정의하고 `max_length`·`max_items`를 스키마 레벨에서 강제한다. 검증 실패는 성공으로 처리하지 않는다.

**구조화 결과와 저장 형식의 관계** — `ApprovalDocument.content`는 Text 하나다. 4개 필드는 최종적으로 한 덩어리 문자열이 되어야 한다.

> **결정:** 조립은 **프론트엔드**에서 한다.
>
> 이유 — 사용자가 미리보기에서 `purpose`만 고치고 `details`는 그대로 두는 식의 필드 단위 수정을 해야 하는데, 백엔드가 미리 합쳐 버리면 그 단위가 사라진다. 프론트가 필드별 textarea를 보여주고 [적용] 시점에 합친다.

조립 형식은 기존 `_build_approval_content`의 `"제목\n본문\n\n제목\n본문"` 관례를 따른다.

---

## 13. `ai_generations` 설계

`docs/AI_DESIGN.md`가 이미 이 테이블을 설계해 두었다. 공통 지침 11번(이름이 다르면 기존 프로젝트 기준)에 따라 **AI_DESIGN.md의 이름을 채택**한다.

| 칼럼 | 타입 | 설명 |
|---|---|---|
| `id` | String(50) PK | `ai-gen-{uuid4hex}` |
| `feature_type` | String(40) | `APPROVAL_DRAFT` / `JOB_POSTING_DRAFT` |
| `related_type` | String(40) nullable | `RECRUITMENT_REQUEST` 등. 생성 시점에 대상이 없으면 null |
| `related_id` | String(50) nullable | |
| `source_input` | JSON | Context 스냅샷 |
| `generated_output` | JSON nullable | AI 최초 결과. **덮어쓰지 않는다** |
| `final_output` | JSON nullable | 사용자가 적용한 최종본 |
| `provider` | String(30) | `mock` / 실제 |
| `model_name` | String(100) nullable | |
| `success` | Boolean | |
| `error_message` | Text nullable | |
| `input_tokens` | Integer nullable | `response.usage.input_tokens` |
| `output_tokens` | Integer nullable | `response.usage.output_tokens` |
| `created_by_id` | FK employees | |
| `created_at` | DateTime(tz) | |

인덱스: `(feature_type, created_at)`, `(related_type, related_id)`, `(created_by_id, created_at)`

세 번째 인덱스는 §20의 일일 호출 제한 조회용이다.

### 토큰 수를 저장하는 이유 — 비용 추적

SDK가 응답에 실제 소비 토큰을 담아준다. 저장만 하면 **추가 테이블 없이 쿼리 하나로 실제 지출을 계산**할 수 있다.

```sql
SELECT SUM(input_tokens) * 5 / 1e6 + SUM(output_tokens) * 25 / 1e6 AS usd
FROM ai_generations
WHERE created_at >= now() - interval '30 days';
```

Console을 열지 않고도 앱 안에서 확인된다. 이상 급증을 조기에 발견하는 수단이기도 하다(§19).

### 프롬프트 제안 이름과의 차이

| 프롬프트 | 채택 | 근거 |
|---|---|---|
| `generation_type` | `feature_type` | AI_DESIGN.md |
| `source_type`/`source_id` | `related_type`/`related_id` | AI_DESIGN.md + `ApprovalDocument`가 이미 동일 이름 사용 |
| `input_snapshot` | `source_input` | AI_DESIGN.md |
| `status` | `success` + `error_message` | 호출이 동기라 중간 상태가 없다 |

재생성은 기존 행을 덮어쓰지 않고 **새 행을 추가**한다.

---

## 14. API 설계

| Method | Path | 권한 | 설명 |
|---|---|---|---|
| `POST` | `/api/v1/ai/approval-drafts` | 인증된 전 역할 | 전자결재 초안 생성 |
| `POST` | `/api/v1/ai/job-posting-drafts` | `SUPER_ADMIN`, `HR_ADMIN`, 요청 부서 `TEAM_ADMIN` | 공고 초안 생성 |
| `PATCH` | `/api/v1/ai/generations/{id}/final` | 생성자 본인 | `final_output` 기록 |
| `PATCH` | `/api/v1/job-postings/{id}` | `SUPER_ADMIN`, `HR_ADMIN` | **신설 필요** — 공고 제목·본문 수정 |

### `PATCH /job-postings/{id}`를 신설해야 하는 이유

현재 `JobPosting`은 승인 시 자동 생성되고 **수정 경로가 전혀 없다**(§1-2). AI 초안을 "공고에 적용"하려면 공고를 고칠 수 있어야 한다. 이것은 AI를 위한 우회로가 아니라 원래 비어 있던 기능이다.

제약: `title`·`content`만 수정 가능. `status`는 **바꿀 수 없다**. AI가 공고를 게시 상태로 바꾸는 경로를 원천 차단한다.

---

## 15. Frontend UX

### 전자결재

```
/approvals/new
  └ [AI 초안 생성] 버튼
      → 패널 열림: 요청 목적 · 주요 내용 · 금액 · 수량 · 희망 시점 · 추가 설명
      → [생성]
      → 미리보기: title / purpose / details / expected_effect 각각 편집 가능
      → [전자결재에 적용]
      → 폼의 제목·내용 채움 (저장 아님)
      → 사용자가 [임시 저장] 또는 [결재 요청]
```

### 채용공고

```
/job-postings (목록) → 공고 상세
  └ [AI 공고 초안 생성]
      → DB 값 자동 표시 (직무·인원·고용형태·경력·업무·역량)
      → 부족한 값 입력 (근무지·마감일·지원방법·팀 소개)
      → [생성] → 미리보기 → 수정
      → [공고 내용에 적용] → PATCH /job-postings/{id}
```

전자결재는 **저장 전 폼 채우기**, 채용공고는 **이미 존재하는 행 수정**이다. 둘 다 사용자가 버튼을 눌러야 일어난다.

Mock Provider 결과일 때는 미리보기에 "샘플 응답" 배지를 표시해 실제 LLM 결과로 오해하지 않게 한다.

API 호출은 `features/ai/api.ts`에서 기존 `apiRequest` 패턴을 따른다.

---

## 16. 포스터 생성 구조 (Freeze 밖 · 설계만)

AI는 **문구만** 만들고 배치는 코드가 결정한다.

```
DB + 사용자 입력 → AI Poster Copy → Structured Poster Data
                                        ↓
                            SVG 템플릿 (Corporate / Tech / Simple)
                                        ↓
                            브라우저 미리보기 → 사용자 수정
                                        ↓
                            Canvas → PNG (프론트엔드)
                                        ↓
                            기존 포스터 업로드 API 재사용
```

렌더링 우선순위: ① SVG 결정론적 템플릿 → ② 프론트엔드 SVG→Canvas→PNG → ③ 현재 의존성만의 HTML/CSS.

**금지:** Backend Playwright screenshot, Backend Chromium, WeasyPrint, 기타 대형 네이티브 렌더러. Render Free 플랜에서 빌드 용량·cold start·메모리를 감당할 수 없다.

한글은 브라우저 폰트 fallback을 쓴다. 서버에 특정 폰트가 설치돼 있다고 가정하지 않고, 런타임에 외부 폰트를 내려받지 않는다. 프론트엔드 Canvas 변환을 택하면 이 문제가 구조적으로 사라진다.

긴 문구는 `overflow: hidden`으로 자르지 않는다. Structured Output 길이 제한 + 항목 수 제한 + 템플릿별 최대 글자수 + 안전한 줄바꿈을 함께 쓴다.

---

## 17. Storage 연동 (Freeze 밖 · 설계만)

기존 `recruitment-posters` 버킷과 업로드 API를 그대로 쓴다. 새 저장 체계를 만들지 않는다.

**SVG를 허용 MIME에 추가하지 않는다.** 현재 `{jpeg, png, webp, pdf}`이며 SVG는 스크립트 삽입 벡터가 된다. SVG는 템플릿·미리보기 내부 표현으로만 쓰고 **최종 저장은 PNG**다. 기존 업로드 검증을 확대하지 않는다.

**미결:** 포스터 슬롯이 요청당 하나라 AI 생성본이 수동 업로드본을 덮어쓴다(§1-3). 덮어쓰기 확인 다이얼로그로 갈지, 칼럼을 늘릴지는 포스터 작업 착수 시 결정한다.

---

## 18. Human-in-the-loop

AI가 자동 수행하지 않는 것: 전자결재 상신 · 승인 · 반려 · 취소 · 삭제, 채용 요청 상신, 공고 게시 상태 변경, 지원자 단계 변경, 합격/불합격 처리, 알림 발송.

구조적 보장:

| 보장 | 방법 |
|---|---|
| 상태 변경 불가 | AI 엔드포인트가 업무 테이블에 **쓰지 않는다**. Service가 approval/recruitment repository의 쓰기 메서드를 호출하지 않음 |
| 상신·승인 불가 | AI 라우터에서 `submit`/`approve`/`reject` 서비스 메서드를 import하지 않음 |
| 공고 게시 불가 | `PATCH /job-postings/{id}`가 `status`를 받지 않음 |
| 자동 저장 불가 | 적용은 프론트 상태 변경이며, 저장은 사용자가 별도 버튼을 눌러야 함 |

---

## 19. 보안

| 항목 | 조치 |
|---|---|
| API Key | `Settings.ai_api_key`로만 읽고 로그·응답·예외 메시지에 넣지 않음 |
| Supabase Secret / DB URL | Context에 넣지 않음 |
| access token | Context에 넣지 않음 |
| 개인정보 | 이메일·전화·사번을 Context에서 제외. 이름·직급·부서만 사용 |
| 근태 사유 | 전면 제외. 비공개 상세 사유는 특히 금지 |
| 다른 직원 데이터 | 본인·요청자 정보만 |
| Provider 오류 | 원시 SDK 응답을 사용자에게 노출하지 않고 정리된 메시지만 |
| `source_input` 저장 | Context와 동일한 최소 데이터만 저장 |
| API Key 노출 경로 | 프론트엔드는 AI Provider를 직접 호출하지 않는다. 백엔드에서만 호출하므로 브라우저에 키가 보이지 않는다. `NEXT_PUBLIC_*`에 절대 넣지 않는다 |
| `.env` 커밋 | `.gitignore`에 `backend/.env`가 이미 포함되어 있고 `.example`만 추적된다(확인 완료) |
| 운영 키 보관 | Render 대시보드 환경변수에만 등록 |

### 비용 사고 방지

AI Provider는 이 프로젝트에서 **유일하게 사용량에 비례해 돈이 나가는 외부 자원**이다. 포트폴리오는 링크를 공개하는 것이 목적이므로, 인증만 통과하면 누구나 누르는 버튼 뒤에 유료 API가 걸린다.

**구조적 안전장치:** Anthropic API는 후불 종량제가 아니라 **선불 크레딧**이다. 충전한 금액을 다 쓰면 호출이 실패할 뿐 카드가 추가로 청구되지 않는다. 즉 **잔액이 곧 손실 상한**이다.

| 겹 | 조치 | 효과 |
|---|---|---|
| 1 계정 | **Auto-reload OFF** | 이것 하나로 상한이 확정된다. 켜두면 후불과 같아진다 |
| 1 계정 | 첫 충전 $5, Spend limit $10 | 최악의 손실을 금액으로 고정 |
| 1 계정 | Usage 알림 50% / 80% | 이상 징후 조기 감지 |
| 2 코드 | `max_tokens=8000`, `timeout=15.0`, `max_retries=2` | 건당 비용·대기·재시도 상한 |
| 3 앱 | 일일 호출 제한 (§20) | 크레딧이 하루 만에 증발하는 것을 방지 |
| 4 관측 | `input_tokens`/`output_tokens` 집계 (§13) | 앱 안에서 실지출 확인 |

정상 사용량이 월 20~40회이므로 §20의 제한은 실사용에서 걸리지 않는다.

---

## 20. 오류 처리

| 상황 | HTTP | 사용자 문구 |
|---|---|---|
| 입력 검증 실패 | 422 | 기존 FastAPI 형식 |
| 권한 없음 | 403 | 기존 형식 |
| 대상 없음 | 404 | |
| **일일 호출 한도 초과** | **429** | "오늘 AI 초안 생성 한도를 초과했습니다." |
| Provider 실패 | **200 + `success: false`** | "초안을 생성하지 못했습니다. 직접 작성할 수 있습니다." |
| Provider 설정 오류 | 500 | 설정 오류임을 알리되 값은 노출 안 함 |

Provider 실패를 5xx로 던지지 않는 이유: 초안 생성은 **부가 기능**이고, 실패해도 사용자는 직접 작성하면 된다. 실패도 `ai_generations`에 `success=false`로 기록한다.

### 일일 호출 제한

Service 진입점에서 Provider를 부르기 **전에** 두 카운트를 확인한다. `ai_generations`의 `created_by_id`·`created_at`으로 세므로 추가 테이블이 필요 없다.

| 제한 | 값 | 근거 |
|---|---|---|
| 사용자당 일일 | 5회 | 정상 사용(1인 하루 1~2회)의 3~5배 |
| **전역 일일** | **30회** | 정상 사용의 15~30배. 실질적인 방어선 |

사용자당 제한만 두면 46명 × 5회 = 230회까지 열린다. **전역 상한이 실제 방어선**이다. 30회면 하루 최대 약 $2이라, $5 크레딧이 소진되려면 이틀 이상 지속 공격이 필요하고 그 전에 사용량 알림이 온다.

```python
if repository.count_today() >= GLOBAL_DAILY_LIMIT:
    raise HTTPException(429, "오늘 AI 초안 생성 한도를 초과했습니다.")
if repository.count_today(created_by_id=actor.employee_id) >= USER_DAILY_LIMIT:
    raise HTTPException(429, "오늘 AI 초안 생성 한도를 초과했습니다.")
```

한도 초과는 Provider를 호출하지 않으므로 `ai_generations`에 기록하지 않는다. 프론트엔드는 요청 중 버튼을 `disabled`로 두어 연타 자체를 막는다.

---

## 21. 테스트 전략

기존 방식(인메모리 SQLite + `fake_poster_storage`)을 그대로 쓴다. **네트워크를 타지 않는다** — 실제 Provider는 `monkeypatch`로 가짜 응답을 주입한다.

| # | 검증 | 단계 |
|---|---|---|
| 1 | Mock Provider 선택 (설정 없을 때) | 1 |
| 2 | Provider 성공 → 구조화 결과 | 1 |
| 3 | Provider 실패 → `success=false` 기록, 200 응답 | 1 |
| 4 | Timeout → 실패 처리 | 1 |
| 5 | 스키마 위반 응답 → 성공 처리 안 함 | 1 |
| 6 | 길이 초과 → 검증 실패 | 1 |
| 7 | `ai_generations` 성공/실패 기록 | 1 |
| 8 | AI 호출 후 `approval_documents` 행 수 불변 | 1·2 |
| 9 | Context에 이메일·사번·토큰 없음 | 1 |
| 10 | 사용자당 일일 한도 초과 → 429 | 1 |
| 11 | 전역 일일 한도 초과 → 429 | 1 |
| 12 | 한도 초과 시 Provider를 호출하지 않음 | 1 |
| 13 | 성공 시 `input_tokens`/`output_tokens` 기록 | 1 |
| 14 | 사용자/조직 Context 정상 구성 | 2 |
| 15 | 금액 미입력 시 Context에 금액 키 없음 | 2 |
| 16 | 초안 생성만으로 Approval 상태 불변 | 2 |
| 17 | 기존 전자결재 작성/수정/상신/승인/반려 회귀 | 2 |
| 18 | RecruitmentRequest Context 조회 | 3 |
| 19 | 권한 없는 역할 403 | 3 |
| 20 | `PATCH /job-postings/{id}`로 `status` 변경 불가 | 3 |
| 21 | 초안 생성만으로 채용 상태 불변 | 3 |
| 22 | 기존 채용 요청→승인→공고 흐름 회귀 | 3 |

**E2E는 추가하지 않는다.** 프론트에 단위 테스트 프레임워크가 없고, Playwright E2E는 `workflow_dispatch` 전용으로 실제 Supabase에 접속한다. AI 흐름을 E2E에 넣으면 운영 DB에 붙는 테스트가 늘어난다. 백엔드 테스트 + 수동 확인으로 커버한다.

---

## 22. Migration 계획

| 항목 | 값 |
|---|---|
| 현재 head | `20260810_0021` (코드·DB 일치 확인 완료) |
| 새 revision | `20260812_0022_ai_generations` |
| `down_revision` | `"20260810_0021"` |
| 내용 | `ai_generations` 테이블(`input_tokens`·`output_tokens` 포함) + 인덱스 3개 |
| `downgrade` | `drop_index` ×3 → `drop_table` |

**운영 DB 적용은 수동이다.** Render Build Command가 `pip install .`뿐이라 배포가 migration을 실행하지 않는다([DEPLOYMENT_PLAN.md](DEPLOYMENT_PLAN.md)). 배포 전에 Supabase에 `alembic upgrade head`를 직접 적용하지 않으면 운영에서 없는 테이블을 조회해 500이 난다. **Prompt 1 완료 조건에 포함한다.**

`JobPosting` 수정 API(§14)는 **migration이 필요 없다**. 기존 칼럼만 쓴다.

---

## 23. 구현 순서

| 단계 | 내용 | 검증 |
|---|---|---|
| *(사전)* | Anthropic Console: **Auto-reload OFF** → 크레딧 $5 충전 → Spend limit $10 → 사용량 알림 → API 키 발급 | §19 체크리스트 |
| **Prompt 1** | Provider·Mock·Structured Output·일일 한도·`ai_generations`·migration 0022·운영 DB 적용 | ruff, pytest. 화면 변화 없음 |
| **Prompt 2** | 전자결재 AI 초안 (API + UI) | ruff, pytest, lint/typecheck/build |
| **Prompt 3** | `PATCH /job-postings/{id}` 신설 + 공고 AI 초안 | 동일 |
| **Prompt 5** | Feature Freeze 판정 | 전체 회귀 |
| *(Freeze 밖)* | 포스터 자동 생성 | — |

각 단계 완료 시 관련 문서(`API_SPEC.md`, `DATA_MODEL.md`, `UPDATELOG.md`)를 함께 갱신한다. 두 문서는 이미 `ax_chat_logs`와 `/ax/chat`이 누락된 채 밀려 있어, 또 미루면 격차가 커진다.

---

## 24. 예상 변경 파일

### Prompt 1

| 구분 | 파일 |
|---|---|
| 신규 | `app/domain/ai_provider.py`, `app/domain/ai_context.py`, `app/models/ai_generation.py`, `app/repositories/ai_generation_repository.py`, `app/services/ai_generation_service.py`, `app/schemas/ai.py`, `migrations/versions/20260812_0022_ai_generations.py`, `tests/test_ai_provider.py`, `tests/test_ai_generation_service.py` |
| 수정 | `app/models/__init__.py`, `app/api/dependencies.py`, **`pyproject.toml`**(`anthropic` 추가), `app/core/config.py`(일일 한도 설정값) |

### Prompt 2

| 구분 | 파일 |
|---|---|
| 신규 | `app/api/ai.py`, `frontend/src/features/ai/api.ts`, `frontend/src/features/ai/approval-draft-panel.tsx`, `frontend/src/types/ai.ts`, `tests/test_ai_approval_api.py` |
| 수정 | `app/api/router.py`, `frontend/src/features/approvals/approval-form.tsx`, `frontend/src/app/globals.css`, `docs/API_SPEC.md`, `docs/DATA_MODEL.md` |

### Prompt 3

| 구분 | 파일 |
|---|---|
| 신규 | `frontend/src/features/ai/job-posting-draft-panel.tsx`, `tests/test_ai_job_posting_api.py` |
| 수정 | `app/api/ai.py`, `app/api/recruitment.py`, `app/services/recruitment_service.py`, `app/schemas/recruitment.py`, `frontend/src/features/recruitment/job-posting-list.tsx`, `docs/API_SPEC.md` |

`app/services/approval_service.py`와 `app/services/recruitment_service.py`의 **기존 메서드는 수정하지 않는다.** Prompt 3의 `recruitment_service.py` 변경은 공고 수정 메서드 추가뿐이다.
