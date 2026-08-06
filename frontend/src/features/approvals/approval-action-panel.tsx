type ApprovalAction = "submit" | "approve" | "reject";

interface ApprovalActionPanelProps {
  canSubmit: boolean;
  canDecide: boolean;
  comment: string;
  rejectReason: string;
  processing: boolean;
  onCommentChange: (value: string) => void;
  onRejectReasonChange: (value: string) => void;
  onProcess: (action: ApprovalAction) => void;
}

export function ApprovalActionPanel({
  canSubmit,
  canDecide,
  comment,
  rejectReason,
  processing,
  onCommentChange,
  onRejectReasonChange,
  onProcess,
}: ApprovalActionPanelProps) {
  if (!canSubmit && !canDecide) return null;

  return <section className="panel action-panel"><h2>{canSubmit ? "결재 요청" : "결재 처리"}</h2>{canSubmit && <><label className="form-field full"><span>상신 의견</span><textarea rows={3} value={comment} onChange={(event) => onCommentChange(event.target.value)} placeholder="결재자에게 전달할 의견을 입력하세요 (선택)" /></label><div className="form-actions"><button className="primary-button" disabled={processing} onClick={() => onProcess("submit")}>{processing ? "처리 중..." : "결재 요청"}</button></div></>}{canDecide && <><label className="form-field full"><span>승인 의견</span><textarea rows={2} value={comment} onChange={(event) => onCommentChange(event.target.value)} placeholder="승인 의견을 입력하세요 (선택)" /></label><label className="form-field full"><span>반려 사유 *</span><textarea rows={3} value={rejectReason} onChange={(event) => onRejectReasonChange(event.target.value)} placeholder="반려 시 반드시 사유를 입력하세요" /></label><div className="form-actions"><button className="danger-button" disabled={processing} onClick={() => onProcess("reject")}>반려</button><button className="primary-button" disabled={processing} onClick={() => onProcess("approve")}>승인</button></div></>}</section>;
}
