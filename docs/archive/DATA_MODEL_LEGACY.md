# Data Model — 과거 설계 기록 (Legacy)

> 이 문서는 `docs/DATA_MODEL.md`가 2026-08-05에 현재 구현 기준으로 재정리되면서, 실제 Supabase 스키마에는 없는 과거 설계 초안과 미구현 확장 계획을 보존하기 위해 분리한 기록입니다. 현재 데이터 모델은 `docs/DATA_MODEL.md`를 참고하세요.

## 과거 확장 데이터 모델 초안 (미구현 항목 포함)

> 아래 표의 AI·지원자 관련 테이블과 SQLite fallback 설명은 과거 설계 기록입니다. `applicants`, `applicant_stage_histories`는 이후 실제로 구현되어 현재 `docs/DATA_MODEL.md`에 반영되었고, `ai_generations`는 아직 구현되지 않았습니다.

| 테이블 / 목적 | 주요 컬럼과 자료형 후보 | 키·제약·관계 | 상태·삭제·확장 |
|---|---|---|---|
| `departments` 조직 기준 | `id uuid`, `code varchar`, `name varchar`, timestamps | PK id, UQ code; employees 1:N | 물리 삭제 전 참조 확인; 계층 부서는 이후 |
| `employees` 샘플 사용자·역할 | `id uuid`, `employee_no varchar`, `name`, `email`, `role varchar`, `department_id uuid`, `is_active bool`, timestamps | UQ employee_no/email, FK department RESTRICT | `ADMIN`은 전 부서 기안 가능, 그 외 역할은 소속 부서 기안; 비활성화 사용; 다중 역할은 이후 |
| `notifications` 인앱 알림 | `id`, `recipient_id`, `type`, `message`, `related_type`, `related_id`, `read_at`, timestamps | FK employee CASCADE 정책은 구현 시 검토 | 읽음 상태; 실시간/채널 확장 |
| `approval_documents` 공통 결재 | `id`, `document_type`, `title`, `content text`, `author_id`, `approver_id`, `status`, `decision_comment`, `submitted_at`, `processed_at`, `related_type`, `related_id`, timestamps | 직원 FK 2개; 관련 업무는 polymorphic 참조라 Service 무결성 필요. `(related_type,related_id)` index | 관리자만 상태와 관계없이 물리 삭제, 일반 역할은 삭제 불가; DRAFT/PENDING/APPROVED/REJECTED/CANCELLED; 다단계는 이후 |
| `approval_histories` 변경 감사 | `id`, `approval_document_id`, `actor_id`, `action`, `from_status`, `to_status`, `comment`, `created_at` | FK approval/employee; 수정·삭제 금지 원칙 | 행동 이력; IP/메타데이터 이후 |
| `recruitment_requests` 채용 요청 | `id`, `requester_id`, `department_id`, `position_title`, `headcount int`, `reason text`, `status`, `approval_document_id`, timestamps | FK 직원/부서/결재, UQ approval_document_id | DRAFT/PENDING/APPROVED/REJECTED/CANCELLED; 상태 보존 |
| `job_postings` 승인 요청 기반 공고 | `id`, `recruitment_request_id`, `title`, `description`, `status`, timestamps | FK request, UQ recruitment_request_id(프로토타입 1:1) | DRAFT/OPEN/CLOSED; 다중 공고는 이후 |
| `applicants` 공고 지원자 | 이후 실제로 구현됨 | - | 현재 상태는 `docs/DATA_MODEL.md`의 ATS 지원자 관리 참고 |
| `ai_generations` 모든 AI 실행 | `id`, `feature_type`, `related_type`, `related_id`, `source_input jsonb/text`, `generated_output jsonb/text`, `final_output jsonb/text`, `provider`, `model_name`, `success bool`, `error_message`, timestamps | polymorphic 업무 참조는 Service 확인; 관련 복합 index | 삭제보다 감사 보존; token/비용/버전 이후 |

## 설계 검토 (과거)

AI 기능별 별도 테이블은 컬럼과 조회 규칙이 반복되므로 프로토타입에서는 공통 `ai_generations`가 적절하다. 다형 참조는 DB FK를 직접 걸기 어렵다는 단점이 있어 Service 검증과 index가 필요하다. 결재의 관련 업무 참조도 같은 주의가 필요하며, 규모가 커지면 명시적 연결 테이블을 재검토한다.

프로토타입에서는 조직 계층, 복수 역할, 지원 단계 이력 전용 테이블(이후 구현됨), 일반화된 soft delete를 생략한다.

## 초기 migration 진행 기록 (과거 서술)

`20260730_0001_approval_flow.py`에서 `departments`, `employees`, `approval_documents`, `approval_histories`와 상태 CHECK, FK, 조회 index, 최초 샘플 조직 데이터를 생성한다. `20260730_0002_add_sample_departments.py`는 개발팀과 재무팀을 샘플 부서로 추가한다. `20260730_0003_make_project_owner_admin.py`는 샘플 프로젝트 운영자 김민성을 관리자로 전환한다.

> 이후 모든 migration의 진행 기록은 `UPDATELOG.md`와 `backend/migrations/versions/`를 기준으로 확인합니다.

## 근태 확장 계획 초안 (미구현)

현재 `AttendanceRecord.employee_id`와 `work_date` unique pair가 다음 확장의 기준 키가 될 예정이며, 아래 테이블은 아직 생성되지 않았습니다.

- `employee_leave_periods`: `employees.id`를 참조하고 여러 날에 걸친 휴가의 시작일, 종료일, 상태 사유, 승인 메타데이터를 보관하는 용도로 검토되었습니다.

일별 근태 기록은 휴가 기간(leave period)과 독립적으로 유지되어야 하며, 이후 휴가 기간이 정정되더라도 과거 일별 기록은 그대로 보존되어야 한다는 원칙이 이 설계의 전제입니다.
