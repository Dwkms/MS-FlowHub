# Domain

업무 규칙과 상태 전이입니다. 코드에서 확인한 것만 적고, 확인되지 않은 것은 "확인 필요"로 남겼습니다.
테이블 구조는 [`DATA_MODEL.md`](DATA_MODEL.md), 엔드포인트는 [`API_SPEC.md`](API_SPEC.md).

## 역할과 권한

### 역할 값이 두 벌 있습니다 — 먼저 읽으세요

권한 판정에 쓰이는 값과 직원 레코드에 저장된 값이 다릅니다.

| 컬럼 | 값 | 쓰이는 곳 |
|---|---|---|
| **`employee_accounts.role`** | `SUPER_ADMIN` · `HR_ADMIN` · `TEAM_ADMIN` · `PART_ADMIN` · `EMPLOYEE` | **권한의 단일 출처.** `get_authenticated_actor`가 이 값으로 `ActorContext`를 만든다 |
| `employees.role` | `ADMIN` · `HR_MANAGER` · `DEPARTMENT_HEAD` · `SALES_REP` · `EMPLOYEE` | Seed(`organization_repository._role_for`)와 테스트 픽스처가 채우는 별개 값 |

그래서 Service 코드의 권한 검사에 `{SUPER_ADMIN, HR_ADMIN, "ADMIN", "HR_MANAGER"}`처럼
**두 어휘가 섞여 나옵니다.** 두 벌 모두를 방어적으로 받는 것이지 오타가 아닙니다.

`PATCH /employees/{id}/role`이 받는 `Literal`은 `employee_accounts.role`의 5개뿐입니다.

> **확인 필요**: 두 어휘를 하나로 통합할지 결정되지 않았습니다. 새 권한 분기를 추가할 때는
> 반드시 `ActorContext.role`(= `employee_accounts.role`)을 기준으로 하세요.

### 관리 범위

| 역할 | 관리 대상 |
|---|---|
| `SUPER_ADMIN` | 전사. 직원·조직·역할 변경, 모든 결재 처리, 매뉴얼 관리 |
| `HR_ADMIN` | 전사 직원·조직·근태. 비공개 사유 열람 가능 |
| `TEAM_ADMIN` (팀장) | **소속 부서 전체.** 산하 파트를 가리지 않는다 |
| `PART_ADMIN` (파트장) | **자기 파트만.** 파트가 지정되지 않으면 본인만 (부서로 넓어지지 않음) |
| `EMPLOYEE` | 본인만 |

범위 기준은 역할에 고정돼 있습니다(`domain/org_scope.py`). 관리자의 `team_id`가 채워졌는지에
따라 의미가 달라지지 않습니다.

**비공개 근태 사유**(`employment_status_private_note`, `daily_work_reason.private_note`)는
`SUPER_ADMIN`·`HR_ADMIN`(및 레거시 `ADMIN`·`HR_MANAGER`)만 볼 수 있습니다.
`TEAM_ADMIN`·`PART_ADMIN`은 볼 수 없습니다 — `domain/employee_status.py:PRIVATE_REASON_VIEWER_ROLES`.

**결재자 자격**: 파트장급 이상만 결재자로 지정할 수 있습니다
(`domain/recruitment_policy.py`). 파트장이 팀원의 상급자이고 팀장에게 보고하는 구조를 따릅니다.
같은 정책이 프론트 `lib/approver-policy.ts`에도 있어 한쪽만 고치면 화면과 서버 판정이 어긋납니다.

> 설계 근거는 [`DECISIONS.md`](DECISIONS.md)의 "파트장 권한 역할 PART_ADMIN 신설"에 있습니다.

## 전자결재

핵심 엔진입니다. 채용 요청이 이 엔진을 타고 승인되면 공고가 생깁니다.

**상태**: `DRAFT` → `PENDING` → `APPROVED` 또는 `REJECTED` (`CANCELLED`는 스키마에 정의됨)

| 규칙 | 내용 |
|---|---|
| 작성자 = 인증 주체 | 요청 본문의 작성자 값을 믿지 않고 `ActorContext`에서 가져온다 |
| 수정 | `DRAFT` 상태에서 **작성자만** |
| 상신 | `DRAFT` 상태에서 **작성자만** |
| 결재자 자격 | **파트장급 이상만** 지정 가능 (`domain/recruitment_policy.py`) |
| 작성자 ≠ 결재자 | 같으면 생성·수정 단계에서 막는다 |
| 본인 문서 자가승인 금지 | 작성자는 승인·반려할 수 없다. 단, `SUPER_ADMIN`/`ADMIN`이 채용 요청 문서일 때만 예외 |
| 기안 부서 | 관리자가 아니면 본인 소속 부서로만 기안 |
| 삭제 | 관리자만 |
| 처리 권한 | 지정 결재자 · 관리자 · 관리 범위 안의 `TEAM_ADMIN`(부서)·`PART_ADMIN`(파트) |
| 이력 | 모든 상태 변경을 `approval_histories`에 남긴다 |

## 채용

```
RecruitmentRequest(채용 요청)
   │  전자결재 문서로 상신 → 승인
   ▼
JobPosting(공고)  ← 승인 시 자동 생성. 본문은 코드가 조립한다
   │
   ▼
Applicant(지원자)
```

- 공고는 **사용자가 직접 쓰는 문서가 아닙니다.** 결재 승인 시
  `recruitment_service.process_approval`이 만들고 본문은 `_build_posting_content`가 조립합니다.
- 공고 수정은 `PATCH /job-postings/{id}`로 **`title`·`content`만** 받습니다.
  **`status`는 받지 않습니다** — AI나 클라이언트가 공고를 게시 상태로 바꾸는 경로를 차단합니다.
- 채용 요청의 선택지(고용형태·학력·지원방법·경력)는 `domain/recruitment_options.py`가 단일 출처이며
  `Literal`에서 목록을 파생시킵니다. 프론트의 `features/recruitment/recruitment-options.ts`에
  같은 목록이 있어 **한쪽만 고치면 런타임 422**가 납니다.
- 경력은 `신입` / `경력`(최소 년수 필수) / `경력무관` 중 하나입니다.
  코드값으로 해석되지 않는 과거 자유입력 값은 버리지 않고 원문 그대로 표시합니다.

**지원자 전형 단계**: `APPLIED` → `SCREENING` → `INTERVIEW` → `OFFERED` → `HIRED` 또는 `REJECTED`

- `HIRED`와 `REJECTED`는 종료 단계이며 이전 단계로 되돌릴 수 없습니다.
- `REJECTED`로 바꿀 때는 메모가 필수입니다.
- 등록·수정·삭제·단계 변경은 `SUPER_ADMIN`·`HR_ADMIN`만, `TEAM_ADMIN`은 본인 부서 공고의
  지원자 조회만 가능합니다. `PART_ADMIN`에게는 지원자 접근을 열지 않았습니다.
- 같은 공고에 같은 이메일은 중복 등록할 수 없습니다.

## 직원·조직과 근태

**조직은 2계층입니다**: `departments`(부서) → `teams`(부서 산하 **파트**, 예: `DEV_SW`/`DEV_HW`/`DEV_QA`).
`teams`는 "팀"이 아니라 파트를 뜻합니다.

**재직 상태**: `ACTIVE` · `ON_LEAVE` · `SCHEDULED` · `RESIGNED`
→ `ACTIVE`가 아니면 일일 근무 상태를 등록할 수 없습니다.

**일일 근무 상태** 12종: `WORKING` `REMOTE_WORK` `OUT_OF_OFFICE` `BUSINESS_TRIP` `ANNUAL_LEAVE`
`MORNING_HALF` `AFTERNOON_HALF` `SICK_LEAVE` `TRAINING` `OTHER` `OFF_WORK` `ABSENT`

| 규칙 | 내용 |
|---|---|
| 사유 필수 | `SICK_LEAVE`·`ABSENT`는 공개 사유가 없으면 422 |
| 휴직 사유 필수 | `ON_LEAVE`로 바꿀 때 사유 필요 |
| 비공개 상세 | 저장되지만 권한 없는 조회자에게는 응답에서 제거된다 |
| 이력 | 실제로 값이 바뀐 경우에만 `attendance_change_histories`에 남긴다 |
| 비활성화 | 최상위 직원 불가. 하위 직원이 있으면 관리자를 먼저 옮겨야 한다 |

**E2E 테스트 계정**(`E2E`로 시작하는 사번)은 일반 사용자의 목록과 대시보드 집계에서 제외됩니다
(`domain/test_accounts.py`).

## AI

**DB = 사실 / 사용자 입력 = 부족한 맥락 / AI = 문장화.** 자세한 제약은 [`AI_DESIGN.md`](AI_DESIGN.md).

- AI는 **어떤 상태도 바꾸지 않습니다.** 초안을 만들어도 문서가 생기지 않고 폼만 채웁니다.
- Context에 없는 값은 키 자체를 만들지 않습니다. `None`을 넣으면 AI가 "미정" 같은 문장을 지어냅니다.
- 채용 AI Context는 **결재 승인된 DB 값이 사용자 입력을 이깁니다.** 승인된 근무지를
  AI 패널에서 조용히 바꿔 끼울 수 없습니다.
- Provider 실패는 5xx가 아니라 `200 + success:false`입니다. 초안은 부가 기능이므로
  기존 작성 흐름을 막지 않습니다.
- 호출 한도는 사용자당·전역 두 겹입니다. **전역 한도가 실질 방어선**입니다.

## 확인 필요

- `CANCELLED` 결재 상태로 전이시키는 경로가 코드에서 확인되지 않습니다. 스키마에만 있습니다.
- `employees.role`과 `employee_accounts.role`의 통합 여부가 정해지지 않았습니다.
