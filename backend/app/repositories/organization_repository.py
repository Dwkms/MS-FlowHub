from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Department, Employee
from app.schemas.common import DepartmentResponse, EmployeeResponse

_ROLE_LABELS = {
    "EMPLOYEE": "일반 직원",
    "DEPARTMENT_HEAD": "부서장",
    "HR_MANAGER": "인사 담당자",
    "SALES_REP": "영업사원",
    "SALES_MANAGER": "영업팀장",
    "ADMIN": "관리자",
}

_SAMPLE_DEPARTMENTS = [
    {"id": "dept-development", "code": "DEV", "name": "개발팀"},
    {"id": "dept-finance", "code": "FINANCE", "name": "재무팀"},
    {"id": "dept-hr", "code": "HR", "name": "인사팀"},
    {"id": "dept-sales", "code": "SALES", "name": "영업팀"},
    {"id": "dept-product", "code": "PRODUCT", "name": "서비스기획팀"},
]

_SAMPLE_EMPLOYEES = [
    {
        "id": "emp-head",
        "employee_no": "MS-1001",
        "name": "김민성",
        "email": "minseong.kim@example.invalid",
        "role": "ADMIN",
        "department_id": "dept-product",
    },
    {
        "id": "emp-hr",
        "employee_no": "MS-2001",
        "name": "박지우",
        "email": "jiwoo.park@example.invalid",
        "role": "HR_MANAGER",
        "department_id": "dept-hr",
    },
    {
        "id": "emp-sales",
        "employee_no": "MS-3001",
        "name": "이도윤",
        "email": "doyoon.lee@example.invalid",
        "role": "SALES_REP",
        "department_id": "dept-sales",
    },
    {
        "id": "emp-sales-head",
        "employee_no": "MS-3002",
        "name": "최서윤",
        "email": "seoyoon.choi@example.invalid",
        "role": "SALES_MANAGER",
        "department_id": "dept-sales",
    },
    {
        "id": "emp-product-head",
        "employee_no": "MS-4001",
        "name": "한유진",
        "email": "yujin.han@example.invalid",
        "role": "DEPARTMENT_HEAD",
        "department_id": "dept-product",
    },
]


class OrganizationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def seed_sample_organization(self) -> None:
        for item in _SAMPLE_DEPARTMENTS:
            if self.session.get(Department, item["id"]) is None:
                self.session.add(Department(**item))
        self.session.flush()
        for item in _SAMPLE_EMPLOYEES:
            employee = self.session.get(Employee, item["id"])
            if employee is None:
                self.session.add(Employee(**item))
                continue
            for field, value in item.items():
                setattr(employee, field, value)

    def list_departments(self) -> list[DepartmentResponse]:
        departments = self.session.scalars(select(Department).order_by(Department.name)).all()
        return [
            DepartmentResponse(id=item.id, code=item.code, name=item.name) for item in departments
        ]

    def list_employees(self) -> list[EmployeeResponse]:
        statement = (
            select(Employee, Department)
            .join(Department, Department.id == Employee.department_id)
            .where(Employee.is_active.is_(True))
            .order_by(Employee.employee_no)
        )
        return [
            self._to_employee(item, department)
            for item, department in self.session.execute(statement)
        ]

    def get_employee(self, employee_id: str) -> EmployeeResponse | None:
        statement = (
            select(Employee, Department)
            .join(Department, Department.id == Employee.department_id)
            .where(Employee.id == employee_id, Employee.is_active.is_(True))
        )
        row = self.session.execute(statement).one_or_none()
        if row is None:
            return None
        return self._to_employee(row[0], row[1])

    def get_department(self, department_id: str) -> DepartmentResponse | None:
        department = self.session.get(Department, department_id)
        if department is None:
            return None
        return DepartmentResponse(id=department.id, code=department.code, name=department.name)

    @staticmethod
    def _to_employee(employee: Employee, department: Department) -> EmployeeResponse:
        return EmployeeResponse(
            id=employee.id,
            employee_no=employee.employee_no,
            name=employee.name,
            role=employee.role,
            role_label=_ROLE_LABELS[employee.role],
            department_id=employee.department_id,
            department_name=department.name,
        )
