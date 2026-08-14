"use client";

/**
 * 로그인하지 않은 사용자를 로그인 화면으로 돌려보내는 문지기.
 *
 * 페이지마다 인증 검사를 넣으면 새 페이지를 만들 때 빠뜨리기 쉽습니다. 레이아웃에서
 * 한 번 감싸 모든 화면에 적용합니다. `/login`과 `/change-password`만 예외입니다.
 *
 * 로그인 화면으로 보내는 경로가 **두 개**라 주의가 필요합니다.
 *   1. Supabase의 `onAuthStateChange` — 토큰이 만료되거나 로그아웃했을 때
 *   2. `useSessionTimeout` — 창을 닫아둔 시간이 기준을 넘었을 때
 *
 * 둘 중 어느 쪽이 먼저 동작할지 알 수 없어서, 자리 비움으로 끊긴 경우를 `timedOutRef`에
 * 미리 적어 둡니다. 그래야 두 경로 모두 `/login?reason=timeout`으로 가고 사용자가
 * "왜 로그아웃됐지"를 알 수 있습니다. `useState`가 아니라 `useRef`인 이유는 이 값이
 * 화면을 다시 그릴 필요가 없는 정보이기 때문입니다.
 */

import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useCallback, useEffect, useRef, useState } from "react";

import { getAuthenticatedEmployee } from "@/features/auth/api";
import { useSessionTimeout } from "@/features/auth/session-timeout";
import { useCurrentUser } from "@/features/current-user/current-user-provider";
import { getSupabaseBrowserClient } from "@/lib/supabase-browser";

export function AuthSessionGuard({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { syncAuthenticatedEmployee } = useCurrentUser();
  const isPublicPage = pathname === "/login" || pathname === "/change-password";
  const [authenticatedPath, setAuthenticatedPath] = useState<string | null>(null);

  // 자리 비움으로 끊긴 경우에만 로그인 화면에 사유를 남긴다.
  // 아래 onAuthStateChange와 훅이 각각 화면을 옮기므로, 사유를 미리 적어 두 경로가 같은 주소로 가게 한다.
  const timedOutRef = useRef(false);

  const redirectToLogin = useCallback(() => {
    setAuthenticatedPath(null);
    router.replace(timedOutRef.current ? "/login?reason=timeout" : "/login");
  }, [router]);

  const markTimedOut = useCallback(() => {
    timedOutRef.current = true;
  }, []);

  useSessionTimeout({
    enabled: !isPublicPage,
    onSignOutStart: markTimedOut,
    onSignOutEnd: redirectToLogin,
  });

  useEffect(() => {
    if (isPublicPage) {
      return;
    }

    let active = true;
    const client = getSupabaseBrowserClient();
    const applySession = async () => {
      const { data } = await client.auth.getSession();
      if (!active) return;
      if (!data.session) {
        router.replace("/login");
        return;
      }
      try {
        const { employeeId, role } = await getAuthenticatedEmployee();
        if (!active) return;
        const employeeLoaded = await syncAuthenticatedEmployee(employeeId, role);
        if (!employeeLoaded) {
          await client.auth.signOut();
          if (active) router.replace("/login");
          return;
        }
        if (!active) return;
        // 새 세션이 붙었으므로 지난 로그아웃 사유는 지운다.
        timedOutRef.current = false;
        setAuthenticatedPath(pathname);
      } catch {
        await client.auth.signOut();
        if (active) router.replace("/login");
      }
    };
    void applySession();
    const { data: listener } = client.auth.onAuthStateChange((_event, session) => {
      if (!session) redirectToLogin();
    });
    return () => {
      active = false;
      listener.subscription.unsubscribe();
    };
  }, [isPublicPage, pathname, redirectToLogin, router, syncAuthenticatedEmployee]);

  if (isPublicPage || authenticatedPath === pathname) return <>{children}</>;
  return <main className="auth-loading">세션을 확인하는 중입니다.</main>;
}
