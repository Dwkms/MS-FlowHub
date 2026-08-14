import { apiDelete, apiGet, apiGetBlob, apiRequest } from "@/lib/api-client";
import type {
  Applicant,
  ApplicantInput,
  ApplicantStage,
  ApplicantUpdateInput,
  JobPosting,
  RecruitmentRequest,
  RecruitmentRequestInput,
} from "@/types/recruitment";

export function listRecruitmentRequests(): Promise<RecruitmentRequest[]> {
  return apiGet("/api/v1/recruitment-requests");
}

export function getRecruitmentRequest(requestId: string): Promise<RecruitmentRequest> {
  return apiGet(`/api/v1/recruitment-requests/${requestId}`);
}

export function createRecruitmentRequest(
  input: RecruitmentRequestInput,
): Promise<RecruitmentRequest> {
  return apiRequest("/api/v1/recruitment-requests", { method: "POST", body: input });
}

export function deleteRecruitmentRequest(requestId: string): Promise<void> {
  return apiDelete(`/api/v1/recruitment-requests/${requestId}`);
}

export function uploadRecruitmentPoster(
  requestId: string,
  poster: File,
): Promise<RecruitmentRequest> {
  const formData = new FormData();
  formData.append("poster", poster);
  return apiRequest(
    `/api/v1/recruitment-requests/${requestId}/poster`,
    { method: "POST", formData },
  );
}

export function getRecruitmentPosterFile(requestId: string): Promise<Blob> {
  return apiGetBlob(`/api/v1/recruitment-requests/${requestId}/poster`);
}

export function submitRecruitmentRequest(
  requestId: string,
): Promise<RecruitmentRequest> {
  return apiRequest(`/api/v1/recruitment-requests/${requestId}/submit`, {
    method: "POST",
    body: {},
  });
}

export function listJobPostings(): Promise<JobPosting[]> {
  return apiGet("/api/v1/job-postings");
}

export function listApplicants(filters?: {
  jobPostingId?: string;
  stage?: ApplicantStage;
  search?: string;
}): Promise<Applicant[]> {
  const params = new URLSearchParams();
  if (filters?.jobPostingId) params.set("job_posting_id", filters.jobPostingId);
  if (filters?.stage) params.set("stage", filters.stage);
  if (filters?.search) params.set("search", filters.search);
  const query = params.toString();
  return apiGet(`/api/v1/applicants${query ? `?${query}` : ""}`);
}

export function getApplicant(applicantId: string): Promise<Applicant> {
  return apiGet(`/api/v1/applicants/${applicantId}`);
}

export function createApplicant(postingId: string, input: ApplicantInput): Promise<Applicant> {
  return apiRequest(`/api/v1/job-postings/${postingId}/applicants`, { method: "POST", body: input });
}

export function updateApplicant(
  applicantId: string,
  input: ApplicantUpdateInput,
): Promise<Applicant> {
  return apiRequest(`/api/v1/applicants/${applicantId}`, { method: "PATCH", body: input });
}

export function updateApplicantStage(
  applicantId: string,
  stage: ApplicantStage,
  note?: string,
): Promise<Applicant> {
  return apiRequest(`/api/v1/applicants/${applicantId}/stage`, {
    method: "POST",
    body: { stage, note: note || null },
  });
}

export function deleteApplicant(applicantId: string): Promise<void> {
  return apiDelete(`/api/v1/applicants/${applicantId}`);
}
