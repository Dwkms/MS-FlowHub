# API

현재 존재하는 엔드포인트 지도입니다. 요청·응답 스키마의 단일 출처는 `backend/app/schemas/`이고,
서버를 띄우면 `/docs`(Swagger)에서 실제 스키마를 볼 수 있습니다.
여기에 필드를 복사해 두지 않습니다 — 코드와 어긋나기 때문입니다.

버전별 변경 이력은 [`archive/API_SPEC_LEGACY.md`](archive/API_SPEC_LEGACY.md)에 보존돼 있습니다.

## 공통

- Base path: **`/api/v1`** (`app/api/router.py`)
- 인증: `Authorization: Bearer <Supabase access token>`. 미인증은 401, 권한 부족은 403
- 프론트엔드는 `/api/*`로 호출하고 Next.js rewrite가 백엔드로 넘깁니다
- 오류 응답은 FastAPI 기본 형식 `{"detail": "..."}` 입니다
- Health check는 `/health` (prefix 없음)

## 인증 · 공통

| Method | Path | 설명 |
|---|---|---|
| GET | `/auth/me` | 현재 로그인 직원과 역할 |
| GET | `/auth/permissions` | 접근 가능 모듈 |
| POST | `/auth/logout` | 로그아웃 |
| GET | `/dashboard` | 개인 지표 · 최근 업무 · (관리자) 분석 |
| GET | `/departments` | 부서 목록 |
| GET | `/employee-options` | 결재자 선택용 직원 목록 |

## 직원 · 조직 · 근태

| Method | Path | 권한 | 설명 |
|---|---|---|---|
| GET | `/employees` | 역할별 범위 | 목록. 검색·부서·재직·근무상태 필터, 페이지네이션 |
| GET | `/employees/{id}` | 역할별 범위 | 상세. 비공개 사유는 권한 없으면 제거됨 |
| POST | `/employees` | 관리자 | 등록 |
| PATCH | `/employees/{id}` | 관리자 | 수정 |
| PATCH | `/employees/{id}/role` | `SUPER_ADMIN` | 역할 변경 |
| DELETE | `/employees/{id}` | 관리자 | 비활성화 |
| PUT | `/employees/{id}/attendance` | 본인 또는 관리 범위 | 일일 근무 상태 |
| PATCH | `/employees/{id}/employment-status-reason` | 관리자 | 재직 상태 사유 |
| GET | `/organization` | 로그인 | 조직도 |

역할별 관리 범위는 [`DOMAIN.md`](DOMAIN.md#관리-범위)를 보세요.

## 전자결재

| Method | Path | 설명 |
|---|---|---|
| GET | `/approvals` | 목록. 관리자가 아니면 본인 관련 문서만 |
| GET | `/approvals/{id}` | 상세와 이력 |
| POST | `/approvals` | 작성 (`DRAFT`) |
| PATCH | `/approvals/{id}` | 수정. `DRAFT` + 작성자만 |
| DELETE | `/approvals/{id}` | 삭제. 관리자만 |
| POST | `/approvals/{id}/submit` | 상신 |
| POST | `/approvals/{id}/approve` | 승인 |
| POST | `/approvals/{id}/reject` | 반려. 사유 필수 |

상태 전이와 권한 규칙은 [`DOMAIN.md`](DOMAIN.md#전자결재).

## 채용 · 지원자

| Method | Path | 설명 |
|---|---|---|
| GET | `/recruitment-requests` | 채용 요청 목록 |
| POST | `/recruitment-requests` | 채용 요청 생성 |
| GET | `/recruitment-requests/{id}` | 상세 |
| DELETE | `/recruitment-requests/{id}` | 삭제 |
| POST | `/recruitment-requests/{id}/submit` | 전자결재로 상신 |
| POST | `/recruitment-requests/{id}/job-posting` | 공고 생성 |
| POST · GET | `/recruitment-requests/{id}/poster` | 포스터 업로드 · 조회 (Supabase Storage) |
| GET | `/job-postings` | 공고 목록 |
| PATCH | `/job-postings/{id}` | 공고 수정. **`title`·`content`만. `status`는 받지 않음** |
| POST | `/job-postings/{id}/applicants` | 지원자 등록 |
| GET | `/applicants` | 지원자 목록. 공고·단계·검색 필터 |
| GET · PATCH · DELETE | `/applicants/{id}` | 상세 · 수정 · 삭제 |
| POST | `/applicants/{id}/stage` | 전형 단계 변경 |

## 매뉴얼 · FAQ · AX

| Method | Path | 설명 |
|---|---|---|
| GET | `/manuals` | 목록. 역할별 공개 범위 적용 |
| GET · PATCH · DELETE | `/manuals/{slug}` | 상세 · 수정 · 삭제 |
| POST | `/manuals` | 등록 |
| GET | `/manuals/categories` | 카테고리 목록 |
| PATCH · DELETE | `/manuals/categories/{id}` | 카테고리 수정 · 삭제 |
| GET | `/faqs` | FAQ 목록 |
| POST | `/ax/chat` | AX 직원 도우미 질의. 매뉴얼·FAQ 기반 |

## AI

| Method | Path | 설명 |
|---|---|---|
| POST | `/ai/approval-drafts` | 전자결재 초안 생성 |
| POST | `/ai/job-posting-drafts` | 채용공고 초안 생성 |
| POST | `/ai/job-posting-posters` | 채용 포스터 이미지 2안 생성 |
| PATCH | `/ai/generations/{id}/final` | 사용자가 최종 채택한 결과 기록 |

**Provider 실패는 5xx가 아니라 `200 + success:false`입니다.** 초안은 부가 기능이므로 기존 작성
흐름을 막지 않습니다. 호출 한도 초과는 429입니다. 제약은 [`AI_DESIGN.md`](AI_DESIGN.md).

## 상태 코드

| 코드 | 의미 |
|---|---|
| 400 | 참조 대상 없음, 소속 부서 불일치 등 요청 내용 오류 |
| 401 | 토큰 없음·만료·검증 실패 |
| 403 | 역할 또는 관리 범위 밖 |
| 404 | 대상 없음 |
| 409 | 상태 충돌 (하위 직원 존재, 재직 상태와 근무 상태 불일치 등) |
| 422 | 스키마 검증 실패, 필수 사유 누락 |
| 429 | AI 호출 한도 초과 |
