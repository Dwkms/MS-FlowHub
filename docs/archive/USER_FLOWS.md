# User Flows

> 상태: 채용 요청·전자결재 흐름 일부만 현재 구현되어 있습니다. 지원자·AI 관련 흐름은 미래 설계이며, 현재 API 계약은 `API_SPEC.md`를 기준으로 합니다.

표의 API는 설계 초안이다. 모든 명령은 FastAPI 서비스에서 현재 직원·역할과 상태를 확인한다.

## 시나리오 1: 채용 업무

| 단계 | 역할 / 화면 | 사용자 입력 | API 요청 | DB 변경 | 성공 결과 | 실패 가능 상황 |
|---|---|---|---|---|---|---|
| 1 역할 선택 | 사용자 선택 / 헤더 | 부서장 직원 ID | `PUT /api/v1/session/current-user` | 프로토타입 세션 컨텍스트 | 부서장 권한 표시 | 직원 없음·비활성 |
| 2 요청 작성 | 부서장 / 채용 요청 작성 | 직무, 인원, 사유 | `POST /api/v1/recruitment-requests` | `recruitment_requests` DRAFT | 요청 저장 | 필수값·권한 오류 |
| 3 사유 요약 | 부서장 / 요청 상세 | 요청 ID | `POST /api/v1/ai-generations` 기능 `RECRUITMENT_REASON_SUMMARY` | `ai_generations` | Mock/LLM 요약 표시 | timeout; 요청은 유지하고 fallback 안내 |
| 4 공고 초안 | 부서장 / 요청 상세 | 요청 내용 | 같은 API, 기능 `JOB_POSTING_DRAFT` | `ai_generations` | 수정 가능한 초안 | 생성 실패·입력 부족 |
| 5 결재 상신 | 부서장 / 요청 상세 | 결재자, 의견 | `POST /api/v1/recruitment-requests/{id}/submit` | 결재문서 PENDING, 이력, 요청 상태, 알림 | 인사 담당자 대기함 표시 | 자기 결재·잘못된 상태 |
| 6 역할 전환 | 인사 / 헤더 | 인사 담당자 ID | 현재 사용자 API | 세션 컨텍스트 | 인사 메뉴 표시 | 역할 불일치 |
| 7 문서 확인 | 인사 / 결재 상세 | 결재 ID | `GET /api/v1/approvals/{id}` | 없음 | 요청과 AI 참고 결과 조회 | 조회 권한·문서 없음 |
| 8 승인 | 인사 / 결재 상세 | 승인 의견 | `POST /api/v1/approvals/{id}/approve` | 문서 APPROVED, 이력, 요청 승인, 알림 | 승인 완료 | 이미 처리·결재자 불일치 |
| 9 공고 생성 | 인사 / 채용 요청 상세 | 제목·게시 내용 확인 | `POST /api/v1/recruitment-requests/{id}/job-posting` | `job_postings` | 요청과 연결된 공고 | 미승인·중복 생성 |
| 10 지원자 등록 | 인사 / 공고 상세 | 이름, 연락 식별정보, 경력 | `POST /api/v1/job-postings/{id}/applicants` | `applicants` APPLIED | 지원자 상세 | 공고 없음·입력 오류 |
| 11 단계 변경 | 인사 / 지원자 상세 | 목표 단계 | `POST /api/v1/applicants/{id}/transition` | applicant stage | 새 단계와 이력성 수정시각 | 허용되지 않은 단계 |
| 12 경력 요약 | 인사 / 지원자 상세 | 입력된 경력 | AI 생성 API, `APPLICANT_CAREER_SUMMARY` | `ai_generations` | 검토 가능한 요약 | 개인정보 과다 입력·실패 |
| 13 면접 질문 | 인사 / 지원자 상세 | 직무·경력 | AI 생성 API, `INTERVIEW_QUESTIONS_DRAFT` | `ai_generations` | 질문 초안 | 편향된 출력·실패 |
| 14 결과 수정 | 인사 / AI 결과 편집 | 최종 문안 | `PATCH /api/v1/ai-generations/{id}/final-output` | `final_output` | 원본 생성물과 수정본 구분 | 빈 결과·권한 오류 |

AI 결과는 합격·불합격을 자동 결정하거나 지원자를 평가·순위화하지 않는다.

## v0.5.0 구현 흐름: 채용 요청 → 결재 → 공고

1. 부서장 또는 관리자가 채용 요청을 임시 저장한다. 요청자는 DB의 직원 역할로 검증한다.
2. 요청자가 상신하면 공통 `approval_documents` 문서와 이력이 생성되고, 요청은 `PENDING_APPROVAL`이 된다.
3. 지정 결재자가 승인하면 전자결재는 `APPROVED`, 요청은 `POSTING_CREATED`가 되며 템플릿 기반 공고 초안이 하나 생성된다.
4. 지정 결재자가 반려하면 전자결재와 요청은 각각 `REJECTED`가 되고 공고는 생성하지 않는다.
5. 승인·반려, 이력, 요청 상태, 공고, 알림은 하나의 DB 트랜잭션으로 처리한다.
