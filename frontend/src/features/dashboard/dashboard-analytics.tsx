import Link from "next/link";

import type { DashboardAnalytics as DashboardAnalyticsData, DashboardBreakdownItem, DashboardMetric } from "@/types/dashboard";

const approvalLabels: Record<string, string> = { APPROVED: "승인", DRAFT: "임시 저장", PENDING: "대기", REJECTED: "반려" };
type StageIconName = "document" | "interview" | "group" | "handshake";

const stageDefinitions: Array<{ icon: StageIconName; keys: string[]; label: string; tone: string }> = [
  { icon: "document", keys: ["APPLIED", "SCREENING"], label: "서류전형", tone: "blue" },
  { icon: "interview", keys: ["INTERVIEW"], label: "1차면접", tone: "teal" },
  { icon: "group", keys: ["OFFERED"], label: "2차면접", tone: "orange" },
  { icon: "handshake", keys: ["HIRED"], label: "최종입사", tone: "purple" },
];

function StageIcon({ icon }: { icon: StageIconName }) {
  if (icon === "document") {
    return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M7 3.5h7l3 3V20H7zM14 3.5V7h3M9.5 11h5M9.5 14h5M9.5 17h3" /></svg>;
  }
  if (icon === "interview") {
    return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M8.5 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM3.5 19c.4-3.2 2-5 5-5 1.4 0 2.5.4 3.3 1.1M14 6.5h6.5v6H17l-2.5 2v-2H14z" /></svg>;
  }
  if (icon === "group") {
    return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M8 11a2.7 2.7 0 1 0 0-5.4A2.7 2.7 0 0 0 8 11Zm8 0a2.7 2.7 0 1 0 0-5.4A2.7 2.7 0 0 0 16 11ZM3.5 19c.3-3.1 1.7-5 4.5-5s4.2 1.9 4.5 5M11.5 19c.3-3.1 1.7-5 4.5-5s4.2 1.9 4.5 5" /></svg>;
  }
  return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m3.5 10 4-3 3 2 3-2 7 5-3.5 4.5-2-1.5-3 3-2-2-2 1-5-5zM7.5 7l3 5 3-1.5M7.5 14.5l2.5 2M10 12l4 3.5" /></svg>;
}

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

  return <section className="dashboard-overview"><div className="overview-kpis"><Link className="overview-kpi blue" href="/approvals"><i>▤</i><span>결재 대기</span><b>{pendingApprovals}<small>건</small></b></Link><Link className="overview-kpi amber" href="/approvals"><i>◷</i><span>상신 결재</span><b>{submittedApprovals}<small>건</small></b></Link><Link className="overview-kpi teal" href="/job-postings"><i>♧</i><span>진행 채용</span><b>{postings}<small>건</small></b></Link><Link className="overview-kpi red" href="/employees"><i>▣</i><span>오늘 근태 미등록</span><b>{analytics.today_attendance_unregistered_count}<small>명</small></b></Link></div><div className="overview-grid"><article className="panel overview-panel approval-overview"><h2>전자결재 상태</h2><ApprovalChart items={analytics.approval_by_status} /><div className="overview-hint">처리 완료 결재 평균 <b>{analytics.average_approval_processing_hours === null ? "-" : `${analytics.average_approval_processing_hours}시간`}</b></div><Link className="overview-link" href="/approvals">전자결재 바로가기 <span>›</span></Link></article><article className="panel overview-panel applicant-overview"><h2>전체 채용공고 현황</h2>{hasApplicants ? <div className="applicant-flow">{stageDefinitions.map((stage, index) => { const value = analytics.applicant_by_stage.filter((item) => stage.keys.includes(item.label)).reduce((total, item) => total + item.value, 0); return <div className="applicant-flow-step" key={stage.label}><i className={stage.tone}><StageIcon icon={stage.icon} /></i><span>{stage.label}</span><b>{value}<small>명</small></b>{index < stageDefinitions.length - 1 && <em>›</em>}</div>; })}</div> : <p className="analytics-empty">등록된 지원자가 없습니다.</p>}<div className="overview-hint">전체 채용 요청 <b>{analytics.recruitment_request_count}건</b></div><Link className="overview-link" href="/applicants">채용 관리 바로가기 <span>›</span></Link></article><article className="panel overview-panel attendance-overview"><h2>오늘의 근태</h2><div className="attendance-alert"><i>!</i><span>근태 미등록</span><b>{analytics.today_attendance_unregistered_count}<small>명</small></b><p>대상자 확인 후 근태를 등록해 주세요.</p></div><Link className="attendance-link" href="/employees">근태 현황 보기 <span>›</span></Link></article></div></section>;
}
