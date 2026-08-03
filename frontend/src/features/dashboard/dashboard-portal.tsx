"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ArrowIcon } from "@/components/icons";
import { useCurrentUser } from "@/features/current-user/current-user-provider";
import { getDashboard } from "@/features/dashboard/api";
import { createFallbackDashboard } from "@/features/dashboard/mock-data";
import type { DashboardData } from "@/types/dashboard";

export function DashboardPortal() {
  const { apiConnected, currentEmployee, isLoadingCurrentUser } = useCurrentUser();
  const [dashboard, setDashboard] = useState<DashboardData>(
    createFallbackDashboard(currentEmployee),
  );
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
        setDashboard(createFallbackDashboard(currentEmployee));
        setError("대시보드 API에 연결하지 못해 안내용 데이터를 표시합니다.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [apiConnected, currentEmployee, isLoadingCurrentUser]);

  const isDashboardLoading = isLoadingCurrentUser || (apiConnected && loading);

  return (
    <section className="content">
      {error && <div className="inline-alert warning">{error}</div>}
      <div className="eyebrow">THURSDAY · JUL 30, 2026</div>
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

      <div className={isDashboardLoading ? "metrics loading" : "metrics"}>
        {dashboard.metrics.map((metric) => (
          <article className={`metric ${metric.tone}`} key={metric.label}>
            <div className="metric-top">
              <span>{metric.label}</span>
              <i />
            </div>
            <strong>{metric.value}</strong>
            <p>{metric.helper}</p>
          </article>
        ))}
      </div>

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
