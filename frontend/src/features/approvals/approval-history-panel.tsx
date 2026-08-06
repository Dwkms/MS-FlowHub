import { formatDateTime } from "@/features/approvals/presentation";
import type { ApprovalHistory } from "@/types/approval";

const actionLabels: Record<string, string> = {
  CREATED: "문서 작성",
  UPDATED: "문서 수정",
  SUBMITTED: "결재 요청",
  APPROVED: "승인",
  REJECTED: "반려",
};

export function ApprovalHistoryPanel({ histories }: { histories: ApprovalHistory[] }) {
  return <aside className="panel history-panel"><span className="section-kicker">HISTORY</span><h2>결재 처리 이력</h2><div className="history-list">{histories.map((history) => <article key={history.id}><i /><div><strong>{actionLabels[history.action] ?? history.action}</strong><p>{history.actor_name} · {formatDateTime(history.created_at)}</p>{history.comment && <blockquote>{history.comment}</blockquote>}</div></article>)}</div></aside>;
}
