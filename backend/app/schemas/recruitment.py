from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RecruitmentStatus = Literal[
    "DRAFT",
    "PENDING_APPROVAL",
    "APPROVED",
    "REJECTED",
    "POSTING_CREATED",
]


class RecruitmentBaseModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class RecruitmentRequestCreate(RecruitmentBaseModel):
    request_department_id: str = Field(min_length=1)
    approver_id: str = Field(min_length=1)
    position_title: str = Field(min_length=1, max_length=150)
    headcount: int = Field(gt=0, le=100)
    employment_type: str = Field(min_length=1, max_length=50)
    experience_level: str = Field(min_length=1, max_length=50)
    reason: str = Field(min_length=1)
    responsibilities: str = Field(min_length=1)
    required_skills: str | None = None
    preferred_skills: str | None = None
    desired_start_date: date | None = None


class RecruitmentSubmit(RecruitmentBaseModel):
    comment: str | None = None


class RecruitmentRequestResponse(BaseModel):
    id: str
    request_department_id: str
    request_department_name: str
    requester_id: str
    requester_name: str
    approver_id: str
    approver_name: str
    position_title: str
    headcount: int
    employment_type: str
    experience_level: str
    reason: str
    responsibilities: str
    required_skills: str | None
    preferred_skills: str | None
    desired_start_date: date | None
    poster_original_name: str | None
    poster_content_type: str | None
    poster_size: int | None
    status: RecruitmentStatus
    approval_document_id: str | None
    job_posting_id: str | None
    created_at: datetime
    updated_at: datetime


class JobPostingResponse(BaseModel):
    id: str
    recruitment_request_id: str
    request_department_name: str
    requester_name: str
    title: str
    content: str
    headcount: int
    employment_type: str
    experience_level: str
    responsibilities: str
    required_skills: str | None
    preferred_skills: str | None
    desired_start_date: date | None
    poster_original_name: str | None
    poster_content_type: str | None
    poster_size: int | None
    status: str
    created_at: datetime
    updated_at: datetime
