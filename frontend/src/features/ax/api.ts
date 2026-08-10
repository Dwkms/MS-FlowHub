import { apiRequest } from "@/lib/api-client";
import type { AxChatResponse } from "@/types/ax";

export function askAssistant(question: string): Promise<AxChatResponse> {
  return apiRequest<AxChatResponse>("/api/v1/ax/chat", {
    method: "POST",
    body: { question },
  });
}
