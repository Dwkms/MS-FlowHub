# 작업 인계 문서 — AX 직원 도우미 (2026-08-10 갱신)

> 이 문서만 읽고도 이어서 작업할 수 있게 작성했습니다. 설계 근거가 필요하면 `docs/AX_FAQ_CHATBOT_PLAN.md`를 보세요.

## ⚠ 지금 바로 이어서 할 일 (2026-08-10 중단 지점)

**코드는 전부 master에 병합됐습니다. 문서 4개만 커밋이 안 된 상태입니다.**

커밋 대기 중인 파일: `README.md`, `UPDATELOG.md`, `TROUBLESHOOTING.md`, `docs/HANDOFF_AX_2026-08-09.md`
(`docs/JIRA_UPDATE_2026-08-08.md`도 수정돼 있지만 AX와 무관하므로 **같이 커밋하지 마세요**)

### 1) 로컬 정리 — 아직 안 됨

PR #3 병합 후 로컬 master를 아직 안 내려받았고, 브랜치도 안 지웠습니다.

```powershell
cd "C:\Users\user\Documents\MS FlowHub"
git switch master
git pull
git branch -d feat/ax-chat-backend
```

### 2) 문서 커밋·푸시

```powershell
git switch -c docs/ax-v1-sync
git add README.md UPDATELOG.md TROUBLESHOOTING.md docs/HANDOFF_AX_2026-08-09.md
git commit -m "docs: AX 도우미 v1 반영 (README/UPDATELOG/TROUBLESHOOTING/인계문서)"
git push -u origin docs/ax-v1-sync
```

그다음 GitHub에서 PR 생성 → **CI 초록불 확인 후** Merge → `Delete branch` → 다시 1)의 로컬 정리.

### 3) 그 뒤 할 일

아래 "다음 작업 후보" 표를 보고 고르면 됩니다. 1순위는 직원 2~3명 사용성 점검입니다.

---

## 한 줄 요약

**AX 직원 도우미 v1 완료.** 기획·백엔드·프론트·테스트·운영 DB 반영까지 끝났고 master에 병합됐습니다(PR #1·#2·#3). 다음 작업은 v1 사용성 점검, 전자결재 첨부 기능, v1.1 성능 측정, v2 LLM·RAG 중에서 고르면 됩니다.

## 이 기능이 무엇인가

우측 하단 플로팅 버튼에서 열리는 사내 도우미입니다. 질문하면 **등록된 매뉴얼 9개 + FAQ 21개에서 맞는 문서를 찾아 원문을 보여줍니다.**

**v1에는 LLM이 없습니다. 이건 미구현이 아니라 의도된 설계입니다**(기획서 0장, 12장 결정 #1). 문서 30개 규모에서는 키워드 검색으로 충분하고, 할루시네이션 위험과 비용이 0이 됩니다. LLM·RAG 도입 여부는 v1 운영 로그를 근거로 판단합니다(11장).

## 완료된 것

| 영역 | 내용 |
|---|---|
| 기획 | `docs/AX_FAQ_CHATBOT_PLAN.md` 12장 — 명세, 실측 임계값, 로드맵, 의사결정 기록 |
| 매칭 | `app/domain/ax_search.py` — 1+2gram + IDF + 카테고리 부스트, `DocumentSearcher` 경계 분리 |
| 룰 | `app/domain/ax_rules.py` — 정책 고정 응답, 개인화 질문 감지 |
| API | `POST /api/v1/ax/chat` — 응답 5종, 역할별 권한 필터 |
| 로깅 | `ax_chat_logs` + migration `20260810_0021` (익명, `top_candidates` 포함) |
| 프론트 | 채팅 패널·드래그·모바일 시트, `/manuals/{slug}` 상세 페이지 |
| 테스트 | 백엔드 119개 전부 통과(AX 신규 35개) |
| 운영 DB | FAQ 21건, `related_manual_id` 연결, `ax_chat_logs` 테이블 반영 완료 |

**측정 결과**: 오답 0건 / 무관 질문 누출 0건 / 확정 정답 14 · 20문항 / 근거 없음 1건.

## 확정된 값과 그 근거

임계값은 **확정 0.30 / 하한 0.24 / 마진 0.05**입니다. 임의로 바꾸지 마세요.

실제 시드 30개 문서에 직원이 칠 법한 표현 19문항과 무관 질문 11개를 넣어 측정하고, IDF 공식 3종 × 임계값 조합을 전수 비교해 **오답 0건을 제약**으로 정한 값입니다. 무관 질문 최고점이 0.230이라 하한을 그 위에 뒀습니다. 마진을 0.04로 낮추면 확정이 1건 늘지만 특정 문항이 0.001 차이로 오답이 되는 자리라 채택하지 않았습니다.

바꿔야 한다면 같은 방식으로 다시 측정하고 기획서 4장·8장을 함께 갱신하세요.

## 이미 발견해둔 함정 (다시 밟지 말 것)

**1. "첨부" 오매칭** — 전체 문서에서 "첨부"는 채용 매뉴얼 2곳에만 있습니다. `faq:approval-attachment`를 추가하고 "채용 포스터와는 다른 기능"이라는 구분 문장을 넣어 해결했습니다. 이 FAQ를 지우면 오답이 되살아납니다.

**2. FAQ와 매뉴얼의 카테고리 이름이 다릅니다** — `직원·조직`(FAQ) vs `직원·조직 관리`(매뉴얼), `채용 요청·ATS` vs `채용 요청·ATS Lite`. 카테고리 매핑은 반드시 **집합**으로 다뤄야 하며, `DOMAIN_CATEGORIES` 한 곳에서 관리합니다.

**3. 권한 질문은 `권한` 카테고리입니다** — `permission-403`·`permission-missing-menu`·`permission-401`. `로그인·계정`으로 부스트하면 정답이 밀립니다.

**4. 2-gram만으로는 한국어 활용어미를 못 넘습니다** — "찾는"/"찾을"/"찾거"는 2-gram이 전부 다릅니다. 1-gram을 함께 넣어 해결했습니다. 토크나이저를 건드릴 때 이 점을 잊지 마세요.

**5. 세션 가드가 화면 전환마다 하위를 언마운트합니다** — 전역 UI 상태는 `AuthSessionGuard` 바깥에 둬야 합니다.

## 지켜야 할 것

- v1에 **LLM·RAG·벡터DB를 넣지 마세요.** 필요성은 로그로 판단합니다.
- **형태소 분석기(konlpy/mecab)를 쓰지 마세요.** 시스템 바이너리 의존성 회피가 이유입니다.
- 가장 큰 리스크는 "못 찾는 것"이 아니라 **"틀린 문서로 자신 있게 답하는 것"**입니다. 애매하면 후보 제시로 떨어뜨립니다.
- AX API는 **읽기 전용**입니다. 결재·근태·채용 데이터를 읽지도 쓰지도 않습니다.
- 로그에 **질문자 식별자를 넣지 마세요**(46명 조직에서 민감 정보가 됩니다).
- 대화 내용을 **브라우저에도 저장하지 마세요**(위치만 저장합니다).
- 기존 FAQ·매뉴얼 본문을 임의로 수정하지 말고, 추가는 목록 **끝**에 붙여 `display_order`를 보존하세요.
- 시드를 운영 DB에 실행하기 전 **드라이런으로 INSERT/UPDATE/DELETE와 외래키를 먼저 확인**하세요.
- **운영 Supabase에 부하 테스트를 걸지 마세요.** 성능 측정은 로컬에서만 합니다.
- 실행하지 않은 테스트를 통과했다고 보고하지 마세요.

## 다음 작업 후보

| 우선순위 | 작업 | 메모 |
|---|---|---|
| 1 | **v1 사용성 점검** | 직원 2~3명이 20문항 체크리스트 + 자유 질문으로 사용(기획서 8장) |
| 2 | **전자결재 첨부 기능** | `EXPENSE`·`QUOTATION_DISCOUNT` 문서 종류가 있는데 첨부가 없어 실무상 공백. 채용 포스터 Storage 코드를 재사용 가능. **만들면 `faq:approval-attachment`를 반드시 수정** |
| 3 | v1.1 성능 측정 | 로컬 부하 → 병목 확인 → 문서 캐시 → 재측정. 캐시는 "문서 수정 즉시 반영"과 상충(기획서 11장) |
| 4 | v2 LLM·RAG | `top_candidates`로 실패 원인을 분류한 뒤 결정. 정답이 2~3위면 임베딩, 후보에 없으면 문서 보강 |

## 검증 명령

```powershell
# Backend
cd backend
.venv\Scripts\python.exe -m ruff check app tests migrations
.venv\Scripts\python.exe -m ruff format --check app tests migrations
.venv\Scripts\python.exe -m pytest -q

# 도우미 손으로 시험 (로그 안 남음)
.venv\Scripts\python.exe -m app.scripts.try_ax_chat

# Frontend
cd frontend
npm run lint
npm run typecheck
npm run build
```

## 참고 문서

| 파일 | 내용 |
|---|---|
| `docs/AX_FAQ_CHATBOT_PLAN.md` | 주 기획서. 2장 질문↔근거 매핑표가 검증 체크리스트, 12장이 의사결정 기록 |
| `docs/AI_DESIGN.md` | AIProvider·`ai_generations` 설계(미구현). v2에서 사용 |
| `docs/HANDOFF.md` | 2026-08-08 CI/CD·대시보드 인계 (종료됨, 맥락 보존용) |
| `TROUBLESHOOTING.md` | AX 관련 증상 3건 포함 |
| `backend/app/scripts/seed_faqs.py` | FAQ 21건 원문 + 매뉴얼 연결 매핑 |

## 현재 git 상태

- `master` = PR #3 병합 완료
- `docs/JIRA_UPDATE_2026-08-08.md`에 커밋되지 않은 수정이 남아 있습니다. AX와 무관해 일부러 커밋하지 않았습니다.
- 새 작업은 새 브랜치에서 시작하세요.
