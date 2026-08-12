import type { DocumentType } from "@/types/approval";

/** AI가 만든 전자결재 초안. 저장은 결국 content 한 덩어리이지만, 사용자가 필드 단위로
 *  고칠 수 있도록 구조화된 상태로 받는다. */
export interface ApprovalDraftOutput {
  title: string;
  purpose: string;
  details: string;
  expected_effect: string;
}

/** 초안 생성 입력. 결재 문서에 저장되지 않는 일회성 값이라 DB 칼럼을 늘리지 않는다.
 *  금액·수량이 문자열인 것은 "약 500만원" 같은 표현을 그대로 넘기기 위해서다. */
export interface ApprovalDraftRequest {
  document_type: DocumentType;
  purpose: string;
  main_content: string;
  amount?: string;
  quantity?: string;
  desired_date?: string;
  extra_note?: string;
}

/** AI가 다듬은 채용공고 문장. 주요 업무·필수 역량은 담당자가 이미 쓴 텍스트를 옮긴 것이지
 *  없던 항목을 만든 것이 아니다. */
export interface JobPostingDraftOutput {
  headline: string;
  introduction: string;
  responsibilities: string[];
  requirements: string[];
  preferred_qualifications: string[];
  team_or_recruitment_description: string;
  closing_message: string;
}

/** 직무·인원·업무·역량은 채용 요청에서 자동으로 가져오므로 보내지 않는다.
 *  여기 있는 값은 DB에 없어서 사용자가 채워야 하는 것들뿐이다. */
export interface JobPostingDraftRequest {
  job_posting_id: string;
  work_location?: string;
  application_deadline?: string;
  apply_method?: string;
  team_intro?: string;
  salary?: string;
}

export interface JobPostingDraftResponse {
  generation_id: string;
  success: boolean;
  provider: string;
  is_sample: boolean;
  output: JobPostingDraftOutput | null;
  error_message: string | null;
}

export interface ApprovalDraftResponse {
  generation_id: string;
  success: boolean;
  provider: string;
  /** Mock Provider 결과. 샘플을 실제 LLM 결과로 오인하지 않도록 화면에 표시한다. */
  is_sample: boolean;
  output: ApprovalDraftOutput | null;
  error_message: string | null;
}
