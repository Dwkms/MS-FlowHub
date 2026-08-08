import Link from "next/link";

import type { DashboardAnalytics as DashboardAnalyticsData, DashboardBreakdownItem, DashboardMetric } from "@/types/dashboard";

const approvalLabels: Record<string, string> = { APPROVED: "승인", DRAFT: "임시 저장", PENDING: "대기", REJECTED: "반려" };
const stageDefinitions = [
  { key: "APPLIED", label: "지원 접수", tone: "blue", symbol: "▤" },
  { key: "SCREENING", label: "서류 검토", tone: "teal", symbol: "⌕" },
  { key: "INTERVIEW", label: "면접", tone: "orange", symbol: "♧" },
  { key: "OFFERED", label: "처우 제안", tone: "violet", symbol: "✦" },
  { key: "HIRED", label: "최종 합격", tone: "purple", symbol: "★" },
  { key: "REJECTED", label: "불합격", tone: "gray", symbol: "−" },
];

function getMetricValue(metrics: DashboardMetric[], label: string) {
  return metrics.find((metric) => metric.label === label)?.value ?? 0;
}

function ApprovalChart({ items }: { items: DashboardBreakdownItem[] }) {
  const total = items.reduce((sum, item) => sum + item.value, 0);
  let offset = 0;
  const colors = ["#246fe5", "#ff9d38", "#f15454", "#aeb5c0"];
  const segments = items.map((item, index) => {
    const percentage = total === 0 ? 0 : (item.value / total) * 100;
    const segment = `${colors[index % colors.length]} ${offset}% ${offset + percentage}%`;
    offset += percentage;
    return segment;
  });
  const background = total ? `conic-gradient(${segments.join(", ")})` : "#edf1f6";

  return <div className="approval-chart"><div className="donut" style={{ background }}><div><span>전체</span><b>{total}건</b></div></div><ul>{items.map((item, index) => <li key={item.label}><i style={{ backgroundColor: colors[index % colors.length] }} /><span>{approvalLabels[item.label] ?? item.label}</span><b>{item.value}건</b></li>)}</ul></div>;
}

export function DashboardAnalytics({ analytics, metrics }: { analytics: DashboardAnalyticsData; metrics: DashboardMetric[] }) {
  const pendingApprovals = getMetricValue(metrics, "내 결재 대기");
  const submittedApprovals = getMetricValue(metrics, "내가 상신한 결재");
  const postings = getMetricValue(metrics, "진행 중 채용");
  const hasApplicants = analytics.applicant_by_stage.length > 0;

  return <section className="dashboard-overview"><div className="overview-kpis"><Link className="overview-kpi blue" href="/approvals"><i>▤</i><span>결재 대기</span><b>{pendingApprovals}<small>건</small></b></Link><Link className="overview-kpi amber" href="/approvals"><i>◷</i><span>상신 결재</span><b>{submittedApprovals}<small>건</small></b></Link><Link className="overview-kpi teal" href="/job-postings"><i>♧</i><span>진행 채용</span><b>{postings}<small>건</small></b></Link><Link className="overview-kpi red" href="/employees"><i>▣</i><span>오늘 근태 미등록</span><b>{analytics.today_attendance_unregistered_count}<small>명</small></b></Link></div><div className="overview-grid"><article className="panel overview-panel approval-overview"><h2>전자결재 상태</h2><ApprovalChart items={analytics.approval_by_status} /><div className="overview-hint">처리 완료 결재 평균 <b>{analytics.average_approval_processing_hours === null ? "-" : `${analytics.average_approval_processing_hours}시간`}</b></div><Link className="overview-link" href="/approvals">전자결재 바로가기 <span>›</span></Link></article><article className="panel overview-panel applicant-overview"><h2>지원자 현황</h2>{hasApplicants ? <div className="applicant-flow">{stageDefinitions.filter((stage) => analytics.applicant_by_stage.some((item) => item.label === stage.key)).map((stage, index, stages) => { const value = analytics.applicant_by_stage.find((item) => item.label === stage.key)?.value ?? 0; return <div className="applicant-flow-step" key={stage.key}><i className={stage.tone}>{stage.symbol}</i><span>{stage.label}</span><b>{value}<small>명</small></b>{index < stages.length - 1 && <em>›</em>}</div>; })}</div> : <p className="analytics-empty">등록된 지원자가 없습니다.</p>}<div className="overview-hint">전체 채용 요청 <b>{analytics.recruitment_request_count}건</b></div><Link className="overview-link" href="/applicants">채용 관리 바로가기 <span>›</span></Link></article><article className="panel overview-panel attendance-overview"><h2>오늘의 근태</h2><div className="attendance-alert"><i>!</i><span>근태 미등록</span><b>{analytics.today_attendance_unregistered_count}<small>명</small></b><p>대상자 확인 후 근태를 등록해 주세요.</p></div><Link className="attendance-link" href="/employees">근태 현황 보기 <span>›</span></Link></article></div></section>;
}
