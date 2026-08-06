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

export type ApplicantStage =
  | "APPLIED"
  | "SCREENING"
  | "INTERVIEW"
  | "OFFERED"
  | "HIRED"
  | "REJECTED";

export interface ApplicantStageHistory {
  id: string;
  from_stage: ApplicantStage | null;
  to_stage: ApplicantStage;
  note: string | null;
  actor_id: string;
  actor_name: string;
  created_at: string;
}

export interface Applicant {
  id: string;
  job_posting_id: string;
  job_posting_title: string;
  request_department_id: string;
  request_department_name: string;
  name: string;
  email: string;
  phone: string | null;
  career_summary: string;
  stage: ApplicantStage;
  created_by_id: string;
  created_by_name: string;
  created_at: string;
  updated_at: string;
  stage_histories: ApplicantStageHistory[];
}

export interface ApplicantInput {
  name: string;
  email: string;
  phone?: string | null;
  career_summary?: string;
}

export interface ApplicantUpdateInput {
  name?: string;
  email?: string;
  phone?: string | null;
  career_summary?: string;
}
