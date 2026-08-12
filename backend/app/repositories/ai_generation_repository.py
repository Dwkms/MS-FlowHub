from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai_generation import AiGeneration

# "일일 한도"를 달력 하루가 아니라 **최근 24시간**으로 정의한다. 자정 경계를 쓰면
# 서버·DB·사용자의 시간대가 갈릴 때 한도가 두 배로 열리거나 조기에 막힌다.
WINDOW_HOURS = 24


class AiGenerationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, record: AiGeneration) -> None:
        self.session.add(record)

    def get(self, generation_id: str) -> AiGeneration | None:
        return self.session.get(AiGeneration, generation_id)

    def count_recent(self, *, created_by_id: str | None = None, hours: int = WINDOW_HOURS) -> int:
        """최근 `hours`시간 동안의 호출 수. `created_by_id`가 없으면 전역 합계."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        statement = (
            select(func.count()).select_from(AiGeneration).where(AiGeneration.created_at >= cutoff)
        )
        if created_by_id is not None:
            statement = statement.where(AiGeneration.created_by_id == created_by_id)
        return self.session.scalar(statement) or 0
