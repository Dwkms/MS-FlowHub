/**
 * 브라우저용 Supabase 클라이언트.
 *
 * **이 프로젝트에서 프론트엔드가 Supabase를 직접 부르는 유일한 곳입니다.**
 * 직원·결재·채용 같은 업무 데이터는 전부 FastAPI를 거칩니다. 브라우저가 DB에 직접
 * 붙으면 권한 판정이 클라이언트로 내려가고, 그건 개발자 도구로 우회할 수 있습니다.
 * 여기서 하는 일은 로그인과 토큰 관리뿐입니다.
 *
 * 클라이언트를 모듈 변수에 담아 재사용하는 이유(`browserClient ??=`): `createClient`를
 * 호출할 때마다 새 인스턴스가 생기고 각자 세션을 감시합니다. 토큰 갱신이 중복으로
 * 일어나고 로그아웃이 한쪽에만 반영되는 문제가 생깁니다.
 */

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
