from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.api.dependencies import get_recruitment_service
from app.schemas.recruitment import (
    JobPostingResponse,
    RecruitmentRequestCreate,
    RecruitmentRequestResponse,
    RecruitmentSubmit,
)
from app.services.recruitment_service import RecruitmentService

router = APIRouter(tags=["Recruitment"])
RecruitmentServiceDependency = Annotated[RecruitmentService, Depends(get_recruitment_service)]


@router.get("/recruitment-requests", response_model=list[RecruitmentRequestResponse])
def list_recruitment_requests(
    service: RecruitmentServiceDependency, employee_id: str = Query(...)
) -> list[RecruitmentRequestResponse]:
    return service.list_requests(employee_id)


@router.post(
    "/recruitment-requests",
    response_model=RecruitmentRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_recruitment_request(
    payload: RecruitmentRequestCreate, service: RecruitmentServiceDependency
) -> RecruitmentRequestResponse:
    return service.create_request(payload)


@router.delete("/recruitment-requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recruitment_request(
    request_id: str,
    service: RecruitmentServiceDependency,
    actor_id: str = Query(...),
) -> None:
    service.delete_request(request_id, actor_id)


@router.post("/recruitment-requests/{request_id}/poster", response_model=RecruitmentRequestResponse)
async def upload_recruitment_poster(
    request_id: str,
    service: RecruitmentServiceDependency,
    poster: Annotated[UploadFile, File(...)],
    actor_id: str = Query(...),
) -> RecruitmentRequestResponse:
    return await service.upload_poster(request_id, actor_id, poster)


@router.get("/recruitment-requests/{request_id}/poster")
def download_recruitment_poster(
    request_id: str,
    service: RecruitmentServiceDependency,
    employee_id: str = Query(...),
) -> FileResponse:
    path, filename, media_type = service.get_poster_file(request_id, employee_id)
    return FileResponse(path, media_type=media_type, filename=filename)


@router.get("/recruitment-requests/{request_id}", response_model=RecruitmentRequestResponse)
def get_recruitment_request(
    request_id: str, service: RecruitmentServiceDependency, employee_id: str = Query(...)
) -> RecruitmentRequestResponse:
    return service.get_request(request_id, employee_id)


@router.post("/recruitment-requests/{request_id}/submit", response_model=RecruitmentRequestResponse)
def submit_recruitment_request(
    request_id: str, payload: RecruitmentSubmit, service: RecruitmentServiceDependency
) -> RecruitmentRequestResponse:
    return service.submit_request(request_id, payload)


@router.post("/recruitment-requests/{request_id}/job-posting", response_model=JobPostingResponse)
def create_job_posting(
    request_id: str, service: RecruitmentServiceDependency, actor_id: str = Query(...)
) -> JobPostingResponse:
    return service.create_posting(request_id, actor_id)


@router.get("/job-postings", response_model=list[JobPostingResponse])
def list_job_postings(
    service: RecruitmentServiceDependency, employee_id: str = Query(...)
) -> list[JobPostingResponse]:
    return service.list_postings(employee_id)
