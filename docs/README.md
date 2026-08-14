# 문서 안내

MS FlowHub의 문서 구조입니다. **필요한 것만 골라 읽으세요.** 전부 읽을 필요 없습니다.

AI 에이전트로 작업한다면 루트의 [`AGENTS.md`](../AGENTS.md)(= [`CLAUDE.md`](../CLAUDE.md))에
작업 종류별 Context Map이 있습니다.

## 메인 — 프로젝트를 처음 보는 사람이 읽을 순서

| 문서 | 역할 | 언제 읽나 |
|---|---|---|
| [`PLAN.md`](PLAN.md) | **무엇을 왜 만들었나.** 15개 기능을 시간순으로, 각 절에 화면·판단 근거·결과 | 프로젝트를 이해할 때. 면접 설명의 주 자료 |
| [`CURRENT_STATE.md`](CURRENT_STATE.md) | **지금 무엇이 되고 안 되나.** 도메인별 상태와 알려진 문제 | 작업을 시작하기 전 |
| [`ROADMAP.md`](ROADMAP.md) | **앞으로 할 일.** 마인드맵·간트로 전체 그림 | 다음에 뭘 할지 정할 때 |

## 참조 — 코드를 고치기 전에 보는 것

| 문서 | 역할 | 언제 읽나 |
|---|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | 요청 흐름, 인증 5단계, 백엔드 9계층, 프론트 구조, 배포 구조 | 어디를 고쳐야 할지 모를 때 |
| [`DOMAIN.md`](DOMAIN.md) | 업무 규칙, 역할과 권한, 상태 전이, 예외 | 업무 로직을 건드릴 때 |
| [`DATA_MODEL.md`](DATA_MODEL.md) | 테이블·컬럼·관계·제약. ERD 포함 | DB를 건드릴 때 |
| [`API_SPEC.md`](API_SPEC.md) | 현재 엔드포인트 지도 | API를 확인하거나 추가할 때 |

> 스키마 필드의 단일 출처는 `backend/app/schemas/`와 `/docs`(Swagger)입니다.
> 문서에 필드를 복사해 두지 않습니다.

## 규칙과 운영

| 문서 | 역할 | 언제 읽나 |
|---|---|---|
| [`CODING_RULES.md`](CODING_RULES.md) | 계층 책임, Backend·Frontend 규칙, 검증 명령, 문서 반영 기준 | 코드를 쓰기 전 |
| [`DEPLOYMENT_PLAN.md`](DEPLOYMENT_PLAN.md) | Render 두 서비스의 실제 설정값과 주의사항 | 배포 설정을 볼 때 |
| [`AI_DESIGN.md`](AI_DESIGN.md) | AI 입출력 제약과 환각 방지 기준 | AI 기능을 건드릴 때 |

## 기록

| 문서 | 역할 |
|---|---|
| [`DECISIONS.md`](DECISIONS.md) | **구조·기술 선택의 근거(ADR).** 날짜·상태·배경·결정·영향·주의사항·재검토 조건 |
| [`JIRA_UPDATE_2026-08-08.md`](JIRA_UPDATE_2026-08-08.md) | Jira 보드에 반영할 대상 목록 |
| [`archive/`](archive/README.md) | 초기 기획 원문과 인계 문서. 무엇이 어디로 요약됐는지 안내 포함 |

루트에는 [`UPDATELOG.md`](../UPDATELOG.md)(날짜별 변경 이력)와
[`TROUBLESHOOTING.md`](../TROUBLESHOOTING.md)(겪은 오류와 해결)가 있습니다.

## 문서 역할이 겹치지 않게 하는 기준

같은 내용을 여러 문서에 복사하지 않습니다. 헷갈리기 쉬운 짝을 정리합니다.

| 헷갈리는 짝 | 구분 |
|---|---|
| `PLAN` ↔ `UPDATELOG` | PLAN은 **기능 단위로 왜**, UPDATELOG는 **날짜 단위로 무엇을** |
| `PLAN` ↔ `DECISIONS` | PLAN은 **기능**을 왜 만들었나, DECISIONS는 **구조·기술**을 왜 골랐나 |
| `CURRENT_STATE` ↔ `ROADMAP` | CURRENT_STATE는 **지금**, ROADMAP은 **앞으로** |
| `PLAN` ↔ `DOMAIN` | PLAN은 **만들 때의 판단**, DOMAIN은 **지금 적용 중인 규칙** |
| `DOMAIN` ↔ `DATA_MODEL` | DOMAIN은 상태값의 **의미와 전이**, DATA_MODEL은 **컬럼과 관계** |
| `ARCHITECTURE` ↔ `DEPLOYMENT_PLAN` | ARCHITECTURE는 **구조 설명**, DEPLOYMENT_PLAN은 **Render 설정값** |

## 왜 폴더로 나누지 않았나

문서가 12개라 한 화면에 들어오고, 나눠 보면 1개짜리 폴더가 생깁니다.
GitHub에서 폴더를 클릭하면 파일 이름만 보이지만 이 `README.md`는 자동으로 렌더링돼
설명과 함께 보입니다.

다음 조건에서 폴더로 나눕니다.

- 문서가 **20개를 넘을 때**
- **한 폴더에 3개 이상**이 자연스럽게 묶일 때
- 회의록·성능 측정·보안 점검처럼 **문서 종류 자체가 늘어날 때**
