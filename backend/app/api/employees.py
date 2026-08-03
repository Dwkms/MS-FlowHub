from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import (
    AuthenticatedActor,
    get_employee_service,
    require_employee_management_permission,
    require_super_admin,
)
from app.schemas.employee import (
    AttendanceStatusUpdate,
    EmployeeCreate,
    EmployeeDetail,
    EmployeeRoleUpdate,
    EmployeeUpdate,
    EmploymentStatusReasonUpdate,
    OrganizationNode,
    PaginatedEmployeeResponse,
)
from app.security.identity import ActorContext
from app.services.employee_service import EmployeeService

router = APIRouter(tags=["Employees"])
Service = Annotated[EmployeeService, Depends(get_employee_service)]
EmployeeManagementActor = Annotated[ActorContext, Depends(require_employee_management_permission)]


@router.get("/employees", response_model=PaginatedEmployeeResponse)
def list_employees(
    service: Service,
    actor: AuthenticatedActor,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    department_code: str | None = None,
    team_code: str | None = None,
    employment_status: str | None = None,
    daily_work_status: str | None = None,
    work_date: date | None = None,
    position: str | None = None,
) -> PaginatedEmployeeResponse:
    return service.list(
        actor,
        page=page,
        page_size=page_size,
        search=search,
        department_code=department_code,
        team_code=team_code,
        employment_status=employment_status,
        daily_work_status=daily_work_status,
        work_date=work_date,
        position=position,
    )


@router.get("/employees/{employee_id}", response_model=EmployeeDetail)
def get_employee(employee_id: str, service: Service, actor: AuthenticatedActor) -> EmployeeDetail:
    return service.detail(employee_id, actor)


@router.post("/employees", response_model=EmployeeDetail, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate, service: Service, actor: EmployeeManagementActor
) -> EmployeeDetail:
    return service.create(payload)


@router.patch("/employees/{employee_id}", response_model=EmployeeDetail)
def update_employee(
    employee_id: str,
    payload: EmployeeUpdate,
    service: Service,
    actor: EmployeeManagementActor,
) -> EmployeeDetail:
    return service.update(employee_id, payload)


@router.patch("/employees/{employee_id}/role", response_model=EmployeeDetail)
def update_employee_role(
    employee_id: str,
    payload: EmployeeRoleUpdate,
    service: Service,
    actor: Annotated[ActorContext, Depends(require_super_admin)],
) -> EmployeeDetail:
    return service.update_role(employee_id, payload, actor)


@router.put("/employees/{employee_id}/attendance", response_model=EmployeeDetail)
def update_attendance_status(
    employee_id: str,
    payload: AttendanceStatusUpdate,
    service: Service,
    actor: AuthenticatedActor,
) -> EmployeeDetail:
    return service.update_attendance_status(employee_id, actor, payload)


@router.patch("/employees/{employee_id}/employment-status-reason", response_model=EmployeeDetail)
def update_employment_status_reason(
    employee_id: str,
    payload: EmploymentStatusReasonUpdate,
    service: Service,
    actor: AuthenticatedActor,
) -> EmployeeDetail:
    return service.update_employment_status_reason(employee_id, actor, payload)


@router.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: str, service: Service, actor: EmployeeManagementActor) -> Response:
    service.deactivate(employee_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/organization", response_model=OrganizationNode)
def organization_tree(service: Service) -> OrganizationNode:
    return service.organization_tree()
