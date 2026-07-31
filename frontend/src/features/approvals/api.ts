import { apiDelete, apiGet, apiRequest } from "@/lib/api-client";
import type {
  ApprovalCreateInput,
  ApprovalDocument,
  ApprovalStatus,
} from "@/types/approval";

interface ApprovalListQuery {
  employeeId?: string;
  search?: string;
  status?: ApprovalStatus | "";
}

export function listApprovals(query: ApprovalListQuery): Promise<ApprovalDocument[]> {
  const params = new URLSearchParams();
  if (query.employeeId) params.set("employee_id", query.employeeId);
  if (query.search) params.set("search", query.search);
  if (query.status) params.set("status", query.status);
  const suffix = params.size > 0 ? `?${params.toString()}` : "";
  return apiGet<ApprovalDocument[]>(`/api/v1/approvals${suffix}`);
}

export function getApproval(documentId: string): Promise<ApprovalDocument> {
  return apiGet<ApprovalDocument>(`/api/v1/approvals/${documentId}`);
}

export function createApproval(
  input: ApprovalCreateInput,
): Promise<ApprovalDocument> {
  return apiRequest<ApprovalDocument>("/api/v1/approvals", {
    method: "POST",
    body: input,
  });
}

export function updateApproval(
  documentId: string,
  input: Partial<ApprovalCreateInput> & { actor_id: string },
): Promise<ApprovalDocument> {
  return apiRequest<ApprovalDocument>(`/api/v1/approvals/${documentId}`, {
    method: "PATCH",
    body: input,
  });
}

export function deleteApproval(documentId: string, actorId: string): Promise<void> {
  const params = new URLSearchParams({ actor_id: actorId });
  return apiDelete(`/api/v1/approvals/${documentId}?${params.toString()}`);
}

export function submitApproval(
  documentId: string,
  actorId: string,
  comment?: string,
): Promise<ApprovalDocument> {
  return apiRequest<ApprovalDocument>(
    `/api/v1/approvals/${documentId}/submit`,
    {
      method: "POST",
      body: { actor_id: actorId, comment: comment || null },
    },
  );
}

export function approveApproval(
  documentId: string,
  actorId: string,
  comment?: string,
): Promise<ApprovalDocument> {
  return apiRequest<ApprovalDocument>(
    `/api/v1/approvals/${documentId}/approve`,
    {
      method: "POST",
      body: { actor_id: actorId, comment: comment || null },
    },
  );
}

export function rejectApproval(
  documentId: string,
  actorId: string,
  comment: string,
): Promise<ApprovalDocument> {
  return apiRequest<ApprovalDocument>(
    `/api/v1/approvals/${documentId}/reject`,
    {
      method: "POST",
      body: { actor_id: actorId, comment },
    },
  );
}
