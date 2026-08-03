import pytest
from fastapi import HTTPException

from app.api.dependencies import (
    require_approval_permission,
    require_employee_management_permission,
    require_hr_admin,
    require_super_admin,
    require_team_admin,
)
from app.security.identity import ActorContext


def actor(role: str) -> ActorContext:
    return ActorContext(employee_id="employee-1", role=role, auth_user_id="auth-1")


@pytest.mark.parametrize(
    ("dependency", "allowed_role"),
    [
        (require_super_admin, "SUPER_ADMIN"),
        (require_hr_admin, "HR_ADMIN"),
        (require_team_admin, "TEAM_ADMIN"),
        (require_employee_management_permission, "HR_ADMIN"),
        (require_approval_permission, "EMPLOYEE"),
    ],
)
def test_role_dependency_allows_expected_role(dependency, allowed_role):
    assert dependency(actor(allowed_role)).role == allowed_role


@pytest.mark.parametrize(
    ("dependency", "blocked_role"),
    [
        (require_super_admin, "HR_ADMIN"),
        (require_hr_admin, "TEAM_ADMIN"),
        (require_team_admin, "EMPLOYEE"),
        (require_employee_management_permission, "TEAM_ADMIN"),
    ],
)
def test_role_dependency_rejects_insufficient_role(dependency, blocked_role):
    with pytest.raises(HTTPException) as error:
        dependency(actor(blocked_role))

    assert error.value.status_code == 403
