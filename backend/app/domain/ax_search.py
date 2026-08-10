"""AX 도우미 문서 검색 — 순수 로직.

DB·HTTP에 의존하지 않는다. v2에서 임베딩 기반 검색으로 교체할 때 이 모듈의
`DocumentSearcher` 구현만 갈아끼우면 API와 응답 형식은 그대로 둘 수 있다.
설계 근거는 docs/AX_FAQ_CHATBOT_PLAN.md 4장 참조.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

FAQ = "FAQ"
MANUAL = "MANUAL"

# 필드 가중치. 질문/제목이 본문보다 훨씬 강한 신호다.
WEIGHT_FAQ_QUESTION = 3.0
WEIGHT_FAQ_ANSWER = 1.0
WEIGHT_MANUAL_TITLE = 3.0
WEIGHT_MANUAL_SUMMARY = 2.0
WEIGHT_MANUAL_CONTENT = 1.0

CATEGORY_BOOST = 1.5

# 2026-08-10 실측으로 확정. 측정 방법과 근거는 기획서 4장 "임계값" 참조.
# 무관 질문 최고점이 0.230이었으므로 하한을 그 위에 둔다.
SCORE_FLOOR = 0.24
SCORE_CONFIDENT = 0.30
SCORE_MARGIN = 0.05

MAX_CANDIDATES = 3

# FAQ와 매뉴얼은 카테고리 이름 체계가 다르다(`직원·조직` vs `직원·조직 관리`).
# 단일 문자열로 매핑하면 한쪽이 통째로 누락되므로 반드시 집합으로 다룬다.
DOMAIN_CATEGORIES: dict[str, frozenset[str]] = {
    "approval": frozenset({"전자결재"}),
    "attendance": frozenset({"근태·휴가"}),
    "recruitment": frozenset({"채용 요청·ATS", "채용 요청·ATS Lite"}),
    "organization": frozenset({"직원·조직", "직원·조직 관리"}),
    "account": frozenset({"로그인·계정"}),
    # 403/401 FAQ는 `로그인·계정`이 아니라 `권한` 카테고리에 있다.
    # 로그인 쪽으로 부스트하면 정답 FAQ가 밀려난다.
    "permission": frozenset({"권한"}),
    "general": frozenset({"일반", "업무 홈 대시보드"}),
}

# 답변 카드의 "관련 화면으로 이동" 버튼. 부스트와 같은 도메인 키를 공유한다.
DOMAIN_ROUTES: dict[str, str | None] = {
    "approval": "/approvals",
    "attendance": "/employees",
    "recruitment": "/recruitment-requests",
    "organization": "/employees",
    "account": None,
    "permission": None,
    "general": "/",
}

DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "approval": ("결재", "전자결재", "상신", "반려", "승인"),
    "attendance": ("근태", "휴가", "연차", "반차", "병가", "출근"),
    "recruitment": ("채용", "지원자", "공고", "전형", "면접"),
    "organization": ("직원", "조직도", "부서", "사번", "팀"),
    "account": ("로그인", "비밀번호", "세션"),
    "permission": ("권한", "403", "401", "메뉴"),
    "general": ("기능", "사용법"),
}


@dataclass(frozen=True)
class SearchDocument:
    """검색 후보 문서. 권한 필터를 통과한 문서만 여기까지 온다."""

    doc_type: str
    doc_id: str
    category: str
    title: str
    body: str
    weighted_fields: tuple[tuple[str, float], ...]
    related_manual_id: str | None = None
    manual_slug: str | None = None


@dataclass(frozen=True)
class SearchHit:
    document: SearchDocument
    score: float


class DocumentSearcher(Protocol):
    """v2에서 임베딩 검색기로 교체할 지점."""

    def search(self, question: str, documents: Sequence[SearchDocument]) -> list[SearchHit]: ...


def normalize(text: str) -> str:
    """공백·문장부호를 모두 제거하고 소문자화한다.

    공백까지 지우는 이유는 한국어 띄어쓰기가 사람마다 달라서다
    ("연차 반차" / "연차반차"가 같은 문자열이 된다).
    """
    return "".join(character for character in text.lower() if character.isalnum())


def bigrams(text: str) -> frozenset[str]:
    """글자 1-gram + 2-gram 집합. 형태소 분석기를 쓰지 않는 이유는 4장 참조.

    1-gram을 함께 넣는 이유는 한국어 활용어미 때문이다. "찾는"/"찾을"/"찾거"는
    2-gram이 전부 달라 서로 매칭되지 않지만, 1-gram "찾"으로는 이어진다.
    흔한 글자는 IDF가 가중치 0에 가깝게 눌러주므로 노이즈가 크게 늘지 않는다.
    """
    normalized = normalize(text)
    if not normalized:
        return frozenset()
    grams = set(normalized)
    grams.update(normalized[index : index + 2] for index in range(len(normalized) - 1))
    return frozenset(grams)


def containment(
    query_grams: frozenset[str],
    field_grams: frozenset[str],
    weights: dict[str, float] | None = None,
) -> float:
    """질문의 몇 %가 이 필드에 등장하는지. `weights`가 있으면 IDF 가중 비율.

    Dice 계수 대신 포함률을 쓴다. Dice는 길이 차가 크면 값이 급격히 작아져서,
    긴 매뉴얼 본문은 질문을 통째로 포함해도 점수가 거의 0이 된다.
    """
    if not query_grams:
        return 0.0
    if weights is None:
        return len(query_grams & field_grams) / len(query_grams)
    total = sum(weights[gram] for gram in query_grams)
    if total <= 0:
        return 0.0
    return sum(weights[gram] for gram in query_grams & field_grams) / total


def matched_domains(question: str) -> frozenset[str]:
    """질문에 등장하는 도메인 키워드를 찾는다. 카테고리 부스트에 쓰인다."""
    normalized = normalize(question)
    return frozenset(
        domain
        for domain, keywords in DOMAIN_KEYWORDS.items()
        if any(normalize(keyword) in normalized for keyword in keywords)
    )


def route_for_category(category: str) -> str | None:
    """문서 카테고리로 이동할 화면을 정한다. FAQ와 매뉴얼 이름이 달라 집합으로 찾는다."""
    for domain, categories in DOMAIN_CATEGORIES.items():
        if category in categories:
            return DOMAIN_ROUTES[domain]
    return None


def boosted_categories(question: str) -> frozenset[str]:
    domains = matched_domains(question)
    categories: set[str] = set()
    for domain in domains:
        categories |= DOMAIN_CATEGORIES[domain]
    return frozenset(categories)


@dataclass(frozen=True)
class _TokenizedDocument:
    document: SearchDocument
    fields: tuple[tuple[frozenset[str], float], ...]
    all_grams: frozenset[str]


def _tokenize(documents: Sequence[SearchDocument]) -> list[_TokenizedDocument]:
    tokenized = []
    for document in documents:
        fields = tuple((bigrams(text), weight) for text, weight in document.weighted_fields)
        all_grams = frozenset().union(*(grams for grams, _ in fields)) if fields else frozenset()
        tokenized.append(_TokenizedDocument(document=document, fields=fields, all_grams=all_grams))
    return tokenized


def inverse_document_frequency(
    query_grams: frozenset[str], tokenized: Sequence[_TokenizedDocument]
) -> dict[str, float]:
    """흔한 글자쌍의 비중을 낮춘다.

    "할수", "있나", "나요" 같은 한국어 의문문 어미는 거의 모든 FAQ에 등장해서,
    가중치를 주지 않으면 짧고 일반적인 질문에서 여러 문서가 동점이 된다(실측으로 확인).
    반대로 코퍼스에 아예 없는 글자쌍은 가장 높은 가중치를 받아, 무관한 질문의 점수를 끌어내린다.
    """
    total = len(tokenized) or 1
    weights = {}
    for gram in query_grams:
        frequency = sum(1 for entry in tokenized if gram in entry.all_grams)
        # 모든 문서에 있는 글자쌍은 가중치 0이 된다(변별력이 없으므로).
        # 코퍼스에 없는 글자쌍은 df=0.5로 취급해 가장 높은 가중치를 준다.
        weights[gram] = math.log(total / (frequency if frequency else 0.5))
    return weights


class KeywordSearcher:
    """글자 bigram + IDF 가중 포함률 기반 검색기 (v1)."""

    def search(self, question: str, documents: Sequence[SearchDocument]) -> list[SearchHit]:
        query_grams = bigrams(question)
        if not query_grams:
            return []
        tokenized = _tokenize(documents)
        weights = inverse_document_frequency(query_grams, tokenized)
        boosted = boosted_categories(question)
        hits = [
            SearchHit(entry.document, self._score(query_grams, entry, weights, boosted))
            for entry in tokenized
        ]
        hits = [hit for hit in hits if hit.score > 0]
        # 점수가 같으면 FAQ를 앞에 둔다. FAQ 답변이 이미 사용자용 문장이라 그대로 보여주기 좋다.
        hits.sort(key=lambda hit: (-hit.score, hit.document.doc_type != FAQ, hit.document.doc_id))
        return hits

    @staticmethod
    def _score(
        query_grams: frozenset[str],
        entry: _TokenizedDocument,
        weights: dict[str, float],
        boosted: frozenset[str],
    ) -> float:
        total_weight = sum(weight for _, weight in entry.fields)
        if total_weight <= 0:
            return 0.0
        # 가중 평균이라 FAQ(필드 2개)와 매뉴얼(필드 3개)의 점수를 같은 척도로 비교할 수 있다.
        weighted_sum = sum(
            weight * containment(query_grams, field_grams, weights)
            for field_grams, weight in entry.fields
        )
        score = weighted_sum / total_weight
        if entry.document.category in boosted:
            score *= CATEGORY_BOOST
        return score
