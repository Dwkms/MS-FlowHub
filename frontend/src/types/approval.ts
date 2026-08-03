export type ApprovalStatus =
  | "DRAFT"
  | "PENDING"
  | "APPROVED"
  | "REJECTED"
  | "CANCELLED";

export type DocumentType =
  | "GENERAL"
  | "RECRUITMENT_REQUEST"
  | "EXPENSE"
  | "QUOTATION_DISCOUNT";

export interface ApprovalHistory {
  id: string;
  actor_id: string;
  actor_name: string;
  action: string;
  from_status: string | null;
  to_status: string;
  comment: string | null;
  created_at: string;
}

export interface ApprovalDocument {
  id: string;
  document_type: DocumentType;
  title: string;
  content: string;
  department_id: string;
  department_name: string;
  author_id: string;
  author_name: string;
  approver_id: string;
  approver_name: string;
  status: ApprovalStatus;
  decision_comment: string | null;
  submitted_at: string | null;
  processed_at: string | null;
  related_type: string | null;
  related_id: string | null;
  created_at: string;
  updated_at: string;
  histories: ApprovalHistory[];
}

export interface ApprovalCreateInput {
  title: string;
  document_type: DocumentType;
  content: string;
  department_id: string;
  approver_id: string;
}
