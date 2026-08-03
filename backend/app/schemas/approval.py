from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ApprovalStatus = Literal["DRAFT", "PENDING", "APPROVED", "REJECTED", "CANCELLED"]
DocumentType = Literal["GENERAL", "RECRUITMENT_REQUEST", "EXPENSE", "QUOTATION_DISCOUNT"]


class ApprovalBaseModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class ApprovalCreate(ApprovalBaseModel):
    title: str = Field(min_length=1, max_length=200)
    document_type: DocumentType
    content: str = Field(min_length=1)
    department_id: str = Field(min_length=1)
    approver_id: str = Field(min_length=1)


class ApprovalUpdate(ApprovalBaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    document_type: DocumentType | None = None
    content: str | None = Field(default=None, min_length=1)
    department_id: str | None = Field(default=None, min_length=1)
    approver_id: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def require_change(self) -> "ApprovalUpdate":
        fields = ("title", "document_type", "content", "department_id", "approver_id")
        if not any(getattr(self, field) is not None for field in fields):
            raise ValueError("수정할 항목을 하나 이상 입력해야 합니다.")
        return self


class ApprovalAction(ApprovalBaseModel):
    comment: str | None = None


class ApprovalSubmit(ApprovalBaseModel):
    comment: str | None = None


class ApprovalReject(ApprovalBaseModel):
    comment: str = Field(min_length=1)


class ApprovalHistoryResponse(BaseModel):
    id: str
    actor_id: str
    actor_name: str
    action: str
    from_status: str | None
    to_status: str
    comment: str | None
    created_at: datetime


class ApprovalResponse(BaseModel):
    id: str
    document_type: str
    title: str
    content: str
    department_id: str
    department_name: str
    author_id: str
    author_name: str
    approver_id: str
    approver_name: str
    status: ApprovalStatus
    decision_comment: str | None
    submitted_at: datetime | None
    processed_at: datetime | None
    related_type: str | None
    related_id: str | None
    created_at: datetime
    updated_at: datetime
    histories: list[ApprovalHistoryResponse] = []
