from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.ax_search import (
    FAQ,
    MANUAL,
    WEIGHT_FAQ_ANSWER,
    WEIGHT_FAQ_QUESTION,
    WEIGHT_MANUAL_CONTENT,
    WEIGHT_MANUAL_SUMMARY,
    WEIGHT_MANUAL_TITLE,
    SearchDocument,
)
from app.models.ax import AxChatLog
from app.models.manual import Manual, ManualFaq


class AxRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_candidate_documents(self, role: str) -> list[SearchDocument]:
        """권한을 통과한 문서만 검색 후보로 만든다.

        `target_roles`는 JSON 배열이라 SQLite/PostgreSQL에서 이식성 있게 SQL 필터를
        걸기 어렵다. 그래서 조회 직후 여기서 걸러낸다. 중요한 것은 **응답을 만든 뒤
        걸러내지 않는다**는 점이다. 권한 밖 문서는 검색기까지 도달하지 않는다.
        """
        documents = [
            SearchDocument(
                doc_type=FAQ,
                doc_id=faq.id,
                category=faq.category,
                title=faq.question,
                body=faq.answer,
                weighted_fields=(
                    (faq.question, WEIGHT_FAQ_QUESTION),
                    (faq.answer, WEIGHT_FAQ_ANSWER),
                ),
                related_manual_id=faq.related_manual_id,
            )
            for faq in self.session.scalars(
                select(ManualFaq).where(ManualFaq.is_published.is_(True))
            )
        ]
        for manual in self.session.scalars(select(Manual).where(Manual.status == "PUBLISHED")):
            if role not in (manual.target_roles or []):
                continue
            documents.append(
                SearchDocument(
                    doc_type=MANUAL,
                    doc_id=manual.id,
                    category=manual.category.name,
                    title=manual.title,
                    body=manual.summary,
                    weighted_fields=(
                        (manual.title, WEIGHT_MANUAL_TITLE),
                        (manual.summary, WEIGHT_MANUAL_SUMMARY),
                        (manual.content, WEIGHT_MANUAL_CONTENT),
                    ),
                    manual_slug=manual.slug,
                )
            )
        return documents

    def manual_slug_by_id(self, manual_id: str) -> str | None:
        return self.session.scalar(select(Manual.slug).where(Manual.id == manual_id))

    def add_log(self, log: AxChatLog) -> None:
        self.session.add(log)
