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
import { ApprovalActionPanel } from "@/features/approvals/approval-action-panel";
import { ApprovalHistoryPanel } from "@/features/approvals/approval-history-panel";
import { useCurrentUser } from "@/features/current-user/current-user-provider";
import { getRecruitmentRequest } from "@/features/recruitment/api";
import { RecruitmentPosterAttachment } from "@/features/recruitment/recruitment-poster-attachment";
import type { ApprovalDocument } from "@/types/approval";
import type { RecruitmentRequest } from "@/types/recruitment";

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
          void getRecruitmentRequest(result.related_id)
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
        result = await submitApproval(document.id, comment);
      } else if (action === "approve") {
        result = await approveApproval(document.id, comment);
      } else {
        result = await rejectApproval(
          document.id,
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
    const linkedRecruitmentMessage = document.related_type === "RECRUITMENT_REQUEST"
      ? " 연결된 채용 요청과 채용공고도 함께 삭제됩니다."
      : "";
    if (!window.confirm(`관리자 권한으로 이 문서를 삭제할까요?${linkedRecruitmentMessage} 삭제한 문서는 복구할 수 없습니다.`)) {
      return;
    }

    setProcessing(true);
    setError(null);
    try {
      await deleteApproval(document.id);
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
  const isAdmin = currentEmployee.role === "SUPER_ADMIN";
  const canSelfDecideRecruitment =
    isAdmin &&
    document.related_type === "RECRUITMENT_REQUEST" &&
    document.author_id === currentEmployee.id;
  const canDecide =
    document.status === "PENDING" &&
    (canSelfDecideRecruitment || (
      document.author_id !== currentEmployee.id &&
      (document.approver_id === currentEmployee.id || isAdmin)
    ));
  const canDelete = isAdmin;
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

          <ApprovalActionPanel canSubmit={canSubmit} canDecide={canDecide} comment={comment} rejectReason={rejectReason} processing={processing} onCommentChange={setComment} onRejectReasonChange={setRejectReason} onProcess={(action) => void processAction(action)} />
        </div>

        <ApprovalHistoryPanel histories={document.histories} />
      </div>
    </section>
  );
}
