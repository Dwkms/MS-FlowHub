# 작업 인계 문서 — AX 직원 도우미 (2026-08-09)

> 이 문서만 읽고도 이어서 작업할 수 있게 작성했습니다. 다만 **구현 전에 `docs/AX_FAQ_CHATBOT_PLAN.md`를 반드시 통독**해야 합니다. 이 문서는 그 기획서의 요약과 인계 맥락입니다.

## 한 줄 요약

**AX 직원 도우미 v1 — 기획 완료, 구현 미착수.** 선행 작업(FAQ 지식 보강)은 코드·운영 DB 모두 반영 완료됐고 PR #1로 master에 병합됐습니다.

## 이 기능이 무엇인가

사내 그룹웨어(MS FlowHub) 직원용 도우미입니다. 우측 하단 플로팅 버튼 → 채팅 패널에서 질문하면, **등록된 매뉴얼·FAQ 중 맞는 문서를 찾아 원문을 보여줍니다.**

**v1에는 LLM이 없습니다.** 이건 미구현이 아니라 의도된 설계입니다(기획서 0장, 12장 결정 #1). 지식 원천이 매뉴얼 9개 + FAQ 21개, 총 30개 문서뿐이라 키워드 매칭으로 충분하고, 할루시네이션 위험과 비용이 0이 됩니다. LLM·RAG는 v2에서 **v1 운영 로그를 근거로** 도입 여부를 판단합니다(기획서 11장).

## 완료된 것 (PR #1, 병합 커밋 `deb6010`)

### 코드
- `docs/AX_FAQ_CHATBOT_PLAN.md` 신규 — v1 명세 + v1.1 성능 계획 + v2 로드맵 + 의사결정 기록
- `backend/app/scripts/seed_faqs.py` — FAQ 18 → **21건**, `RELATED_MANUAL_SLUGS` 매핑 추가
- `backend/tests/test_faq_api.py` — 하드코딩된 건수(18/17)를 `len(FAQS)` 기준으로 변경

### 운영 DB (Supabase) — 이미 반영됨
- FAQ 21건 (신규 3건: `approval-attachment`, `attendance-leave-request`, `general-features`)
- FAQ 20건에 `related_manual_id` 연결 (`permission-403`만 의도적으로 비움 — 해당 매뉴얼이 없음)
- 기존 18건의 본문·카테고리·`display_order`는 **무변경** (신규 항목을 목록 끝에 배치)
- 시드 실행 전후로 드라이런 대조 완료, FK 위반 없음 확인

### 검증 완료
- backend pytest **84개 통과**, ruff check/format 통과
- GitHub Actions CI 통과 후 병합

## 다음에 할 일 (기획서 10장)

권장 순서는 **백엔드 매칭 → API → 프론트**입니다. 매칭 로직이 이 기능의 핵심이고, 그게 되면 임계값 실측(기획서 4장)을 일찍 시작할 수 있습니다.

**백엔드**
1. 매칭 서비스 — 글자 bigram + 필드 가중치 + 카테고리 집합 부스트. **교체 가능한 검색기(searcher) 경계로 분리**할 것 (v2에서 임베딩으로 갈아끼우기 위함)
2. `POST /api/v1/ax/chat` — 권한 필터 → 정책 룰 → v2 안내 룰 → 스코어링 → 응답 5종
3. `ax_chat_logs` 모델 + **Alembic migration**. `top_candidates`(상위 3개 후보) 컬럼 포함
4. 테스트 — 20문항 회귀, 권한 픽스처, 정책 우선순위, 무관 질문 fallback

**프론트**
5. `/manuals/{slug}` 읽기 전용 상세 페이지 — **백엔드 API와 `getManual(slug)` 클라이언트는 이미 존재.** 페이지만 만들면 됨
6. 플로팅 버튼 + 채팅 패널(데스크톱 360×560) / 전체화면 시트(모바일 <768px)
7. 답변 카드 5종 렌더링, 추천 질문 5개, 대화 지우기

**튜닝**
8. 임계값 실측 후 확정하고 테스트로 고정

## 이미 발견해둔 함정 (다시 밟지 말 것)

구현 중에 마주칠 문제들인데, 조사해서 원인과 해법을 이미 문서화해뒀습니다.

**1. "첨부" 오매칭** — 전체 30개 문서에서 "첨부"라는 단어는 채용 관련 2곳에만 있습니다(`man:recruitment-request-to-posting`에 "JPG, PNG, WEBP, PDF 5MB 이하" 상세 기술). 그래서 "전자결재에 파일 첨부되나요?"가 채용 매뉴얼에 걸려 **"네, 가능합니다"라는 오답**이 나갑니다. 실제로 `ApprovalDocument`에 첨부 컬럼이 없습니다.
→ `faq:approval-attachment`를 추가해 해결했고, 그 FAQ에 "채용 포스터와는 다른 기능"이라는 구분 문장을 넣었습니다. **8장 하드 게이트에서 반드시 검증할 것.**

**2. FAQ와 매뉴얼의 카테고리 이름이 다릅니다** — `직원·조직`(FAQ) vs `직원·조직 관리`(매뉴얼), `채용 요청·ATS`(FAQ) vs `채용 요청·ATS Lite`(매뉴얼). 카테고리 부스트나 라우트 매핑을 **단일 문자열로 하면 한쪽이 통째로 누락**됩니다. 반드시 **집합**으로 매핑하세요(기획서 3장·4장에 표 있음).

**3. 권한 질문은 `로그인·계정`이 아니라 `권한` 카테고리입니다** — `permission-403`, `permission-missing-menu`, `permission-401`이 전부 `권한`에 있습니다. 403/401을 로그인 쪽으로 부스트하면 정답 FAQ가 밀립니다.

**4. `/manuals/{slug}` 페이지가 없습니다** — 라우트는 `/manuals`(목록)와 `/manuals/{slug}/edit`(관리자 전용)뿐이고, 목록 카드는 `title`과 `summary`만 렌더링합니다. 즉 **일반 직원이 매뉴얼 본문을 볼 방법이 현재 없습니다.** 그래서 상세 페이지를 v1 범위에 넣었습니다(기획서 3장).

## 설계상 반드시 지킬 것

- **v1에 LLM·RAG·벡터DB를 넣지 마세요.** 의도된 결정입니다(기획서 12장 #1, #2). 필요성은 v2에서 로그로 판단합니다.
- **형태소 분석기(konlpy/mecab)를 쓰지 마세요.** 글자 bigram으로 갑니다. 시스템 바이너리 의존성 회피가 이유입니다.
- **임계값을 임의의 숫자로 정하지 마세요.** 구현 후 20문항 + 함정 질문 + 무관 질문으로 점수 분포를 뽑고, **오답 0건**을 최우선 제약으로 정한 뒤 테스트로 고정합니다(기획서 4장 절차).
- **가장 큰 리스크는 "못 찾는 것"이 아니라 "틀린 문서로 자신 있게 답하는 것"입니다.** 애매하면 확정 답변 대신 "후보 제시"로 떨어뜨리세요.
- AX API는 **읽기 전용**입니다. `Manual`·`ManualFaq`·`Employee.role`만 읽고 결재·근태·채용 데이터는 건드리지 않습니다.
- 권한 필터는 **조회 쿼리 단계**에서 겁니다(응답 생성 후 걸러내지 않음).

## 하지 말 것

- 기존 FAQ 21건·매뉴얼 9건의 **본문을 임의로 수정하지 마세요.** 추가가 필요하면 목록 끝에 붙여 `display_order`를 보존합니다.
- **운영 Supabase에 부하 테스트를 걸지 마세요.** 실제 직원 46명 데이터가 있고 커넥션 제한·비용에 부딪힙니다. 성능 측정은 로컬에서만(기획서 11장).
- 시드 스크립트를 운영 DB에 실행하기 전 **반드시 드라이런으로 INSERT/UPDATE/DELETE 건수와 FK를 먼저 확인**하세요. 이번 작업에서 확립한 절차입니다.
- Supabase 데이터 삭제, Alembic 초기화 금지.
- Secret을 저장소에 기록 금지 (`backend/.env`는 gitignore됨, 추적되지 않음 — 확인 완료).
- **실행하지 않은 테스트를 통과했다고 보고하지 마세요.**

## 검증 명령

```powershell
# Backend
cd backend
.venv\Scripts\python.exe -m ruff check app tests
.venv\Scripts\python.exe -m ruff format --check app tests
.venv\Scripts\python.exe -m pytest -q

# Frontend
cd frontend
npm run lint
npm run typecheck
npm run build
```

FAQ 시드를 다시 실행해야 한다면(멱등, upsert 전용, DELETE 없음):
```powershell
cd backend
.venv\Scripts\python.exe -m app.scripts.seed_faqs
```

## 참고 문서

| 파일 | 내용 |
|---|---|
| `docs/AX_FAQ_CHATBOT_PLAN.md` | **주 기획서.** 2장 질문↔근거 매핑표가 곧 검증 체크리스트 |
| `docs/AI_DESIGN.md` | AIProvider·`ai_generations` 설계(미구현). v2에서 사용 |
| `docs/HANDOFF.md` | 2026-08-08 CI/CD·대시보드 인계 (종료됨, 맥락 보존용) |
| `backend/app/scripts/seed_faqs.py` | FAQ 21건 원문 + 매뉴얼 연결 매핑 |
| `backend/app/scripts/seed_manuals.py` | 매뉴얼 9건 원문, 카테고리 6종 |
| `backend/app/models/manual.py` | `Manual`, `ManualFaq`, `ManualCategory` 스키마 |
| `frontend/src/features/manuals/` | 매뉴얼 목록·폼·API 클라이언트 |

## 현재 git 상태

- `master` = `deb6010` (PR #1 병합 완료), 로컬·원격 동기화됨
- `docs/JIRA_UPDATE_2026-08-08.md`에 **커밋되지 않은 수정**이 남아 있습니다. 이번 AX 작업과 무관해서 일부러 커밋하지 않았습니다. 별도로 처리하세요.
- 구현은 새 브랜치에서 시작하세요(예: `feat/ax-chat-backend`).
