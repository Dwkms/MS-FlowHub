from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status

from app.api.dependencies import AuthenticatedActor, get_recruitment_service
from app.schemas.recruitment import (
    ApplicantCreate,
    ApplicantResponse,
    ApplicantStageUpdate,
    ApplicantUpdate,
    JobPostingResponse,
    JobPostingUpdate,
    RecruitmentRequestCreate,
    RecruitmentRequestResponse,
    RecruitmentSubmit,
)
from app.services.recruitment_service import RecruitmentService

router = APIRouter(tags=["Recruitment"])
RecruitmentServiceDependency = Annotated[RecruitmentService, Depends(get_recruitment_service)]
APPLICANT_STAGE_PATTERN = "^(APPLIED|SCREENING|INTERVIEW|OFFERED|HIRED|REJECTED)$"


@router.get("/recruitment-requests", response_model=list[RecruitmentRequestResponse])
def list_recruitment_requests(
    service: RecruitmentServiceDependency, actor: AuthenticatedActor
) -> list[RecruitmentRequestResponse]:
    return service.list_requests(actor)


@router.post(
    "/recruitment-requests",
    response_model=RecruitmentRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_recruitment_request(
    payload: RecruitmentRequestCreate,
    service: RecruitmentServiceDependency,
    actor: AuthenticatedActor,
) -> RecruitmentRequestResponse:
    return service.create_request(payload, actor)


@router.delete("/recruitment-requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recruitment_request(
    request_id: str,
    service: RecruitmentServiceDependency,
    actor: AuthenticatedActor,
) -> None:
    service.delete_request(request_id, actor)


@router.post("/recruitment-requests/{request_id}/poster", response_model=RecruitmentRequestResponse)
async def upload_recruitment_poster(
    request_id: str,
    service: RecruitmentServiceDependency,
    poster: Annotated[UploadFile, File(...)],
    actor: AuthenticatedActor,
) -> RecruitmentRequestResponse:
    return await service.upload_poster(request_id, actor, poster)


@router.get("/recruitment-requests/{request_id}/poster")
def download_recruitment_poster(
    request_id: str,
    service: RecruitmentServiceDependency,
    actor: AuthenticatedActor,
) -> Response:
    content, filename, media_type = service.get_poster_file(request_id, actor)
    ascii_fallback = filename.encode("ascii", "ignore").decode("ascii") or "poster"
    disposition = f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{quote(filename)}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": disposition},
    )


@router.get("/recruitment-requests/{request_id}", response_model=RecruitmentRequestResponse)
def get_recruitment_request(
    request_id: str, service: RecruitmentServiceDependency, actor: AuthenticatedActor
) -> RecruitmentRequestResponse:
    return service.get_request(request_id, actor)


@router.post("/recruitment-requests/{request_id}/submit", response_model=RecruitmentRequestResponse)
def submit_recruitment_request(
    request_id: str,
    payload: RecruitmentSubmit,
    service: RecruitmentServiceDependency,
    actor: AuthenticatedActor,
) -> RecruitmentRequestResponse:
    return service.submit_request(request_id, payload, actor)


@router.post("/recruitment-requests/{request_id}/job-posting", response_model=JobPostingResponse)
def create_job_posting(
    request_id: str, service: RecruitmentServiceDependency, actor: AuthenticatedActor
) -> JobPostingResponse:
    return service.create_posting(request_id, actor)


@router.patch("/job-postings/{posting_id}", response_model=JobPostingResponse)
def update_job_posting(
    posting_id: str,
    payload: JobPostingUpdate,
    service: RecruitmentServiceDependency,
    actor: AuthenticatedActor,
) -> JobPostingResponse:
    """채용공고 제목·본문을 수정합니다. 게시 상태(`status`)는 변경할 수 없습니다."""
    return service.update_posting(posting_id, payload, actor)


@router.get("/job-postings", response_model=list[JobPostingResponse])
def list_job_postings(
    service: RecruitmentServiceDependency, actor: AuthenticatedActor
) -> list[JobPostingResponse]:
    return service.list_postings(actor)


@router.get("/applicants", response_model=list[ApplicantResponse])
def list_applicants(
    service: RecruitmentServiceDependency,
    actor: AuthenticatedActor,
    job_posting_id: str | None = None,
    stage: str | None = Query(default=None, pattern=APPLICANT_STAGE_PATTERN),
    search: str | None = None,
) -> list[ApplicantResponse]:
    return service.list_applicants(
        job_posting_id=job_posting_id, stage=stage, search=search, actor=actor
    )


@router.post(
    "/job-postings/{posting_id}/applicants",
    response_model=ApplicantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_applicant(
    posting_id: str,
    payload: ApplicantCreate,
    service: RecruitmentServiceDependency,
    actor: AuthenticatedActor,
) -> ApplicantResponse:
    return service.create_applicant(posting_id, payload, actor)


@router.get("/applicants/{applicant_id}", response_model=ApplicantResponse)
def get_applicant(
    applicant_id: str, service: RecruitmentServiceDependency, actor: AuthenticatedActor
) -> ApplicantResponse:
    return service.get_applicant(applicant_id, actor)


@router.patch("/applicants/{applicant_id}", response_model=ApplicantResponse)
def update_applicant(
    applicant_id: str,
    payload: ApplicantUpdate,
    service: RecruitmentServiceDependency,
    actor: AuthenticatedActor,
) -> ApplicantResponse:
    return service.update_applicant(applicant_id, payload, actor)


@router.post("/applicants/{applicant_id}/stage", response_model=ApplicantResponse)
def change_applicant_stage(
    applicant_id: str,
    payload: ApplicantStageUpdate,
    service: RecruitmentServiceDependency,
    actor: AuthenticatedActor,
) -> ApplicantResponse:
    return service.change_applicant_stage(applicant_id, payload, actor)


@router.delete("/applicants/{applicant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_applicant(
    applicant_id: str, service: RecruitmentServiceDependency, actor: AuthenticatedActor
) -> None:
    service.delete_applicant(applicant_id, actor)
