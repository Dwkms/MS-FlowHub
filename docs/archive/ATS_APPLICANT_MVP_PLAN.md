# ATS 지원자 관리 MVP 기획

> 상태: 착수 전 기획 문서입니다. 이 MVP는 2026-08-05에 구현·검증까지 완료됐습니다. 실제 구현 상태는 `docs/DATA_MODEL.md`(ATS 지원자 관리)와 `docs/API_SPEC.md`, 변경 이력은 `UPDATELOG.md`를 기준으로 확인하세요.

기준일: 2026-08-05  
연결 에픽: `MFH-4 채용 관리`

## 1. 목표와 경계

승인된 채용 요청으로 생성된 채용공고에 지원자를 연결하고, 인사 담당자가 채용 단계를 일관되게 관리한다.

이번 MVP는 내부 운영 화면만 제공한다. 외부 공개 지원 페이지, 지원자 로그인, AI 평가·자동 합격 판정, 이력서 파일 업로드는 포함하지 않는다. 지원자 정보는 HR이 수동으로 등록한다.

## 2. 사용자와 권한

| 역할 | 목록·상세 조회 | 등록·수정·단계 변경 | 삭제 |
|---|---|---|---|
| `SUPER_ADMIN` | 전체 | 가능 | 가능 |
| `HR_ADMIN` | 전체 | 가능 | 가능 |
| `TEAM_ADMIN` | 본인 부서 채용공고의 지원자만 | 불가 | 불가 |
| `EMPLOYEE` | 불가 | 불가 | 불가 |

지원자 정보는 개인정보이므로 서버가 공고의 요청 부서와 조회자의 소속 부서를 비교해 조회 범위를 제한한다.

## 3. 업무 흐름

1. HR 또는 SUPER_ADMIN이 생성된 채용공고에서 `지원자 관리`를 선택한다.
2. 지원자 이름, 이메일, 전화번호(선택), 경력 요약을 입력해 등록한다.
3. 시스템은 해당 공고의 `APPLIED` 단계 지원자와 최초 단계 이력을 한 트랜잭션으로 저장한다.
4. HR 또는 SUPER_ADMIN이 지원자를 열어 `SCREENING`, `INTERVIEW`, `OFFERED`, `HIRED`, `REJECTED` 단계로 변경한다.
5. 단계 변경 시 변경자·변경 시각·메모를 이력으로 남긴다. `REJECTED`는 메모를 필수로 한다.

## 4. 데이터 모델

### `applicants`

| 컬럼 | 설명 |
|---|---|
| `id` | UUID 문자열 PK |
| `job_posting_id` | `job_postings.id` FK |
| `name` | 지원자 이름 |
| `email` | 소문자로 정규화한 이메일 |
| `phone` | 선택 전화번호 |
| `career_summary` | 경력·지원 메모 텍스트 |
| `stage` | 현재 채용 단계 |
| `created_by_id` | 수동 등록한 HR 또는 관리자 |
| `created_at`, `updated_at` | 생성·수정 시각 |

같은 공고에 동일 이메일을 중복 등록하지 않도록 `(job_posting_id, email)` 유니크 제약을 둔다. 다른 공고에는 같은 지원자를 별도 등록할 수 있다.

### `applicant_stage_histories`

| 컬럼 | 설명 |
|---|---|
| `id` | UUID 문자열 PK |
| `applicant_id` | `applicants.id` FK |
| `from_stage`, `to_stage` | 이전·변경 단계 |
| `note` | 단계 변경 메모 |
| `actor_id` | 변경한 HR 또는 관리자 |
| `created_at` | 변경 시각 |

지원자 삭제 시 단계 이력도 함께 삭제한다. 채용공고 삭제 시 연결 지원자와 이력도 함께 삭제해 기존 관리자 삭제 흐름과 일치시킨다.

## 5. 단계 규칙

`APPLIED` → `SCREENING` → `INTERVIEW` → `OFFERED` → `HIRED`를 기본 흐름으로 사용한다. 어느 진행 단계에서든 `REJECTED`로 변경할 수 있다.

- `HIRED`, `REJECTED`는 종료 단계다.
- 종료 단계의 재개·되돌리기는 이번 MVP에서 제공하지 않는다.
- `REJECTED` 변경에는 메모를 필수로 한다.
- AI가 단계·합격 여부를 자동으로 결정하지 않는다.

## 6. 화면 구성

### 지원자 목록 `/applicants`

- 채용공고 선택, 단계 필터, 이름·이메일 검색
- 이름, 지원 공고, 현재 단계, 최근 변경일 표시
- HR·관리자만 `지원자 등록` 버튼 표시
- TEAM_ADMIN은 본인 부서 범위 안에서 조회 전용

### 지원자 상세

- 기본 정보와 경력 요약
- 현재 단계 배지
- 단계 변경 폼(HR·관리자만)
- 최신순 단계 변경 이력

### 채용공고 연계

- 기존 채용공고 카드·상세에 지원자 수와 `지원자 관리` 진입 버튼 추가

## 7. API 초안

| Method | URL | 역할 |
|---|---|---|
| `GET` | `/api/v1/applicants?job_posting_id=&stage=&search=&page=` | 역할 범위 내 목록 |
| `POST` | `/api/v1/job-postings/{job_posting_id}/applicants` | HR·관리자 등록 |
| `GET` | `/api/v1/applicants/{applicant_id}` | 역할 범위 내 상세 |
| `PATCH` | `/api/v1/applicants/{applicant_id}` | HR·관리자 기본 정보 수정 |
| `POST` | `/api/v1/applicants/{applicant_id}/stage` | HR·관리자 단계 변경 |
| `DELETE` | `/api/v1/applicants/{applicant_id}` | HR·관리자 중복·오등록 정리 |

모든 API는 Bearer 토큰에서 역할과 직원 정보를 해석한다. Router는 의존성·응답만 맡고, 권한·단계 규칙은 Service, DB 접근은 Repository에 둔다.

## 8. 이번 MVP 제외 범위

- 외부 공개 지원 URL, 지원자 회원가입·로그인
- 이력서·포트폴리오 파일 업로드
- 이메일 발송, 면접 일정, 평가표, 댓글
- AI 요약·질문 생성·자동 평가·자동 합격 판정
- 종료 단계 재개, 복수 채용 담당자, 개인정보 보존 기간 자동화

## 9. 완료 기준과 검증

- 지원자 등록·목록 검색·공고/단계 필터·상세 조회가 동작한다.
- 같은 공고에 동일 이메일을 중복 등록할 수 없다.
- 단계 변경과 이력이 하나의 트랜잭션으로 저장된다.
- `REJECTED` 메모 필수와 종료 단계 재변경 차단을 검증한다.
- 역할별 조회 범위 및 수정·삭제 차단을 백엔드 API 테스트로 검증한다.
- Alembic upgrade/downgrade, seed 재실행, Frontend lint/build, Backend Ruff/pytest를 통과한다.

## 10. 다음 확장

Supabase Storage 전환 후 `applicant_documents` 테이블과 이력서 파일 첨부를 추가한다. 그 뒤에 면접 일정과 평가표를 검토하며, AI는 인사 담당자의 검토용 초안만 제공한다.
