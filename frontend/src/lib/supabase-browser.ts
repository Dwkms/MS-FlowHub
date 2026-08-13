import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let browserClient: SupabaseClient | null = null;

export function getSupabaseBrowserClient(): SupabaseClient {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

  if (!url || !publishableKey) {
    throw new Error(
      "Supabase Auth 환경변수가 설정되지 않았습니다. frontend/.env.local을 확인하세요.",
    );
  }

  // 세션 저장과 토큰 갱신은 그대로 둔다. 이걸 끄면 새로고침만 해도 로그아웃돼 업무가 끊긴다.
  // "다음날도 로그인 상태" 문제는 features/auth/session-timeout.ts의 자리 비움 측정으로 막는다.
  browserClient ??= createClient(url, publishableKey, {
    auth: { persistSession: true, autoRefreshToken: true },
  });
  return browserClient;
}
