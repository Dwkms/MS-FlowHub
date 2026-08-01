from datetime import date, datetime

from sqlalchemy import (
    Boolean,
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


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    employee_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    team_id: Mapped[str | None] = mapped_column(
        ForeignKey("teams.id", ondelete="RESTRICT"), nullable=True
    )
    position: Mapped[str] = mapped_column(String(50), default="사원", nullable=False)
    job_title: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    job_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    manager_id: Mapped[str | None] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), nullable=True
    )
    employment_type: Mapped[str] = mapped_column(String(30), default="REGULAR", nullable=False)
    employment_status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    employment_status_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    employment_status_reason_category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    employment_status_reason_summary: Mapped[str | None] = mapped_column(String(200), nullable=True)
    employment_status_private_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    employment_status_reason_registered_by_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    employment_status_reason_registered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    employment_status_effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    hire_date: Mapped[date | None] = mapped_column(nullable=True)
    phone_extension: Mapped[str | None] = mapped_column(String(20), nullable=True)
    work_location: Mapped[str] = mapped_column(String(100), default="서울 본사", nullable=False)
    profile_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("employee_id", "work_date", name="uq_attendance_employee_date"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    work_status: Mapped[str] = mapped_column(String(30), nullable=False)
    check_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason_category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reason_summary: Mapped[str | None] = mapped_column(String(200), nullable=True)
    private_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason_registered_by_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reason_registered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
