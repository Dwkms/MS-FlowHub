export type RecruitmentStatus =
  | "DRAFT"
  | "PENDING_APPROVAL"
  | "APPROVED"
  | "REJECTED"
  | "POSTING_CREATED";

export interface RecruitmentRequest {
  id: string;
  request_department_id: string;
  request_department_name: string;
  requester_id: string;
  requester_name: string;
  approver_id: string;
  approver_name: string;
  position_title: string;
  headcount: number;
  employment_type: string;
  experience_level: string;
  reason: string;
  responsibilities: string;
  required_skills: string | null;
  preferred_skills: string | null;
  desired_start_date: string | null;
  poster_original_name: string | null;
  poster_content_type: string | null;
  poster_size: number | null;
  status: RecruitmentStatus;
  approval_document_id: string | null;
  job_posting_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface RecruitmentRequestInput {
  request_department_id: string;
  approver_id: string;
  position_title: string;
  headcount: number;
  employment_type: string;
  experience_level: string;
  reason: string;
  responsibilities: string;
  required_skills?: string | null;
  preferred_skills?: string | null;
  desired_start_date?: string | null;
}

export interface JobPosting {
  id: string;
  recruitment_request_id: string;
  request_department_name: string;
  requester_name: string;
  title: string;
  content: string;
  headcount: number;
  employment_type: string;
  experience_level: string;
  responsibilities: string;
  required_skills: string | null;
  preferred_skills: string | null;
  desired_start_date: string | null;
  poster_original_name: string | null;
  poster_content_type: string | null;
  poster_size: number | null;
  status: string;
  created_at: string;
  updated_at: string;
}
