import { apiDelete, apiGet, apiGetBlob, apiRequest } from "@/lib/api-client";
import type {
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
