"use client";

import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";

import { getAuthenticatedEmployee } from "@/features/auth/api";
import { useCurrentUser } from "@/features/current-user/current-user-provider";
import { getSupabaseBrowserClient } from "@/lib/supabase-browser";

export function AuthSessionGuard({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { syncAuthenticatedEmployee } = useCurrentUser();
  const isPublicPage = pathname === "/login" || pathname === "/change-password";
  const [authenticatedPath, setAuthenticatedPath] = useState<string | null>(null);

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
        setAuthenticatedPath(pathname);
      } catch {
        await client.auth.signOut();
        if (active) router.replace("/login");
      }
    };
    void applySession();
    const { data: listener } = client.auth.onAuthStateChange((_event, session) => {
      if (!session) {
        setAuthenticatedPath(null);
        router.replace("/login");
      }
    });
    return () => {
      active = false;
      listener.subscription.unsubscribe();
    };
  }, [isPublicPage, pathname, router, syncAuthenticatedEmployee]);

  if (isPublicPage || authenticatedPath === pathname) return <>{children}</>;
  return <main className="auth-loading">세션을 확인하는 중입니다.</main>;
}
