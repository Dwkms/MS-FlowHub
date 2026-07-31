"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  approveApproval,
  deleteApproval,
  getApproval,
  rejectApproval,
  submitApproval,
} from "@/features/approvals/api";
import {
  documentTypeLabels,
  formatDateTime,
  statusLabels,
} from "@/features/approvals/presentation";
import { useCurrentUser } from "@/features/current-user/current-user-provider";
import { getRecruitmentRequest } from "@/features/recruitment/api";
import { RecruitmentPosterAttachment } from "@/features/recruitment/recruitment-poster-attachment";
import type { ApprovalDocument } from "@/types/approval";
import type { RecruitmentRequest } from "@/types/recruitment";

const actionLabels: Record<string, string> = {
  CREATED: "문서 작성",
  UPDATED: "문서 수정",
  SUBMITTED: "결재 요청",
  APPROVED: "승인",
  REJECTED: "반려",
};

export function ApprovalDetail() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { currentEmployee } = useCurrentUser();
  const [document, setDocument] = useState<ApprovalDocument | null>(null);
  const [relatedRecruitmentRequest, setRelatedRecruitmentRequest] =
    useState<RecruitmentRequest | null>(null);
  const [comment, setComment] = useState("");
  const [rejectReason, setRejectReason] = useState("");
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void getApproval(params.id)
      .then((result) => {
        if (active) setDocument(result);
        if (result.related_type === "RECRUITMENT_REQUEST" && result.related_id) {
          void getRecruitmentRequest(result.related_id, currentEmployee.id)
            .then((request) => {
              if (active) setRelatedRecruitmentRequest(request);
            })
            .catch(() => {
              // The approval document remains available even if its related request was removed.
            });
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "문서를 불러오지 못했습니다.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [currentEmployee.id, params.id]);

  async function processAction(action: "submit" | "approve" | "reject") {
    if (!document) return;
    if (action === "reject" && !rejectReason.trim()) {
      setError("반려 사유를 입력해 주세요.");
      return;
    }

    setProcessing(true);
    setError(null);
    setNotice(null);
    try {
      let result: ApprovalDocument;
      if (action === "submit") {
        result = await submitApproval(document.id, currentEmployee.id, comment);
      } else if (action === "approve") {
        result = await approveApproval(document.id, currentEmployee.id, comment);
      } else {
        result = await rejectApproval(
          document.id,
          currentEmployee.id,
          rejectReason.trim(),
        );
      }
      setDocument(result);
      setComment("");
      setRejectReason("");
      setNotice(
        action === "submit"
          ? "결재 요청을 완료했습니다."
          : action === "approve"
            ? "문서를 승인했습니다."
            : "문서를 반려했습니다.",
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "문서를 처리하지 못했습니다.");
    } finally {
      setProcessing(false);
    }
  }

  async function deleteDocument() {
    if (!document) return;
    if (!window.confirm("관리자 권한으로 이 문서를 삭제할까요? 삭제한 문서는 복구할 수 없습니다.")) {
      return;
    }

    setProcessing(true);
    setError(null);
    try {
      await deleteApproval(document.id, currentEmployee.id);
      router.push("/approvals");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "문서를 삭제하지 못했습니다.");
      setProcessing(false);
    }
  }

  if (loading) {
    return (
      <section className="content approval-page">
        <div className="state-box">전자결재 문서를 불러오는 중입니다.</div>
      </section>
    );
  }

  if (!document) {
    return (
      <section className="content approval-page">
        <div className="state-box error">{error ?? "문서를 찾을 수 없습니다."}</div>
      </section>
    );
  }

  const canSubmit =
    document.status === "DRAFT" && document.author_id === currentEmployee.id;
  const canDecide =
    document.status === "PENDING" &&
    (document.approver_id === currentEmployee.id || currentEmployee.role === "ADMIN");
  const canDelete = currentEmployee.role === "ADMIN";
  const isCompleted =
    document.status === "APPROVED" || document.status === "REJECTED";

  return (
    <section className="content approval-page">
      <div className="page-heading detail-heading">
        <div>
          <span className="section-kicker">APPROVAL DETAIL</span>
          <h1>{document.title}</h1>
          <p>
            {documentTypeLabels[document.document_type]} · {document.department_name}
          </p>
        </div>
        <div className="heading-actions">
          <span className={`approval-status large ${document.status.toLowerCase()}`}>
            {statusLabels[document.status]}
          </span>
          <Link className="secondary-button" href="/approvals">
            목록으로
          </Link>
          {canDelete && (
            <button
              className="danger-button"
              disabled={processing}
              onClick={() => void deleteDocument()}
            >
              삭제
            </button>
          )}
        </div>
      </div>

      {notice && <div className="inline-alert success">{notice}</div>}
      {error && <div className="inline-alert error">{error}</div>}

      <div className="approval-detail-grid">
        <div>
          <section className="panel detail-panel">
            <div className="approval-progress" aria-label="결재 진행 상태">
              <div className="done">
                <i>1</i>
                <span>문서 작성</span>
              </div>
              <b />
              <div className={document.status !== "DRAFT" ? "done" : ""}>
                <i>2</i>
                <span>결재 대기</span>
              </div>
              <b />
              <div className={isCompleted ? "done" : ""}>
                <i>3</i>
                <span>{isCompleted ? statusLabels[document.status] : "처리 완료"}</span>
              </div>
            </div>

            <dl className="document-meta">
              <div>
                <dt>기안자</dt>
                <dd>{document.author_name}</dd>
              </div>
              <div>
                <dt>기안 부서</dt>
                <dd>{document.department_name}</dd>
              </div>
              <div>
                <dt>결재자</dt>
                <dd>{document.approver_name}</dd>
              </div>
              <div>
                <dt>작성일</dt>
                <dd>{formatDateTime(document.created_at)}</dd>
              </div>
            </dl>

            <div className="document-content">
              <span>문서 내용</span>
              <p>{document.content}</p>
            </div>

            {relatedRecruitmentRequest && (
              <RecruitmentPosterAttachment
                requestId={relatedRecruitmentRequest.id}
                employeeId={currentEmployee.id}
                originalName={relatedRecruitmentRequest.poster_original_name}
                contentType={relatedRecruitmentRequest.poster_content_type}
              />
            )}

            {document.related_type === "RECRUITMENT_REQUEST" && document.related_id && (
              <div className="decision-comment">
                <strong>관련 업무</strong>
                <p>
                  <Link href={`/recruitment-requests/${document.related_id}`}>
                    연결된 채용 요청 보기
                  </Link>
                </p>
              </div>
            )}

            {document.decision_comment && (
              <div className="decision-comment">
                <strong>{document.status === "REJECTED" ? "반려 사유" : "결재 의견"}</strong>
                <p>{document.decision_comment}</p>
              </div>
            )}
          </section>

          {(canSubmit || canDecide) && (
            <section className="panel action-panel">
              <h2>{canSubmit ? "결재 요청" : "결재 처리"}</h2>
              {canSubmit && (
                <>
                  <label className="form-field full">
                    <span>상신 의견</span>
                    <textarea
                      rows={3}
                      value={comment}
                      onChange={(event) => setComment(event.target.value)}
                      placeholder="결재자에게 전달할 의견을 입력하세요 (선택)"
                    />
                  </label>
                  <div className="form-actions">
                    <button
                      className="primary-button"
                      disabled={processing}
                      onClick={() => void processAction("submit")}
                    >
                      {processing ? "처리 중..." : "결재 요청"}
                    </button>
                  </div>
                </>
              )}
              {canDecide && (
                <>
                  <label className="form-field full">
                    <span>승인 의견</span>
                    <textarea
                      rows={2}
                      value={comment}
                      onChange={(event) => setComment(event.target.value)}
                      placeholder="승인 의견을 입력하세요 (선택)"
                    />
                  </label>
                  <label className="form-field full">
                    <span>반려 사유 *</span>
                    <textarea
                      rows={3}
                      value={rejectReason}
                      onChange={(event) => setRejectReason(event.target.value)}
                      placeholder="반려 시 반드시 사유를 입력하세요"
                    />
                  </label>
                  <div className="form-actions">
                    <button
                      className="danger-button"
                      disabled={processing}
                      onClick={() => void processAction("reject")}
                    >
                      반려
                    </button>
                    <button
                      className="primary-button"
                      disabled={processing}
                      onClick={() => void processAction("approve")}
                    >
                      승인
                    </button>
                  </div>
                </>
              )}
            </section>
          )}
        </div>

        <aside className="panel history-panel">
          <span className="section-kicker">HISTORY</span>
          <h2>결재 처리 이력</h2>
          <div className="history-list">
            {document.histories.map((history) => (
              <article key={history.id}>
                <i />
                <div>
                  <strong>{actionLabels[history.action] ?? history.action}</strong>
                  <p>
                    {history.actor_name} · {formatDateTime(history.created_at)}
                  </p>
                  {history.comment && <blockquote>{history.comment}</blockquote>}
                </div>
              </article>
            ))}
          </div>
        </aside>
      </div>
    </section>
  );
}
