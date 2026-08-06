import Link from "next/link";

import type { DashboardMetric } from "@/types/dashboard";

const metricLinks: Record<string, string> = {
  "내 결재 대기": "/approvals",
  "내가 상신한 결재": "/approvals",
  "진행 중 채용": "/job-postings",
};

export function DashboardMetrics({ metrics }: { metrics: DashboardMetric[] }) {
  return (
    <div className="metrics">
      {metrics.map((metric) => {
        const href = metric.value > 0 ? metricLinks[metric.label] : undefined;
        const content = (
          <>
            <div className="metric-top">
              <span>{metric.label}</span>
              <i />
            </div>
            <strong>{metric.value}</strong>
            <p>{metric.helper}</p>
          </>
        );

        return href ? (
          <Link
            aria-label={`${metric.label} ${metric.value}건 보기`}
            className={`metric metric-link ${metric.tone}`}
            href={href}
            key={metric.label}
          >
            {content}
          </Link>
        ) : (
          <article className={`metric ${metric.tone}`} key={metric.label}>
            {content}
          </article>
        );
      })}
    </div>
  );
}
