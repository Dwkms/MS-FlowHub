"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useState } from "react";

import { BellIcon, FlowMark } from "@/components/icons";
import { useCurrentUser } from "@/features/current-user/current-user-provider";
import { getSupabaseBrowserClient } from "@/lib/supabase-browser";

const navigation = [
  { label: "업무 홈", href: "/", glyph: "⌂" },
  { label: "전자결재", href: "/approvals", glyph: "✓" },
  { label: "ATS Lite", href: "/recruitment-requests", glyph: "⌕" },
  { label: "직원 · 부서", href: "/employees", glyph: "♟" },
  { label: "직원 매뉴얼", href: "/manuals", glyph: "▤" },
  { label: "FAQ", href: "/faq", glyph: "?" },
];

export function PortalShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { apiConnected, currentEmployee } = useCurrentUser();
  const [settingsOpen, setSettingsOpen] = useState(false);
  if (pathname === "/login" || pathname === "/change-password") return <>{children}</>;

  async function logout() {
    await getSupabaseBrowserClient().auth.signOut();
    router.replace("/login");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/"><FlowMark className="brand-mark" /><div><strong>MS FlowHub</strong><span>WORK CONNECTED</span></div></Link>
        <nav aria-label="주요 메뉴"><p className="nav-label">WORKSPACE</p>{navigation.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return <Link className={active ? "nav-item active" : "nav-item"} href={item.href} key={item.href}><span className="nav-glyph">{item.glyph}</span>{item.label}</Link>;
        })}</nav>
        <div className="sidebar-settings">
          {settingsOpen && <div className="settings-menu"><Link href="/change-password" onClick={() => setSettingsOpen(false)}>비밀번호 변경</Link><button onClick={() => void logout()}>로그아웃</button></div>}
          <button className="settings-toggle" onClick={() => setSettingsOpen((open) => !open)} aria-expanded={settingsOpen} aria-label="설정">⚙</button>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <span className={apiConnected ? "connection ok" : "connection"}><i />{apiConnected ? "Backend API 연결됨" : "Backend 연결 필요"}</span>
          <div className="top-actions">
            <button
              aria-label="알림 기능은 사내 메일 시스템 도입 후 제공 예정입니다"
              className="icon-button notification-disabled"
              disabled
              title="사내 메일 시스템 도입 후 제공 예정"
              type="button"
            >
              <BellIcon />
            </button>
            <div className="authenticated-user"><span className="avatar">{currentEmployee.name.slice(0, 1)}</span><span><small>현재 사용자</small><b>{currentEmployee.name}</b></span></div>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
