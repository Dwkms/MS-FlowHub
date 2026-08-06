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
ApplicantStage = Literal["APPLIED", "SCREENING", "INTERVIEW", "OFFERED", "HIRED", "REJECTED"]


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


class ApplicantCreate(RecruitmentBaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    career_summary: str = Field(default="", max_length=5000)


class ApplicantUpdate(RecruitmentBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    career_summary: str | None = Field(default=None, max_length=5000)


class ApplicantStageUpdate(RecruitmentBaseModel):
    stage: ApplicantStage
    note: str | None = Field(default=None, max_length=2000)


class ApplicantStageHistoryResponse(BaseModel):
    id: str
    from_stage: ApplicantStage | None
    to_stage: ApplicantStage
    note: str | None
    actor_id: str
    actor_name: str
    created_at: datetime


class ApplicantResponse(BaseModel):
    id: str
    job_posting_id: str
    job_posting_title: str
    request_department_id: str
    request_department_name: str
    name: str
    email: str
    phone: str | None
    career_summary: str
    stage: ApplicantStage
    created_by_id: str
    created_by_name: str
    created_at: datetime
    updated_at: datetime
    stage_histories: list[ApplicantStageHistoryResponse] = Field(default_factory=list)
