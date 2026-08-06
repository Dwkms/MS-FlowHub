"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ArrowIcon } from "@/components/icons";
import { useCurrentUser } from "@/features/current-user/current-user-provider";
import { getDashboard } from "@/features/dashboard/api";
import { DashboardMetrics } from "@/features/dashboard/dashboard-metrics";
import type { DashboardData } from "@/types/dashboard";

export function DashboardPortal() {
  const { apiConnected, currentEmployee, isLoadingCurrentUser } = useCurrentUser();
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    if (isLoadingCurrentUser) {
      return () => {
        active = false;
      };
    }
    if (!apiConnected) {
      return () => {
        active = false;
      };
    }
    void getDashboard()
      .then((result) => {
        if (!active) return;
        setDashboard(result);
        setError(null);
      })
      .catch(() => {
        if (!active) return;
        setError("대시보드 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [apiConnected, isLoadingCurrentUser]);

  const isDashboardLoading = isLoadingCurrentUser || (apiConnected && loading);
  const todayLabel = new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date()).toUpperCase();

  if (isDashboardLoading) return <section className="content"><div className="state-box">대시보드를 불러오는 중입니다.</div></section>;
  if (!dashboard) return <section className="content"><div className="state-box error">{error ?? "대시보드를 불러올 수 없습니다."}</div></section>;

  return (
    <section className="content">
      {error && <div className="inline-alert warning">{error}</div>}
      <div className="eyebrow">{todayLabel}</div>
      <div className="welcome">
        <div>
          <h1>안녕하세요, {currentEmployee.name}님.</h1>
          <p>
            {currentEmployee.department_name} · {currentEmployee.role_label} 권한으로
            접속했습니다. 오늘 처리할 업무를 확인해 보세요.
          </p>
        </div>
        <div className="access-card">
          <span>접근 가능 모듈</span>
          <div>
            {dashboard.accessible_modules.map((module) => (
              <b key={module}>{module}</b>
            ))}
          </div>
        </div>
      </div>

      <DashboardMetrics metrics={dashboard.metrics} />

      <div className="grid">
        <section className="panel tasks-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">RECENT WORK</span>
              <h2>최근 업무</h2>
            </div>
            <Link className="text-link" href="/approvals">
              전체 보기 <ArrowIcon />
            </Link>
          </div>
          <div className="task-list">
            {dashboard.recent_tasks.length === 0 && (
              <div className="state-box">최근 처리한 전자결재 또는 채용 요청이 없습니다.</div>
            )}
            {dashboard.recent_tasks.map((task) => {
              const content = (
                <>
                  <span className="task-category">{task.category}</span>
                  <div>
                    <strong>{task.title}</strong>
                    <p>담당자 {task.owner}</p>
                  </div>
                  <span className="status-pill">{task.status}</span>
                  <ArrowIcon className="row-arrow" />
                </>
              );
              return task.href ? (
                <Link className="task-row" href={task.href} key={task.id}>
                  {content}
                </Link>
              ) : (
                <article className="task-row" key={task.id}>
                  {content}
                </article>
              );
            })}
          </div>
        </section>
      </div>
    </section>
  );
}
