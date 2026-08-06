# AI Design

> 상태: 미래 확장 설계. 현재 AI Provider, `ai_generations` 테이블, AI API 및 화면은 구현하지 않았습니다.

## 원칙과 호출 구조

`ATS Service → AI Application Service → AIProvider → Mock 또는 실제 LLM` 순서로 호출한다. Provider 생성은 Backend의 AI factory 또는 FastAPI dependency 경계에서 환경설정을 읽어 한 곳에서 담당한다. Router와 UI는 Provider를 직접 호출하지 않는다.

```python
# 인터페이스 형태를 설명하기 위한 의사 코드이며 아직 구현하지 않는다.
class AIProvider:
    def generate(self, feature_type, input_data) -> AIProviderResult: ...
```

Provider 결과 후보는 `content`, `provider`, `model_name`, `success`, `error_message`를 포함한다.

## Provider 선택

- `AI_PROVIDER`가 없거나 실제 Provider 필수 설정이 없으면 `MockAIProvider`
- Mock은 입력을 기반으로 고정 형식의 재현 가능한 한국어 예시를 반환하며 외부 네트워크를 사용하지 않는다.
- 실제 LLM Provider는 `AI_API_KEY`, `AI_MODEL`을 설정에서 읽고 timeout과 예외를 공통 결과로 변환한다.
- 잘못된 명시적 Provider 설정을 조용히 Mock으로 숨길지는 구현 시 구분한다. 시연 기본값 누락은 Mock, 운영 의도의 오타는 설정 오류로 보는 방향을 권장한다.

## 기능별 입력과 출력 예시

| 기능 종류 | 입력 | 출력 형태·예시 |
|---|---|---|
| `RECRUITMENT_REASON_SUMMARY` | 직무, 인원, 부서, 채용 사유 | 짧은 문단: “고객 지원 업무 증가에 대응하기 위한 1명 충원 요청입니다.” |
| `JOB_POSTING_DRAFT` | 직무, 필요 역량, 업무, 조건 | 구조화 초안: 제목, 주요 업무, 자격 요건, 우대 사항 |
| `APPLICANT_CAREER_SUMMARY` | 입력된 경력 텍스트, 지원 직무 | 사실 중심 요약: “관련 업무 2년, 고객 문의 처리와 문서화 경험이 입력되었습니다.” |
| `INTERVIEW_QUESTIONS_DRAFT` | 직무, 경력, 공고 | 문자열 배열: `["업무 우선순위를 정한 경험을 설명해 주세요.", ...]` |

공고·질문은 구조화된 JSON 출력을 우선 검토하고, 단순 요약은 텍스트가 충분하다. Pydantic 스키마로 검증하되 출력 파싱 실패도 AI 실패로 기록한다.

## 저장 구조

공통 `ai_generations` 한 테이블을 사용한다.

- `source_input`: 호출 당시 정규화한 원본 입력. 무분별한 개인정보·기밀은 제거하거나 최소화한다.
- `generated_output`: Provider가 생성한 원본. 재실행·수정 시 덮어쓰지 않는다.
- `final_output`: 사용자가 확인·수정한 최종 문안. 생성 원본과 분리한다.
- `feature_type`, `related_type`, `related_id`: 기능과 업무 연결
- `provider`, `model_name`, `success`, `error_message`, `created_at`: 실행 추적

AI 재실행은 기존 행을 덮어쓰기보다 새 generation 행을 생성해 이력을 보존한다. 어떤 결과가 현재 선택본인지 필요해지면 업무 엔티티의 선택 참조 또는 별도 상태를 이후 검토한다.

## 실패, timeout, fallback

- timeout 후보는 Provider 설정값으로 중앙 관리하며 초기값은 실제 연동 때 측정 후 확정한다.
- 호출 실패도 `success=false`, 안전하게 정리한 오류 메시지와 함께 기록한다. 비밀·원시 SDK 응답은 사용자에게 노출하지 않는다.
- AI가 부가 동작이면 핵심 업무 데이터 저장을 먼저 안정적으로 완료하고 “초안을 생성하지 못했으나 직접 작성 가능” 상태를 반환한다.
- AI 결과가 반드시 필요한 별도 생성 요청은 성공 응답과 실패 결과의 HTTP 의미를 API 구현 시 확정하되, 관련 채용 요청을 rollback하지 않는다.
- Mock fallback 사용 여부를 UI에 표시해 실제 LLM 결과로 오해하지 않게 한다.

## 개인정보·기밀과 금지 판단

프로토타입에는 실제 개인정보와 회사 기밀을 넣지 않는다. 지원자 입력은 가상 데이터만 사용하고 Provider 전달 필드를 최소화한다. 로그에 API 키나 접속정보를 남기지 않는다.

AI는 지원자 평가·순위·자동 탈락, 승인·반려, 합격·불합격을 수행하지 않는다. 모든 결과는 담당자가 확인하고 수정하는 보조 초안이며 업무 상태에 자동 반영하지 않는다.
