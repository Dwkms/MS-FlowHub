import { apiDelete, apiGet, apiRequest } from "@/lib/api-client";
import type {
  JobPosting,
  RecruitmentRequest,
  RecruitmentRequestInput,
} from "@/types/recruitment";

export function listRecruitmentRequests(employeeId: string): Promise<RecruitmentRequest[]> {
  return apiGet(`/api/v1/recruitment-requests?employee_id=${encodeURIComponent(employeeId)}`);
}

export function getRecruitmentRequest(
  requestId: string,
  employeeId: string,
): Promise<RecruitmentRequest> {
  return apiGet(
    `/api/v1/recruitment-requests/${requestId}?employee_id=${encodeURIComponent(employeeId)}`,
  );
}

export function createRecruitmentRequest(
  input: RecruitmentRequestInput,
): Promise<RecruitmentRequest> {
  return apiRequest("/api/v1/recruitment-requests", { method: "POST", body: input });
}

export function deleteRecruitmentRequest(requestId: string, actorId: string): Promise<void> {
  return apiDelete(
    `/api/v1/recruitment-requests/${requestId}?actor_id=${encodeURIComponent(actorId)}`,
  );
}

export function uploadRecruitmentPoster(
  requestId: string,
  actorId: string,
  poster: File,
): Promise<RecruitmentRequest> {
  const formData = new FormData();
  formData.append("poster", poster);
  return apiRequest(
    `/api/v1/recruitment-requests/${requestId}/poster?actor_id=${encodeURIComponent(actorId)}`,
    { method: "POST", formData },
  );
}

export function getRecruitmentPosterUrl(requestId: string, employeeId: string): string {
  return `/api/v1/recruitment-requests/${requestId}/poster?employee_id=${encodeURIComponent(employeeId)}`;
}

export function submitRecruitmentRequest(
  requestId: string,
  actorId: string,
): Promise<RecruitmentRequest> {
  return apiRequest(`/api/v1/recruitment-requests/${requestId}/submit`, {
    method: "POST",
    body: { actor_id: actorId },
  });
}

export function listJobPostings(employeeId: string): Promise<JobPosting[]> {
  return apiGet(`/api/v1/job-postings?employee_id=${encodeURIComponent(employeeId)}`);
}
