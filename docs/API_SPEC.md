# API Specification

## Recruitment Poster (v0.5.7)

### POST /api/v1/recruitment-requests/{request_id}/poster

- 목적: 임시 저장 상태의 채용 요청에 포스터 파일을 첨부한다.
- 요청: Query `actor_id`, multipart field `poster`.
- 허용 형식: JPG, PNG, WEBP, PDF. 최대 5MB.
- 권한: 요청 작성자 또는 관리자. 상신 후에는 변경할 수 없다.
- 응답: 포스터 메타데이터가 포함된 채용 요청.
- 오류: 400(형식·크기), 403(권한), 409(상신 후 상태).

### GET /api/v1/recruitment-requests/{request_id}/poster

- 목적: 권한이 있는 직원이 첨부된 채용 포스터를 연다.
- 요청: Query `employee_id`.
- 응답: 원본 파일명과 MIME 형식을 유지한 파일 응답.
- 관련 테이블: `recruitment_requests`.

Base path는 `/api/v1`이다. 공통 조회 API와 전자결재 Router는 구현되었고, 나머지 모듈의 API는 이 문서의 계약을 기준으로 구현할 예정이다. 공통 오류는 현재 FastAPI의 `detail` 응답을 사용하며, 이후 `{code, message, details?, request_id?}` 형태로 확장할 수 있다. 현재 사용자 ID는 조회 시 `employee_id` query parameter, 상태 변경 시 요청 body의 `actor_id`로 전달하되 Service가 해당 직원과 역할을 저장소에서 다시 조회한다.

## API 목록

| 그룹 | Method / URL | 목적·요청 | 응답 / 역할 / 상태 코드 | 규칙·트랜잭션·테이블 |
|---|---|---|---|---|
| Health | `GET /health` | 프로세스 상태 | `{status}` / 전체 / 200 | DB deep health는 별도 검토 |
| Departments | `GET /departments` | 부서 목록, query `active?` | 부서 목록 / 전체 / 200 | `departments` |
| Employees | `GET /employees` | 샘플 직원 목록, query `department_id?, role?` | 직원 목록 / 전체 / 200 | `employees`, `departments` |
| Current User | `PUT /session/current-user` | body `{employee_id}` | 현재 직원·역할·접근 모듈 / 전체 / 200, 404, 409 | 활성 직원 재조회; 영속 세션 방식은 구현 시 결정 |
| Dashboard | `GET /dashboard` | 현재 역할의 업무 요약 | counts/tasks / 전체 / 200, 403 | 결재·채용·견적·알림 read transaction |
| Approvals | `GET /approvals` | query `employee_id?, status?` | 목록 / 역할별 / 200 | 관리자는 전체, 그 외 역할은 작성·결재 관련 문서만 조회, `approval_documents` |
| Approvals | `GET /approvals/{id}` | 결재와 이력 상세 | 상세 / 작성자·결재자·관리자 / 200,403,404 | approval/history |
| Approvals | `POST /approvals` | body `{document_type,title,content,department_id,author_id,approver_id}` | DRAFT / 작성 가능 역할 / 201,400 | 직원·부서 확인, 작성자≠결재자; 관리자는 모든 부서, 그 외 역할은 소속 부서만 기안; 문서와 초기 이력 transaction |
| Approvals | `PATCH /approvals/{id}` | body `{actor_id,title?,document_type?,content?,department_id?,approver_id?}` | 수정된 DRAFT / 작성자 / 200,400,403,409 | DRAFT와 작성자만 수정 가능 |
| Approvals | `DELETE /approvals/{id}` | query `{actor_id}` | 빈 응답 / 관리자 / 204,403,404 | 상태와 관계없이 관리자만 물리 삭제하며 `approval_histories`는 FK cascade로 함께 삭제 |
| Approvals | `POST /approvals/{id}/submit` | body `{actor_id,comment?}` | PENDING / 작성자 / 200,403,409 | DRAFT→PENDING, 이력 transaction |
| Approvals | `POST /approvals/{id}/approve` | body `{actor_id,comment?}` | APPROVED / 지정 결재자 / 200,403,409 | PENDING→APPROVED; 이력 원자 처리 |
| Approvals | `POST /approvals/{id}/reject` | body `{actor_id,comment}` | REJECTED / 지정 결재자 / 200,403,409,422 | PENDING→REJECTED; 반려 사유 필수 |
| Approvals | `POST /approvals/{id}/cancel` | body `{reason?}` | CANCELLED / 작성자 / 200,409 | DRAFT→CANCELLED |
| Recruitment Requests | `POST /recruitment-requests` | body 직무·인원·사유·부서 | DRAFT / 활성 직원 / 201,400 | `recruitment_requests` |
| Recruitment Requests | `GET /recruitment-requests` | query status/department | 목록 / 부서장·인사·관리자 / 200 | role scope |
| Recruitment Requests | `GET /recruitment-requests/{id}` | 상세 | 요청·결재·AI 링크 / 관련 역할 / 200,403,404 | 여러 테이블 read |
| Recruitment Requests | `POST /recruitment-requests/{id}/submit` | body `{approver_id,comment?}` | 요청 PENDING+결재 | 요청 작성자 / 200,403,409 | 요청·결재·이력·알림 transaction |
| Job Postings | `POST /recruitment-requests/{id}/job-posting` | body `{title,description}` | 공고 / 인사 / 201,403,409 | 요청 APPROVED, 1회만; posting transaction |
| Job Postings | `GET /job-postings` | query status? | 목록 / 관련 역할 / 200 | `job_postings` |
| Job Postings | `GET /job-postings/{id}` | 상세 | 공고 / 관련 역할 / 200,404 | posting |
| Applicants | `POST /job-postings/{id}/applicants` | body 이름·연락·경력 | APPLIED 지원자 / 인사 / 201,400,403 | posting 존재 확인 |
| Applicants | `GET /applicants` | query posting/stage | 목록 / 인사·관리자 / 200 | applicant |
| Applicants | `GET /applicants/{id}` | 상세 | 지원자+AI 링크 / 인사·관리자 / 200,404 | applicant/ai |
| Applicants | `POST /applicants/{id}/transition` | body `{stage}` | 변경된 지원자 / 인사 / 200,400,409 | 허용 단계 규칙; 합격 자동 결정 금지 |
| Customers | `POST /customers` | body 고객 정보 | 고객 / 영업·관리자 / 201,400,409 | `customers` |
| Customers | `GET /customers` | query search? | 목록 / 영업 / 200 | customer |
| Customers | `GET /customers/{id}` | 상세 | 고객·기회 요약 / 영업 / 200,404 | customer/opportunity |
| Products | `POST /products` | body code/name/default price | 상품 / 관리자 / 201,400,409 | product |
| Products | `GET /products` | query active? | 목록 / 영업·관리자 / 200 | product |
| Sales Opportunities | `POST /sales-opportunities` | body customer/title/status | 기회 / 영업 / 201,400,404 | customer/opportunity |
| Sales Opportunities | `POST /sales-opportunities/{id}/transition` | body `{status}` | 변경된 기회 / 소유 영업·관리자 / 200,409 | 허용 상태 전환 |
| Quotations | `POST /quotations` | body opportunity/valid_until/reason | DRAFT / 영업 / 201,400 | quotation |
| Quotations | `GET /quotations` | query status/customer? | 목록 / 영업·팀장·관리자 / 200 | role scope |
| Quotations | `GET /quotations/{id}` | 상세·서버 계산값 | 견적/항목/결재 / 관련 역할 / 200,404 | quotation/items |
| Quotations | `PUT /quotations/{id}/items` | body `{items:[product_id,quantity,unit_price]}` | 재계산 견적 | 소유 영업 / 200,400,409 | DRAFT 계열만; items+totals transaction |
| Quotations | `PATCH /quotations/{id}` | body discount_rate/reason/valid_until | 재계산 견적 | 소유 영업 / 200,400,409 | 서버 Decimal 계산, 기준 초과 상태 결정 |
| Quotations | `POST /quotations/{id}/request-approval` | body `{approver_id}` | 견적 PENDING_APPROVAL+결재 | 영업 / 200,403,409 | >기준, 자기 결재 금지; 결재·이력·알림 transaction |
| Quotations | `POST /quotations/{id}/confirm` | 없음 | CONFIRMED | 소유 영업 / 200,403,409 | ≤기준 또는 APPROVED만; 서버 재계산 transaction |
| AI Generations | `POST /ai-generations` | body `{feature_type,related_type,related_id,input}` | 생성 기록·결과 | 관련 업무 역할 / 201 또는 fallback 201 | 업무 존재·권한 확인; AI 실패가 업무 저장 rollback을 유발하지 않음 |
| AI Generations | `GET /ai-generations/{id}` | 생성 상세 | source/generated/final/status | 관련 역할 / 200,403,404 | ai |
| AI Generations | `PATCH /ai-generations/{id}/final-output` | body `{final_output}` | 수정 결과 | 관련 담당자 / 200,400,403 | generated 원본 보존 |
| AI Generations | `POST /ai-generations/{id}/retry` | 선택적 재실행 | 새 generation 권장 | 관련 담당자 / 201,409 | 기존 기록 덮어쓰지 않음 |
| Notifications | `GET /notifications` | query unread? | 현재 사용자 알림 | 전체 / 200 | recipient 강제 |
| Notifications | `POST /notifications/{id}/read` | 없음 | read_at | 수신자 / 200,403,404 | notification |

## 상태와 오류 기준

- `400`: 형식·범위 오류, `403`: 역할/소유권 위반, `404`: 대상 없음, `409`: 현재 상태와 명령 충돌
- 결재: DRAFT→PENDING, PENDING→APPROVED/REJECTED, DRAFT→CANCELLED만 허용
- 견적: DRAFT→APPROVAL_REQUIRED(기준 초과), APPROVAL_REQUIRED→PENDING_APPROVAL, PENDING_APPROVAL→APPROVED/REJECTED, APPROVED→CONFIRMED. 기준 이하는 DRAFT→CONFIRMED 가능
- 승인/반려에서 결재문서, 관련 업무, 이력, 알림은 한 트랜잭션이다.
## v0.5.0 구현 API

| Recruitment Requests | `DELETE /recruitment-requests/{id}?actor_id=` | 관리자만 삭제 가능. 연결된 공고·결재·이력·관련 알림도 같은 트랜잭션으로 삭제 |

관리자는 지정 결재자가 아니어도 `PENDING` 전자결재를 승인 또는 반려할 수 있다. 처리 이력에는 실제 관리자 ID가 기록된다.

| Group | API | 핵심 규칙 |
|---|---|---|
| Recruitment Requests | `POST /recruitment-requests` | 활성 직원이면 생성 가능하며 요청 부서는 등록된 부서인지 검증 |
| Recruitment Requests | `GET /recruitment-requests?employee_id=` | 요청자·결재자만, 인사·관리자는 전체 조회 |
| Recruitment Requests | `GET /recruitment-requests/{id}?employee_id=` | 역할 범위로 상세 조회 |
| Recruitment Requests | `POST /recruitment-requests/{id}/submit` | 요청·공통 결재·이력·알림을 함께 생성 |
| Job Postings | `GET /job-postings?employee_id=` | 승인으로 자동 생성된 공고 초안 목록 |

결재 승인·반려 API는 관련 유형이 `RECRUITMENT_REQUEST`이면 같은 트랜잭션에서 요청 상태와 공고/알림을 함께 갱신한다.
