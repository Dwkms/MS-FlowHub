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
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  formData?: FormData;
};

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store",
      method: options.method ?? "GET",
      headers: {
        Accept: "application/json",
        ...(options.body === undefined || options.formData ? {} : { "Content-Type": "application/json" }),
      },
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

  if (response.status === 204) return undefined as T;

  return (await response.json()) as T;
}

export function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>(path);
}

export function apiDelete(path: string): Promise<void> {
  return apiRequest<void>(path, { method: "DELETE" });
}
