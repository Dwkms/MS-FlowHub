# MS FlowHub 현재 구현 요약

작성일: 2026-07-31

## 1. 현재 구조

- 프런트엔드는 공통 API Client를 통해 FastAPI를 호출한다.
- FastAPI Router는 요청과 응답을 담당하고, 업무 규칙은 Service, DB 접근은 Repository가 담당한다.
- 백엔드는 `DATABASE_URL`이 있으면 SQLAlchemy와 Psycopg 3를 통해 Supabase PostgreSQL을 사용한다.
- 프런트엔드의 `localStorage`는 현재 선택한 사용자 정보만 저장하며 업무 데이터 저장소가 아니다.
- 대시보드 API 실패 시 표시되는 mock 데이터는 화면 fallback일 뿐 실제 저장 데이터가 아니다.

## 2. 지금까지 구현된 업무

- 공통 조직 데이터: 부서와 직원, 역할 기반 샘플 사용자
- 전자결재: 문서 작성·수정·상신·승인·반려·취소·이력·알림
- ATS Lite: 채용 요청 작성·조회·상신, 승인 기반 채용공고 생성·조회
- 채용 포스터: 요청별 업로드·조회 메타데이터와 로컬 개발 파일 저장
- 대시보드: 접근 모듈, 지표, 최근 업무 조회

## 3. Supabase 반영 상태

- Alembic `20260731_0005 (head)`까지 Supabase에 적용했다.
- 생성된 핵심 테이블: `departments`, `employees`, `approval_documents`, `approval_histories`, `notifications`, `recruitment_requests`, `job_postings`, `alembic_version`
- 초기 데이터: 부서 5건, 직원 5건
- 현재 업무 데이터: 결재·채용 요청·채용공고 0건
- 애플리케이션 DB 연결과 migration DB 연결 모두 확인했다.

## 4. 환경 설정 정리

- `backend/.env`의 두 DB URL을 `postgresql+psycopg://` 형식으로 정리했다.
- 비밀번호 특수문자를 URL 인코딩하고 `sslmode=require`를 적용했다.
- Psycopg에서 인식하지 않는 `pgbouncer=true` 옵션과 잘못된 migration DB명 끝 따옴표를 제거했다.
- 실제 비밀값은 저장소나 문서에 기록하지 않는다.

## 5. 다음 작업

다음 작업일에는 직원관리프로세스를 시작한다. 직원 등록·조회·수정·비활성화와 부서·역할 변경 규칙을 먼저 정의하고, API Schema → Service → Repository → 화면 순서로 구현한다.
