from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AxResultType = Literal["CONFIRMED", "CANDIDATES", "NO_MATCH", "POLICY", "PERSONAL_DATA"]
AxDocumentType = Literal["FAQ", "MANUAL"]


class AxChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    # v1은 단일 턴이다. 이전 대화를 서버로 다시 보내지 않고 매 질문을 독립적으로 처리한다.
    question: str = Field(min_length=1, max_length=300)


class AxSource(BaseModel):
    """답변 카드에 표시할 근거. 제목과 카테고리를 항상 함께 보여준다."""

    doc_type: AxDocumentType
    doc_id: str
    title: str
    category: str
    manual_slug: str | None = None


class AxCandidate(BaseModel):
    """접전일 때 사용자가 고르도록 제시하는 후보."""

    doc_id: str
    title: str
    category: str


class AxChatResponse(BaseModel):
    result_type: AxResultType
    answer: str
    source: AxSource | None = None
    candidates: list[AxCandidate] = Field(default_factory=list)
    route: str | None = None
