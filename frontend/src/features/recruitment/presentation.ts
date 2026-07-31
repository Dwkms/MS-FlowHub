import type { RecruitmentStatus } from "@/types/recruitment";

export const recruitmentStatusLabels: Record<RecruitmentStatus, string> = {
  DRAFT: "임시 저장",
  PENDING_APPROVAL: "결재 대기",
  APPROVED: "승인",
  REJECTED: "반려",
  POSTING_CREATED: "공고 생성",
};
