"""자동화 테스트 전용 계정을 실제 직원과 구분하는 규칙.

Playwright E2E는 실제 Supabase에 접속해 테스트용 직원을 만들고 끝나면 지웁니다.
그 계정이 직원 목록이나 대시보드 집계에 섞이면 "직원이 48명"처럼 보이고 지표도 틀어집니다.

별도 컬럼(`is_test` 같은)을 두지 않고 **사번 접두어**로 구분하는 이유는, 컬럼을 추가하면
migration이 필요하고 모든 조회에 조건을 걸어야 하는데 접두어는 문자열 검사 하나로 끝나기
때문입니다. E2E는 임시 데이터라 이 정도 단순함이 적당하다고 봤습니다.
"""

E2E_EMPLOYEE_ID_PREFIX = "emp-e2e-"


def is_e2e_employee(employee_id: str) -> bool:
    """이 직원이 E2E 전용 계정인가.

    호출하는 쪽은 보통 이렇게 씁니다 — **E2E 계정으로 로그인했을 때만** E2E 계정이 보이고,
    일반 직원이 보면 목록에서 빠집니다. 테스트 중에도 화면을 확인할 수 있어야 하기 때문입니다.
    """
    return employee_id.startswith(E2E_EMPLOYEE_ID_PREFIX)
