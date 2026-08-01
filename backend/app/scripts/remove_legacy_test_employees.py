"""Remove only the five legacy placeholder employees created before organization seeding."""

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.models.organization import Employee

LEGACY_TEST_EMPLOYEE_IDS = (
    "emp-head",
    "emp-hr",
    "emp-sales",
    "emp-sales-head",
    "emp-product-head",
)


def main() -> None:
    with SessionLocal() as session:
        employees = session.scalars(
            select(Employee).where(Employee.id.in_(LEGACY_TEST_EMPLOYEE_IDS))
        ).all()
        if not employees:
            print("No legacy test employees found.")
            return

        try:
            session.execute(delete(Employee).where(Employee.id.in_(LEGACY_TEST_EMPLOYEE_IDS)))
            session.commit()
        except IntegrityError as error:
            session.rollback()
            raise RuntimeError(
                "Legacy test employees are referenced by existing business data. "
                "Reassign or remove the related test records before deleting them."
            ) from error

        print(f"Removed {len(employees)} legacy test employees.")


if __name__ == "__main__":
    main()
