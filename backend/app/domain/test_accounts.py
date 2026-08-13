"""실제 직원 화면에서 자동화 전용 계정을 구분하는 규칙."""

E2E_EMPLOYEE_ID_PREFIX = "emp-e2e-"


def is_e2e_employee(employee_id: str) -> bool:
    return employee_id.startswith(E2E_EMPLOYEE_ID_PREFIX)
