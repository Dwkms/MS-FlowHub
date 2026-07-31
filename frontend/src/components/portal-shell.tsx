"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { BellIcon, FlowMark } from "@/components/icons";
import { useCurrentUser } from "@/features/current-user/current-user-provider";

const navigation = [
  { label: "업무 홈", href: "/", glyph: "⌂", enabled: true },
  { label: "전자결재", href: "/approvals", glyph: "✓", enabled: true },
  { label: "ATS Lite", href: "/recruitment-requests", glyph: "◎", enabled: true },
  { label: "CRM Lite", href: "#", glyph: "◇", enabled: false },
];

export function PortalShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { employees, currentEmployee, selectedId, setSelectedId, apiConnected } =
    useCurrentUser();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/">
          <FlowMark className="brand-mark" />
          <div>
            <strong>MS FlowHub</strong>
            <span>WORK CONNECTED</span>
          </div>
        </Link>

        <nav aria-label="주요 메뉴">
          <p className="nav-label">WORKSPACE</p>
          {navigation.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
            if (!item.enabled) {
              return (
                <span className="nav-item disabled" key={item.label}>
                  <span className="nav-glyph">{item.glyph}</span>
                  {item.label}
                  <span className="soon">예정</span>
                </span>
              );
            }
            return (
              <Link
                className={active ? "nav-item active" : "nav-item"}
                href={item.href}
                key={item.label}
              >
                <span className="nav-glyph">{item.glyph}</span>
                {item.label}
              </Link>
            );
          })}
          <p className="nav-label second">MANAGEMENT</p>
          <span className="nav-item disabled">
            <span className="nav-glyph">♙</span>
            직원·부서
            <span className="soon">예정</span>
          </span>
        </nav>

        <div className="sidebar-note">
          <span className="note-dot" />
          <div>
            <strong>Prototype v0.5.0</strong>
            <p>전자결재 흐름 구현</p>
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <span className={apiConnected ? "connection ok" : "connection"}>
            <i />
            {apiConnected ? "Backend API 연결됨" : "Backend 연결 필요"}
          </span>
          <div className="top-actions">
            <button className="icon-button" aria-label="알림">
              <BellIcon />
              <b>4</b>
            </button>
            <label className="user-switcher">
              <span className="avatar">{currentEmployee.name.slice(0, 1)}</span>
              <span>
                <small>현재 사용자</small>
                <select
                  value={selectedId}
                  onChange={(event) => setSelectedId(event.target.value)}
                  aria-label="현재 사용자 선택"
                >
                  {employees.map((employee) => (
                    <option value={employee.id} key={employee.id}>
                      {employee.name} · {employee.role_label}
                    </option>
                  ))}
                </select>
              </span>
            </label>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
