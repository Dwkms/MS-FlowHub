export type ManualStatus = "DRAFT" | "PUBLISHED";
export type ManualRole = "SUPER_ADMIN" | "HR_ADMIN" | "TEAM_ADMIN" | "EMPLOYEE";
export type ManualAssetType = "IMAGE" | "PDF";

export interface ManualCategory {
  id: string;
  name: string;
  description: string | null;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface ManualAsset {
  id: string;
  asset_type: ManualAssetType;
  file_url: string;
  thumbnail_url: string | null;
  alt_text: string | null;
  display_order: number;
}

export interface ManualListItem {
  id: string;
  category: ManualCategory;
  title: string;
  slug: string;
  summary: string;
  target_roles: ManualRole[];
  is_pinned: boolean;
  status: ManualStatus;
  updated_at: string;
  thumbnail_url: string | null;
}

export interface ManualDetail extends ManualListItem {
  content: string;
  created_at: string;
  assets: ManualAsset[];
}

export interface ManualAssetInput {
  asset_type: ManualAssetType;
  file_url: string;
  thumbnail_url?: string | null;
  alt_text?: string | null;
  display_order: number;
}

export interface ManualInput {
  category_id: string;
  title: string;
  summary: string;
  content: string;
  target_roles: ManualRole[];
  is_pinned: boolean;
  status: ManualStatus;
  assets: ManualAssetInput[];
}

export interface ManualFaq {
  id: string;
  category: string;
  question: string;
  answer: string;
  related_manual_id: string | null;
  display_order: number;
}
