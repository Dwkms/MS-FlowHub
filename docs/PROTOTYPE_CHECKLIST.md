# Prototype Checklist

## v0.5.0 진행 상태

- [x] ATS: 채용 요청 작성·목록·상세
- [x] ATS: 채용 요청 상신과 공통 전자결재 연결
- [x] ATS: 승인 후 채용공고 초안 자동 생성
- [x] ATS: 반려 시 공고 미생성 및 요청 상태 동기화
- [-] ATS: 지원자 등록과 채용 단계 관리
- [ ] Mock AI 채용 요약·공고 생성
- [x] Database: 채용 흐름 migration upgrade/downgrade 검증
- [x] Backend 테스트: 채용 요청 권한·상태·중복·트랜잭션


목표일: 2026-08-15

상태 표기: `[ ] 미착수`, `[-] 진행 중`, `[x] 완료`, `[~] 제외`, `[!] 오류`. 한 항목에는 하나의 상태만 사용한다.

## 프로젝트 문서

- [x] 프로젝트 규칙과 기획 문서
- [x] 데이터·API·AI 설계 초안
- [x] 로드맵과 설계 결정 기록

## Backend 환경

- [-] Python 3.12와 FastAPI 기본 환경 — 프로젝트 설정 완료, 로컬 Python 3.12 설치 필요
- [-] Pydantic v2 설정 및 오류 응답 — 설정·응답 Schema 완료, 공통 오류 형식 예정
- [ ] SQLAlchemy 2.0 동기 Session

## Frontend 환경

- [x] Next.js App Router, TypeScript, Tailwind CSS
- [-] 공통 API Client와 로딩·오류 fallback — 빈 데이터 화면 예정

## Supabase 연결

- [ ] 개발용 Supabase PostgreSQL 준비
- [-] FastAPI 연결 구조 및 프론트 직접 접근 금지 — 환경변수·Repository 구현, 실제 접속값 검증 필요

## Alembic

- [x] 초기화와 최초 migration
- [x] 별도 로컬 테스트 DB upgrade/downgrade 검증

## Seed 데이터

- [-] 샘플 부서·직원·역할 — 상품 예정
- [x] 조직 Seed 반복 실행 중복 방지

## 직원·부서 / 역할 전환 / 대시보드

- [-] 직원·부서 조회 — Mock 조회 API 완료, DB 저장 예정
- [-] 샘플 사용자 선택과 서비스 계층 역할 확인 — Mock 역할 조회 완료, 세션 API 예정
- [x] 역할별 모듈 접근 표시와 업무 요약

## 전자결재

- [x] 문서 작성·목록·상세·상신
- [x] 단일 승인·반려·의견
- [x] 상태 전환·자기 결재·재처리 방지
- [-] 처리 이력 완료, 인앱 알림 저장 예정

## ATS

- [ ] 채용 요청과 결재 연결
- [ ] 승인된 요청의 공고 생성
- [ ] 지원자 등록·조회·단계 변경

## CRM·견적

- [ ] 고객·기회·상품
- [ ] 견적 항목과 Decimal 서버 계산
- [ ] 10% 초과 결재와 승인 후 확정

## Mock AI / 실제 AI Provider 인터페이스

- [ ] MockAIProvider의 7개 기능
- [ ] 공통 Provider 인터페이스와 환경변수 선택
- [ ] 생성·수정 결과 및 실패 기록

## Backend 테스트

- [x] 전자결재 권한과 상태 전환
- [ ] 금액 계산과 할인 경계값
- [ ] 통합 시나리오 핵심 API

## Frontend 검증

- [ ] lint와 type check
- [ ] production build와 핵심 화면

## Database 검증

- [ ] FK·Unique·상태 제약
- [ ] 트랜잭션과 Seed 멱등성
- [ ] migration 적용·downgrade

## README / UPDATELOG

- [x] 기획 단계 README
- [x] v0.1.0 Update Log
- [ ] 구현 상태에 맞춘 최종 갱신

## 시연 데이터 / 시나리오

- [ ] 안전한 가상 시연 데이터
- [ ] 채용 시나리오 전체
- [ ] 영업 시나리오 전체

## 포트폴리오 자료

- [ ] 문제·설계·검증 설명
- [ ] 핵심 화면 스크린샷
- [ ] 시연 영상
