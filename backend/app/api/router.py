from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.ai import router as ai_router
from app.api.approvals import router as approvals_router
from app.api.auth import router as auth_router
from app.api.ax import router as ax_router
from app.api.dependencies import AuthenticatedActor, get_dashboard_service
from app.api.employees import router as employees_router
from app.api.faqs import router as faqs_router
from app.api.manuals import router as manuals_router
from app.api.recruitment import router as recruitment_router
from app.schemas.common import DashboardResponse, DepartmentResponse, EmployeeResponse
from app.services.dashboard_service import DashboardService

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(approvals_router)
api_router.include_router(recruitment_router)
api_router.include_router(employees_router)
api_router.include_router(manuals_router)
api_router.include_router(faqs_router)
api_router.include_router(ax_router)
api_router.include_router(ai_router)
DashboardServiceDependency = Annotated[DashboardService, Depends(get_dashboard_service)]


@api_router.get("/departments", response_model=list[DepartmentResponse], tags=["Departments"])
def list_departments(service: DashboardServiceDependency) -> list[DepartmentResponse]:
    return service.list_departments()


@api_router.get("/employee-options", response_model=list[EmployeeResponse], tags=["Employees"])
def list_employees(service: DashboardServiceDependency) -> list[EmployeeResponse]:
    return service.list_employees()


@api_router.get("/dashboard", response_model=DashboardResponse, tags=["Dashboard"])
def get_dashboard(
    service: DashboardServiceDependency,
    actor: AuthenticatedActor,
) -> DashboardResponse:
    return service.get_dashboard(actor.employee_id, actor.role)
