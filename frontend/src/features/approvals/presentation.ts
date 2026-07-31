import type {
  ApprovalStatus,
  DocumentType,
} from "@/types/approval";

export const statusLabels: Record<ApprovalStatus, string> = {
  DRAFT: "임시 저장",
  PENDING: "결재 대기",
  APPROVED: "승인",
  REJECTED: "반려",
  CANCELLED: "취소",
};

export const documentTypeLabels: Record<DocumentType, string> = {
  GENERAL: "일반 품의",
  RECRUITMENT_REQUEST: "채용 요청",
  EXPENSE: "비용 품의",
  QUOTATION_DISCOUNT: "견적 할인",
};

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value));
}

export function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
