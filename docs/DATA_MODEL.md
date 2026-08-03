# Data Model

## 직원 매뉴얼 MVP (v0.7.0)

`manual_categories`는 이름, 설명, 표시 순서를 관리합니다. `manuals`는 텍스트 원본인
제목·요약·본문과 대상 역할, 공개 상태(`DRAFT`, `PUBLISHED`), 중요 고정 여부를 보관합니다.
`slug`는 상세 페이지의 안정적인 식별자이며 유일합니다.

`manual_assets`는 매뉴얼별 이미지 또는 PDF URL을 표시 순서대로 연결합니다. MVP는 URL 등록만
지원하며 파일 업로드 저장소나 대용량 첨부파일은 포함하지 않습니다. 매뉴얼 삭제 시 연결된
asset는 함께 삭제되고, 카테고리에 매뉴얼이 남아 있으면 카테고리를 삭제할 수 없습니다.

- `manual_categories` 1:N `manuals`
- `manuals` 1:N `manual_assets`
- `manuals.created_by`, `manuals.updated_by`는 작성·수정한 직원의 선택적 참조입니다.

공개 매뉴얼은 모든 인증된 직원이 읽을 수 있으며 초안은 `SUPER_ADMIN`, `HR_ADMIN`에게만
노출됩니다. 초기 7개 카테고리와 15개 매뉴얼은 slug/name을 기준으로 갱신하므로 seed를 다시
실행해도 중복 생성되지 않습니다.

## Employee organization management (v0.6.0)

`departments` has unique code/name and display ordering. `teams` represents the
two development subteams (`DEV_SW`, `DEV_HW`) and belongs to a department.
`employees` references its department, optional team, and optional manager with
`RESTRICT` foreign keys. Employee list queries return department/team/manager
summaries; employee deletion is implemented as `employment_status=INACTIVE`.

Database runtime is Supabase PostgreSQL only; SQLite is not a supported application database.

## Supabase Auth employee accounts (v0.6.2)

`employee_accounts` is the application-side link between a Supabase Auth user
and exactly one `employees` record. `auth_user_id` and `employee_id` are both
unique, which prevents duplicate links. The application role is stored in
`employee_accounts.role`; it is intentionally separate from the employee's job
role and is used by the upcoming JWT-based authorization layer.

The Auth seed reconciles all employee records on every run: it reuses Auth users
by email, creates only missing Auth users, and synchronizes the account role and
active flag. Seed passwords are read only from the environment and are never
persisted or logged by the application.

## Attendance records (v0.6.1)

`attendance_records` stores one daily work status per employee. The composite
unique constraint on `(employee_id, work_date)` makes daily seed data idempotent.
Long-lived employment status remains on `employees.employment_status`.
Daily and employment-status reasons are separated into `reason_category`,
`reason_summary`, and `private_note`. Attendance reasons use these fields on
`attendance_records`; employment-status reasons use their `employment_status_*`
counterparts on `employees`. The records also retain the reason registrant and time.
`reason_summary` is visible to all users, while `private_note` for sick leave and
long-term leave is returned only to administrators and HR managers.

### Planned attendance extensions

The current `AttendanceRecord.employee_id` and `work_date` unique pair is the
stable parent for the next two tables; neither table is created in this change.

- `attendance_change_histories` should reference `attendance_records.id` and
  store the before/after status, reason fields, actor, and timestamp.
- `employee_leave_periods` should reference `employees.id` and hold the start,
  end, status reason, and approval metadata for multi-day leave.

Daily records must remain independent from leave periods so a historical daily
record can be preserved even when a leave period is later corrected.

## 채용 포스터 메타데이터 (v0.5.7)

`recruitment_requests`는 요청당 하나의 채용 포스터를 선택적으로 연결한다. `poster_original_name`, `poster_stored_name`, `poster_content_type`, `poster_size` 컬럼은 원본 파일명, 서버 내부 저장명, MIME 형식, 바이트 크기를 구분한다. 실제 파일은 프로토타입 로컬 개발 저장소에 두며, 요청 삭제 시 함께 제거한다. 생성된 `job_postings`는 연결된 채용 요청을 통해 이 메타데이터를 조회하므로 별도 중복 컬럼을 두지 않는다.

## 공통 원칙

- PostgreSQL의 timezone-aware `timestamptz`를 사용하고 서버/DB 기준 UTC 저장, 화면에서 지역 시간으로 표시한다.
- 금액은 `NUMERIC(18,2)`, 할인율은 `NUMERIC(5,2)` 후보이며 Python `Decimal`과 대응한다.
- PK는 초기 구현 시 UUID를 우선 검토한다. 모든 업무 테이블에 `created_at`, `updated_at`을 둔다.
- Soft Delete를 일괄 적용하지 않는다. 감사가 중요한 결재·견적은 상태 변경으로 보존하고, 기준 데이터는 실제 요구가 생길 때 비활성 플래그를 검토한다.
- 상태값은 Python Enum과 DB 제약의 균형을 migration에서 검토한다.
- 실제 배포 대상은 Supabase PostgreSQL이다. 연결 정보가 없는 로컬 개발에서는 동일 ORM 모델의 파일 기반 SQLite를 fallback으로 사용하며 배포 DB로 사용하지 않는다.

## 테이블 요약

| 테이블 / 목적 | 주요 컬럼과 자료형 후보 | 키·제약·관계 | 상태·삭제·확장 |
|---|---|---|---|
| `departments` 조직 기준 | `id uuid`, `code varchar`, `name varchar`, timestamps | PK id, UQ code; employees 1:N | 물리 삭제 전 참조 확인; 계층 부서는 이후 |
| `employees` 샘플 사용자·역할 | `id uuid`, `employee_no varchar`, `name`, `email`, `role varchar`, `department_id uuid`, `is_active bool`, timestamps | UQ employee_no/email, FK department RESTRICT | `ADMIN`은 전 부서 기안 가능, 그 외 역할은 소속 부서 기안; 비활성화 사용; 다중 역할은 이후 |
| `notifications` 인앱 알림 | `id`, `recipient_id`, `type`, `message`, `related_type`, `related_id`, `read_at`, timestamps | FK employee CASCADE 정책은 구현 시 검토 | 읽음 상태; 실시간/채널 확장 |
| `approval_documents` 공통 결재 | `id`, `document_type`, `title`, `content text`, `author_id`, `approver_id`, `status`, `decision_comment`, `submitted_at`, `processed_at`, `related_type`, `related_id`, timestamps | 직원 FK 2개; 관련 업무는 polymorphic 참조라 Service 무결성 필요. `(related_type,related_id)` index | 관리자만 상태와 관계없이 물리 삭제, 일반 역할은 삭제 불가; DRAFT/PENDING/APPROVED/REJECTED/CANCELLED; 다단계는 이후 |
| `approval_histories` 변경 감사 | `id`, `approval_document_id`, `actor_id`, `action`, `from_status`, `to_status`, `comment`, `created_at` | FK approval/employee; 수정·삭제 금지 원칙 | 행동 이력; IP/메타데이터 이후 |
| `recruitment_requests` 채용 요청 | `id`, `requester_id`, `department_id`, `position_title`, `headcount int`, `reason text`, `status`, `approval_document_id`, timestamps | FK 직원/부서/결재, UQ approval_document_id | DRAFT/PENDING/APPROVED/REJECTED/CANCELLED; 상태 보존 |
| `job_postings` 승인 요청 기반 공고 | `id`, `recruitment_request_id`, `title`, `description`, `status`, timestamps | FK request, UQ recruitment_request_id(프로토타입 1:1) | DRAFT/OPEN/CLOSED; 다중 공고는 이후 |
| `applicants` 공고 지원자 | `id`, `job_posting_id`, `name`, `contact`, `career_text`, `stage`, timestamps | FK posting; 실제 개인정보 금지, 프로토타입 중복 제약 생략 | APPLIED/SCREENING/INTERVIEW/OFFERED/HIRED/REJECTED; 삭제 대신 상태·가상 데이터 |
| `customers` 고객 | `id`, `name`, `business_no_candidate`, `contact_name`, `contact_email`, timestamps | UQ는 샘플 데이터 정책 확정 후; opportunities 1:N | 초기 물리 삭제 제한; 주소/담당자 분리 이후 |
| `products` 견적 상품 | `id`, `code`, `name`, `default_unit_price numeric`, `is_active`, timestamps | UQ code; items 1:N | 비활성화; 가격 이력 이후 |
| `sales_opportunities` 영업기회 | `id`, `customer_id`, `owner_id`, `title`, `status`, timestamps | FK customer/employee; quotations 1:N | LEAD/QUALIFIED/PROPOSAL/WON/LOST 후보; 최소 단계만 구현 |
| `quotations` 견적 헤더·합계 | `id`, `opportunity_id`, `owner_id`, `status`, `discount_rate numeric`, `discount_reason`, `subtotal numeric`, `discount_amount numeric`, `total_amount numeric`, `approval_document_id`, `valid_until date`, timestamps | FK opportunity/employee/approval, UQ approval_document_id nullable | DRAFT/APPROVAL_REQUIRED/PENDING_APPROVAL/APPROVED/REJECTED/CONFIRMED/CANCELLED; 삭제 대신 상태 |
| `quotation_items` 견적 항목 스냅샷 | `id`, `quotation_id`, `product_id`, `product_name`, `quantity numeric`, `unit_price numeric`, `line_amount numeric`, timestamps | FK quotation CASCADE(초안 삭제 시), product RESTRICT; check 양수 | 상품명·가격 스냅샷; 세금은 이후 |
| `ai_generations` 모든 AI 실행 | `id`, `feature_type`, `related_type`, `related_id`, `source_input jsonb/text`, `generated_output jsonb/text`, `final_output jsonb/text`, `provider`, `model_name`, `success bool`, `error_message`, timestamps | polymorphic 업무 참조는 Service 확인; 관련 복합 index | 삭제보다 감사 보존; token/비용/버전 이후 |

## 핵심 관계

- Department 1:N Employee, Employee 1:N 작성/결재 ApprovalDocument
- ApprovalDocument 1:N ApprovalHistory
- RecruitmentRequest 1:0..1 ApprovalDocument, 1:0..1 JobPosting, JobPosting 1:N Applicant
- Customer 1:N SalesOpportunity 1:N Quotation 1:N QuotationItem; Product 1:N QuotationItem
- Quotation 1:0..1 ApprovalDocument
- 각 업무 엔티티 1:N AIGeneration은 `related_type/id`로 연결한다.

## 설계 검토

AI 기능별 별도 테이블은 컬럼과 조회 규칙이 반복되므로 프로토타입에서는 공통 `ai_generations`가 적절하다. 다형 참조는 DB FK를 직접 걸기 어렵다는 단점이 있어 Service 검증과 index가 필요하다. 결재의 관련 업무 참조도 같은 주의가 필요하며, 규모가 커지면 명시적 연결 테이블을 재검토한다.

프로토타입에서는 조직 계층, 복수 역할, 지원 단계 이력 전용 테이블, 견적 버전·세금, 고객 담당자 분리, 일반화된 soft delete를 생략한다.

## 현재 구현

`20260730_0001_approval_flow.py`에서 `departments`, `employees`, `approval_documents`, `approval_histories`와 상태 CHECK, FK, 조회 index, 최초 샘플 조직 데이터를 생성한다. `20260730_0002_add_sample_departments.py`는 개발팀과 재무팀을 샘플 부서로 추가한다. `20260730_0003_make_project_owner_admin.py`는 샘플 프로젝트 운영자 김민성을 관리자로 전환한다. 나머지 표의 테이블은 아직 설계 상태다.
## v0.5.0 구현 메모

- 채용 요청 삭제는 관리자 전용이다. 요청과 1:1 공고, 연결된 결재 문서·이력, 관련 알림을 함께 물리 삭제한다.

- 채용 요청은 요청 부서·요청자·결재자와 1개의 전자결재 문서를 연결한다.
- 채용 요청 상태는 `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `POSTING_CREATED`이며, 결재 문서 상태와 분리한다.
- 채용공고는 요청당 하나만 허용한다. 승인 처리에서 템플릿 초안을 생성한 뒤 요청 상태를 `POSTING_CREATED`로 기록한다.
- `20260731_0004_recruitment_flow.py`는 결재 관련 업무 식별자, `notifications`, `recruitment_requests`, `job_postings`, 부서장 시연 직원을 추가한다.
