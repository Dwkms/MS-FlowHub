import { apiRequest } from "@/lib/api-client";
import type {
  ApprovalDraftOutput,
  ApprovalDraftRequest,
  ApprovalDraftResponse,
} from "@/types/ai";

export function createApprovalDraft(
  payload: ApprovalDraftRequest,
): Promise<ApprovalDraftResponse> {
  return apiRequest<ApprovalDraftResponse>("/api/v1/ai/approval-drafts", {
    method: "POST",
    body: payload,
  });
}

/** 사용자가 수정해 실제로 적용한 최종본을 기록한다. AI 최초 결과는 덮어쓰지 않는다. */
export function recordFinalOutput(
  generationId: string,
  finalOutput: ApprovalDraftOutput,
): Promise<void> {
  return apiRequest<void>(`/api/v1/ai/generations/${generationId}/final`, {
    method: "PATCH",
    body: { final_output: finalOutput },
  });
}
