from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain import ax_rules
from app.domain.ax_search import (
    FAQ,
    MAX_CANDIDATES,
    SCORE_CONFIDENT,
    SCORE_FLOOR,
    SCORE_MARGIN,
    DocumentSearcher,
    SearchHit,
    route_for_category,
)
from app.models.ax import AxChatLog
from app.repositories.ax_repository import AxRepository
from app.schemas.ax import AxCandidate, AxChatResponse, AxSource


class AxService:
    """AX 도우미 질의 처리.

    처리 순서는 정책 룰 → v2 안내 룰 → 권한 필터 → 검색 → 응답 5종 분기다.
    정책 룰을 검색보다 먼저 두는 이유는, 검색 점수에 따라 답이 흔들리면 안 되는
    질문이기 때문이다. 업무 데이터는 읽지도 쓰지도 않는다(읽기 전용).
    """

    def __init__(self, session: Session, repository: AxRepository, searcher: DocumentSearcher):
        self.session = session
        self.repository = repository
        self.searcher = searcher

    def answer(self, question: str, role: str) -> AxChatResponse:
        if ax_rules.is_policy_question(question):
            return self._respond(
                question,
                AxChatResponse(result_type=ax_rules.POLICY, answer=ax_rules.POLICY_ANSWER),
                hits=[],
            )
        if ax_rules.is_personal_data_question(question):
            return self._respond(
                question,
                AxChatResponse(
                    result_type=ax_rules.PERSONAL_DATA, answer=ax_rules.PERSONAL_DATA_ANSWER
                ),
                hits=[],
            )

        hits = self.searcher.search(question, self.repository.list_candidate_documents(role))
        return self._respond(question, self._classify(hits), hits)

    def _classify(self, hits: list[SearchHit]) -> AxChatResponse:
        top = hits[0] if hits else None
        if top is None or top.score < SCORE_FLOOR:
            return AxChatResponse(result_type=ax_rules.NO_MATCH, answer=ax_rules.NO_MATCH_ANSWER)

        runner_up = hits[1].score if len(hits) > 1 else 0.0
        if top.score >= SCORE_CONFIDENT and (top.score - runner_up) >= SCORE_MARGIN:
            return AxChatResponse(
                result_type=ax_rules.CONFIRMED,
                answer=top.document.body,
                source=self._source(top),
                route=route_for_category(top.document.category),
            )

        # 접전이면 확신하지 않고 사용자가 고르게 한다. 틀린 답을 자신 있게 내는 것보다 낫다.
        return AxChatResponse(
            result_type=ax_rules.CANDIDATES,
            answer=ax_rules.CANDIDATES_ANSWER,
            candidates=[
                AxCandidate(
                    doc_id=hit.document.doc_id,
                    title=hit.document.title,
                    category=hit.document.category,
                )
                for hit in hits[:MAX_CANDIDATES]
            ],
        )

    def _source(self, hit: SearchHit) -> AxSource:
        document = hit.document
        slug = document.manual_slug
        if document.doc_type == FAQ and document.related_manual_id:
            slug = self.repository.manual_slug_by_id(document.related_manual_id)
        return AxSource(
            doc_type=document.doc_type,
            doc_id=document.doc_id,
            title=document.title,
            category=document.category,
            manual_slug=slug,
        )

    def _respond(
        self, question: str, response: AxChatResponse, hits: list[SearchHit]
    ) -> AxChatResponse:
        self.repository.add_log(
            AxChatLog(
                id=f"ax-log-{uuid4().hex}",
                question_text=question,
                result_type=response.result_type,
                matched_type=response.source.doc_type if response.source else None,
                matched_id=response.source.doc_id if response.source else None,
                top_score=hits[0].score if hits else None,
                top_candidates=[
                    {"doc_id": hit.document.doc_id, "score": round(hit.score, 4)}
                    for hit in hits[:MAX_CANDIDATES]
                ],
            )
        )
        self.session.commit()
        return response
