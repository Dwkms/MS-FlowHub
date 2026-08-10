export type AxResultType =
  | "CONFIRMED"
  | "CANDIDATES"
  | "NO_MATCH"
  | "POLICY"
  | "PERSONAL_DATA";

export interface AxSource {
  doc_type: "FAQ" | "MANUAL";
  doc_id: string;
  title: string;
  category: string;
  manual_slug: string | null;
}

export interface AxCandidate {
  doc_id: string;
  title: string;
  category: string;
}

export interface AxChatResponse {
  result_type: AxResultType;
  answer: string;
  source: AxSource | null;
  candidates: AxCandidate[];
  route: string | null;
}
