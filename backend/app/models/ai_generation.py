from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AiGeneration(Base):
    """생성형 AI 호출 1건의 기록.

    `generated_output`(AI 최초 결과)과 `final_output`(사용자가 수정해 적용한 결과)을
    분리한다. 둘을 한 칼럼에 담으면 "AI가 뭘 냈고 사람이 뭘 고쳤는지"를 잃는다.
    재실행은 기존 행을 덮어쓰지 않고 새 행을 만든다.

    `input_tokens`/`output_tokens`는 비용 추적용이다. Console을 열지 않고도 쿼리 하나로
    실지출을 계산해 이상 급증을 조기에 발견한다(docs/AI_AUTOMATION_PLAN.md 13장·19장).
    """

    __tablename__ = "ai_generations"
    __table_args__ = (
        Index("ix_ai_generations_feature_created", "feature_type", "created_at"),
        Index("ix_ai_generations_related", "related_type", "related_id"),
        # 일일 호출 제한 조회용(19장·20장).
        Index("ix_ai_generations_creator_created", "created_by_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    feature_type: Mapped[str] = mapped_column(String(40), nullable=False)
    related_type: Mapped[str | None] = mapped_column(String(40))
    related_id: Mapped[str | None] = mapped_column(String(50))
    source_input: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    generated_output: Mapped[dict | None] = mapped_column(JSON)
    final_output: Mapped[dict | None] = mapped_column(JSON)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(100))
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    created_by_id: Mapped[str] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    # 일일 한도 계산이 `created_at`을 Python에서 만든 시각과 비교하므로, 저장 값도
    # 같은 경로에서 만든다. server_default는 직접 INSERT하는 경우의 안전망이다.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now(), nullable=False
    )
