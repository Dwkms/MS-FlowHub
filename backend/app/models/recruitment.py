from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RecruitmentRequest(Base):
    __tablename__ = "recruitment_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT','PENDING_APPROVAL','APPROVED','REJECTED','POSTING_CREATED')",
            name="ck_recruitment_requests_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    requester_id: Mapped[str] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    approver_id: Mapped[str] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    position_title: Mapped[str] = mapped_column(String(150), nullable=False)
    headcount: Mapped[int] = mapped_column(Integer, nullable=False)
    employment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    experience_level: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    responsibilities: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[str | None] = mapped_column(Text)
    preferred_skills: Mapped[str | None] = mapped_column(Text)
    desired_start_date: Mapped[date | None] = mapped_column(Date)
    poster_original_name: Mapped[str | None] = mapped_column(String(255))
    poster_stored_name: Mapped[str | None] = mapped_column(String(100))
    poster_content_type: Mapped[str | None] = mapped_column(String(100))
    poster_size: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False, index=True)
    approval_document_id: Mapped[str | None] = mapped_column(
        ForeignKey("approval_documents.id", ondelete="RESTRICT"), unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    recruitment_request_id: Mapped[str] = mapped_column(
        ForeignKey("recruitment_requests.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Applicant(Base):
    __tablename__ = "applicants"
    __table_args__ = (
        UniqueConstraint("job_posting_id", "email", name="uq_applicants_posting_email"),
        CheckConstraint(
            "stage IN ('APPLIED','SCREENING','INTERVIEW','OFFERED','HIRED','REJECTED')",
            name="ck_applicants_stage",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_posting_id: Mapped[str] = mapped_column(
        ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    career_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    stage: Mapped[str] = mapped_column(String(20), default="APPLIED", nullable=False, index=True)
    created_by_id: Mapped[str] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ApplicantStageHistory(Base):
    __tablename__ = "applicant_stage_histories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    applicant_id: Mapped[str] = mapped_column(
        ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_stage: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_stage: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_id: Mapped[str] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
