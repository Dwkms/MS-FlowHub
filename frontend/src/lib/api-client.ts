import { getSupabaseBrowserClient } from "@/lib/supabase-browser";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  formData?: FormData;
  headers?: HeadersInit;
};

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetchApi(path, options);
  if (response.status === 204) return undefined as T;

  return (await response.json()) as T;
}

export async function apiGetBlob(path: string): Promise<Blob> {
  const response = await fetchApi(path);
  return response.blob();
}

async function fetchApi(path: string, options: RequestOptions = {}): Promise<Response> {
  let response: Response;
  try {
    const requestHeaders = new Headers(options.headers);
    requestHeaders.set("Accept", "application/json");
    if (options.body !== undefined && !options.formData) {
      requestHeaders.set("Content-Type", "application/json");
    }
    if (!requestHeaders.has("Authorization")) {
      const { data } = await getSupabaseBrowserClient().auth.getSession();
      const accessToken = data.session?.access_token;
      if (accessToken) {
        requestHeaders.set("Authorization", `Bearer ${accessToken}`);
      }
    }

    response = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store",
      method: options.method ?? "GET",
      headers: requestHeaders,
      body: options.formData ?? (options.body === undefined ? undefined : JSON.stringify(options.body)),
    });
  } catch {
    throw new ApiError("Backend API에 연결할 수 없습니다.");
  }

  if (!response.ok) {
    let message = `API 요청이 실패했습니다. (${response.status})`;
    try {
      const errorBody = (await response.json()) as { detail?: string };
      if (typeof errorBody.detail === "string") message = errorBody.detail;
    } catch {
      // JSON 오류 응답이 아니면 기본 메시지를 사용한다.
    }
    throw new ApiError(message, response.status);
  }

  return response;
}

export function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>(path);
}

export function apiDelete(path: string): Promise<void> {
  return apiRequest<void>(path, { method: "DELETE" });
}
