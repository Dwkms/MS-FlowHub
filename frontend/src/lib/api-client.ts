/**
 * 백엔드 API를 부르는 유일한 통로.
 *
 * 화면 컴포넌트가 `fetch`를 직접 부르지 않고 여기를 거치는 이유가 셋 있습니다.
 *
 * 1. **인증 토큰을 자동으로 붙입니다.** 컴포넌트마다 세션을 꺼내 헤더를 만들면
 *    한 군데만 빠뜨려도 그 화면만 401이 납니다.
 * 2. **오류 메시지를 한 곳에서 해석합니다.** FastAPI는 실패를 `{"detail": "..."}`로
 *    돌려주는데, 이 파일이 그 문구를 꺼내 `ApiError`에 담습니다. 화면은 사람이 읽을
 *    문장을 그대로 보여주기만 하면 됩니다.
 * 3. **`cache: "no-store"`로 고정합니다.** Next.js는 기본적으로 fetch 결과를
 *    캐시하는데, 근태·결재처럼 방금 바꾼 값을 다시 읽어야 하는 화면에서는
 *    옛 데이터가 보이게 됩니다.
 *
 * 실제 호출은 기능별 `features/<도메인>/api.ts`에 모으고, 컴포넌트는 그 함수를 씁니다.
 * 같은 요청을 여러 컴포넌트가 각자 구현하지 않게 하기 위해서입니다.
 *
 * 요청 경로는 `/api/v1/...`로 시작합니다. 운영에서는 Next.js가 이 경로를 백엔드로
 * 넘겨주므로(`next.config.ts`의 rewrite) 프론트엔드는 백엔드 주소를 몰라도 됩니다.
 */

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
