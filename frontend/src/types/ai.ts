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

export interface JobPosterGenerateRequest {
  job_posting_id: string;
  design_direction?: string;
}

export interface JobPosterGenerateResponse {
  generation_id: string;
  success: boolean;
  provider: string;
  model_name: string | null;
  image_base64: string | null;
  content_type: string | null;
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
