"""Assign varied test work statuses to ten active employees for today."""

from datetime import UTC, date, datetime, time
from random import SystemRandom

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.organization import AttendanceRecord, Employee

WORK_STATUSES = (
    "WORKING",
    "REMOTE_WORK",
    "OUT_OF_OFFICE",
    "BUSINESS_TRIP",
    "ANNUAL_LEAVE",
    "MORNING_HALF",
    "AFTERNOON_HALF",
    "SICK_LEAVE",
    "TRAINING",
    "OFF_WORK",
)
WORK_STATUS_REASONS = {
    "REMOTE_WORK": ("WORK", "집중 문서 작업", None),
    "OUT_OF_OFFICE": ("BUSINESS", "외부 협력사 방문", None),
    "BUSINESS_TRIP": ("BUSINESS", "고객사 미팅 참석", None),
    "ANNUAL_LEAVE": ("PERSONAL", "개인 일정", None),
    "MORNING_HALF": ("HEALTH", "오전 병원 진료", None),
    "AFTERNOON_HALF": ("PERSONAL", "가족 일정", None),
    "SICK_LEAVE": ("HEALTH", "감기 증상으로 휴식", "회복을 위해 병원 진료 후 휴식"),
    "TRAINING": ("TRAINING", "직무 역량 교육 참석", None),
}


def main() -> None:
    today = date.today()
    with SessionLocal() as session:
        employees = session.scalars(
            select(Employee)
            .where(Employee.employment_status == "ACTIVE")
            .order_by(Employee.employee_no)
        ).all()
        selected = SystemRandom().sample(employees, k=min(10, len(employees)))
        for index, employee in enumerate(selected):
            record = session.scalar(
                select(AttendanceRecord).where(
                    AttendanceRecord.employee_id == employee.id,
                    AttendanceRecord.work_date == today,
                )
            )
            status = WORK_STATUSES[index % len(WORK_STATUSES)]
            if record is None:
                record = AttendanceRecord(
                    id=f"attendance-{today.isoformat()}-{employee.id}",
                    employee_id=employee.id,
                    work_date=today,
                    work_status=status,
                )
                session.add(record)
            record.work_status = status
            reason = WORK_STATUS_REASONS.get(status)
            if reason:
                record.reason_category, record.reason_summary, record.private_note = reason
                record.note = record.reason_summary
                record.reason_registered_by_id = employee.id
                record.reason_registered_at = datetime.now(UTC)
            else:
                record.note = None
                record.reason_category = None
                record.reason_summary = None
                record.private_note = None
                record.reason_registered_by_id = None
                record.reason_registered_at = None
            record.check_in_at = (
                datetime.combine(today, time(9, 0), tzinfo=UTC)
                if status in {"WORKING", "REMOTE_WORK", "OUT_OF_OFFICE", "BUSINESS_TRIP"}
                else None
            )
            record.check_out_at = None
        session.commit()
        print(f"Updated today's work status for {len(selected)} employees.")


if __name__ == "__main__":
    main()
