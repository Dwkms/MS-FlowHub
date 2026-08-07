import { apiDelete, apiGet, apiRequest } from "@/lib/api-client";
import type {
  ManualCategory,
  ManualDetail,
  ManualFaq,
  ManualInput,
  ManualListItem,
} from "@/types/manual";

export function listManualCategories(): Promise<ManualCategory[]> {
  return apiGet<ManualCategory[]>("/api/v1/manuals/categories");
}

export function listManuals(query: { search?: string; categoryId?: string }): Promise<ManualListItem[]> {
  const params = new URLSearchParams();
  if (query.search) params.set("search", query.search);
  if (query.categoryId) params.set("category_id", query.categoryId);
  const suffix = params.size ? `?${params.toString()}` : "";
  return apiGet<ManualListItem[]>(`/api/v1/manuals${suffix}`);
}

export function getManual(slug: string): Promise<ManualDetail> {
  return apiGet<ManualDetail>(`/api/v1/manuals/${slug}`);
}

export function createManual(input: ManualInput): Promise<ManualDetail> {
  return apiRequest<ManualDetail>("/api/v1/manuals", { method: "POST", body: input });
}

export function updateManual(slug: string, input: Partial<ManualInput>): Promise<ManualDetail> {
  return apiRequest<ManualDetail>(`/api/v1/manuals/${slug}`, { method: "PATCH", body: input });
}

export function deleteManual(slug: string): Promise<void> {
  return apiDelete(`/api/v1/manuals/${slug}`);
}

export function listFaqs(): Promise<ManualFaq[]> {
  return apiGet<ManualFaq[]>("/api/v1/faqs");
}
