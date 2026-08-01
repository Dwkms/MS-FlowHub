"use client";

import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";

import { getAuthenticatedEmployee } from "@/features/auth/api";
import { useCurrentUser } from "@/features/current-user/current-user-provider";
import { getSupabaseBrowserClient } from "@/lib/supabase-browser";

export function AuthSessionGuard({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { setSelectedId } = useCurrentUser();
  const isPublicPage = pathname === "/login" || pathname === "/change-password";
  const [ready, setReady] = useState(isPublicPage);

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
        const employeeId = await getAuthenticatedEmployee(data.session.access_token);
        if (!active) return;
        setSelectedId(employeeId);
        setReady(true);
      } catch {
        await client.auth.signOut();
        if (active) router.replace("/login");
      }
    };
    void applySession();
    const { data: listener } = client.auth.onAuthStateChange((_event, session) => {
      if (!session) router.replace("/login");
    });
    return () => {
      active = false;
      listener.subscription.unsubscribe();
    };
  }, [isPublicPage, pathname, router, setSelectedId]);

  if (isPublicPage || ready) return <>{children}</>;
  return <main className="auth-loading">세션을 확인하는 중입니다.</main>;
}
