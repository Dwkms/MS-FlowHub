"use client";

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
