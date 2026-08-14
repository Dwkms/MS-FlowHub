# Roadmap

전체 그림과 앞으로 할 일입니다.

- 각 기능을 **왜 만들었나** → [`PLAN.md`](PLAN.md)
- 지금 **무엇이 되고 안 되나** → [`CURRENT_STATE.md`](CURRENT_STATE.md)
- 날짜별 **변경 이력** → [`../UPDATELOG.md`](../UPDATELOG.md)
- Jira 보드 반영 대상 → [`JIRA_UPDATE_2026-08-08.md`](JIRA_UPDATE_2026-08-08.md)
- 2026-07-30 작성 당시의 일정 기준선 → [`archive/ROADMAP_PLAN_2026-08.md`](archive/ROADMAP_PLAN_2026-08.md)

## 기능 구성 한눈에 보기

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontFamily": "Pretendard, Noto Sans KR, sans-serif",
    "fontSize": "15px",
    "lineColor": "#9aa4b5",
    "cScale0": "#dfe8f5", "cScaleLabel0": "#172033",
    "cScale1": "#e2eddc", "cScaleLabel1": "#172033",
    "cScale2": "#f6e9d9", "cScaleLabel2": "#172033",
    "cScale3": "#ece1f2", "cScaleLabel3": "#172033",
    "cScale4": "#fbe6e6", "cScaleLabel4": "#172033",
    "cScale5": "#dfeef1", "cScaleLabel5": "#172033",
    "cScale6": "#ebedf2", "cScaleLabel6": "#172033",
    "cScale7": "#f0ece2", "cScaleLabel7": "#172033"
  }
}}%%
mindmap
  root((MS FlowHub))
    공통 기반
      Supabase Auth 로그인
      역할 5종 권한 판정
      자동 로그아웃 30분
      조직 2계층
    전자결재
      작성·상신·승인·반려
      처리 이력
      결재자 파트장급 이상
      AI 문안 초안
    채용
      채용 요청
      승인 시 공고 생성
      AI 공고 초안
      AI 포스터 이미지
      지원자 6단계
    직원·근태
      검색·필터
      근무 상태 12종
      비공개 사유 분리
      변경 이력
    지식
      직원 매뉴얼
      FAQ 21문항
      AX 도우미
    대시보드
      개인 지표 3종
      관리자 분석 6종
    운영
      GitHub Actions CI
      Render 배포 게이트
      Alembic migration
```

## 진행 일정

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontFamily": "Pretendard, Noto Sans KR, sans-serif",
    "fontSize": "14px"
  },
  "gantt": {
    "useWidth": 1200,
    "barHeight": 26,
    "barGap": 10,
    "topPadding": 60,
    "leftPadding": 130,
    "gridLineStartPadding": 40,
    "fontSize": 13,
    "sectionFontSize": 15,
    "numberSectionStyles": 5
  }
}}%%
gantt
    title MS FlowHub 개발 일정
    dateFormat YYYY-MM-DD
    axisFormat %m/%d
    todayMarker off

    section 기반
    프로젝트 기획        :done, p1, 2026-07-30, 2d
    조직·직원·근태       :done, p2, 2026-08-01, 3d

    section 핵심 기능
    전자결재 엔진        :done, p3, 2026-08-04, 3d
    Render 배포          :done, p4, 2026-08-05, 2d
    매뉴얼·FAQ           :done, p5, 2026-08-07, 1d
    ATS 지원자 관리      :done, p6, 2026-08-07, 3d
    관리자 대시보드      :done, p7, 2026-08-08, 1d

    section 자동화
    CI 구성              :done, p8, 2026-08-08, 1d
    AX 직원 도우미       :done, p9, 2026-08-09, 2d
    생성형 AI 초안       :done, p10, 2026-08-12, 1d
    채용 구체화·포스터    :done, p11, 2026-08-13, 1d
    세션 자동 로그아웃    :done, p12, 2026-08-13, 1d

    section 안정화
    Feature Freeze       :done, p13, 2026-08-13, 1d
    배포 게이트          :done, p14, 2026-08-13, 2d
    권한 체계 재설계      :done, p15, 2026-08-14, 1d
    데드코드·문서 정리    :active, p16, 2026-08-14, 2d

    section 제출 준비
    코드 주석 보강       :p17, 2026-08-15, 1d
    README 재구성        :p18, 2026-08-16, 1d
    Jira 최종정리        :p19, 2026-08-17, 1d
```

## 지금 하는 일 — 포트폴리오 제출 준비

목표는 **"어느 파일에 무엇이 왜 있는지 설명할 수 있는 저장소"** 입니다.
용량 감소는 부수 효과이고 설명 가능성이 목적입니다.

| 단계 | 내용 | 상태 |
|---|---|---|
| 1 | 데드코드·중복 자산 정리, 알림 기능 제거 | **완료** |
| 2 | 기획 문서 5개를 `PLAN.md`로 통합, archive 정리 | **완료** |
| 3 | 로드맵 시각화, 문서 안내 신설 | **완료** |
| 4 | 핵심 코드 주석 보강 — 시니어가 주니어에게 설명하는 수준 | 예정 |
| 5 | README 재구성 — 프로젝트 구성 요약 중심 | 예정 |
| 6 | 전체 검증 | 예정 |
| 7 | Jira 최종정리 | 예정 |

## 그다음 — 우선순위 순

| 순서 | 항목 | 비고 |
|---|---|---|
| 1 | **GitHub branch protection** | `master` 직접 push 금지 + PR 필수 CI. Render 게이트가 하류 방어라면 이쪽이 상위 보호 |
| 2 | **Pre-Deploy Command로 migration 자동화 검토** | 현재는 배포 전 수동 `alembic upgrade head`. 실패 시 운영 DB가 중간 상태로 남을 위험이 있어 별도 판단 |
| 3 | **화면이 없는 기능의 UI** | 결재 문서 수정 · 공고 수정 · 역할 변경. API는 준비돼 있고 화면만 없습니다 |
| 4 | 공통 오류 응답 형식 정리 | |
| 5 | ATS·Storage Playwright E2E 확대 | |

## 후속 과제 — 착수 시점 미정

구조에 손대야 해서 별도 판단이 필요합니다.

- **직급과 직책 컬럼 분리** — `employees.position` 한 컬럼에 사원·대리(직급)와 팀장·파트장(직책)이
  섞여 있어 파트장의 직급을 표현할 수 없습니다
- **역할 값 어휘 통합** — `employee_accounts.role`(권한)과 `employees.role`(시드)이 다른 값을 씁니다
- **storage 레이어** — `localStorage`를 감싸는 규칙만 있고 구현이 없습니다
- **조직도 API 활용** — `GET /employees/organization`이 있는데 화면은 1.24MB 정적 PNG를 씁니다

## 확정된 정책

되돌리지 않기로 한 결정입니다. 근거는 [`DECISIONS.md`](DECISIONS.md).

- **대시보드에 가짜 업무 데이터를 넣지 않습니다.** 지표가 비어 보여도 실데이터만 씁니다.
- **AI는 업무 상태를 바꾸지 않습니다.** 초안을 만들 뿐 저장은 사용자가 합니다.
- **Playwright E2E는 수동 실행 전용입니다.** 실제 Supabase에 접속하므로 CI에서 자동 실행하지 않습니다.

## 범위 밖

의도적으로 만들지 않기로 한 것들입니다. 배경은
[`PLAN.md`](PLAN.md#1-프로젝트-배경과-범위--2026-07-30).

실제 이메일 발송 · PDF 분석·OCR · RAG·벡터 DB · n8n · 다단계 결재 ·
WebSocket 실시간 알림 · Docker · 모바일 앱 · 자동 채용 결정

인앱 알림은 2026-08-14에 제거했습니다. 사내 메일 시스템 도입 시 다시 설계합니다.
