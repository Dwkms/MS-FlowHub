from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AxChatLog(Base):
    """AX 도우미 질문 로그. 품질 개선에 필요한 최소 항목만 남긴다.

    `employee_id`를 저장하지 않는다(익명). 품질 개선에는 누가 물었는지가 필요 없고,
    46명 규모 조직에서 "누가 병가 관련 질문을 했는지"가 남으면 그 자체로 민감 정보가 된다.
    설계 근거는 docs/AX_FAQ_CHATBOT_PLAN.md 7장 참조.
    """

    __tablename__ = "ax_chat_logs"
    __table_args__ = (Index("ix_ax_chat_logs_result_created", "result_type", "created_at"),)

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    result_type: Mapped[str] = mapped_column(String(20), nullable=False)
    matched_type: Mapped[str | None] = mapped_column(String(20))
    matched_id: Mapped[str | None] = mapped_column(String(50))
    top_score: Mapped[float | None] = mapped_column(Float)
    # 상위 3개 후보의 문서 ID와 점수. 실패 원인을 "순위 문제"와 "문서 부재"로
    # 구분하기 위해 남긴다. 이 구분이 v2에서 임베딩 도입 여부를 판단하는 근거다.
    top_candidates: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
