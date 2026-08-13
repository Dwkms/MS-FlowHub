"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useCurrentUser } from "@/features/current-user/current-user-provider";
import {
  deleteRecruitmentRequest,
  getRecruitmentRequest,
  submitRecruitmentRequest,
} from "@/features/recruitment/api";
import { RecruitmentPosterAttachment } from "@/features/recruitment/recruitment-poster-attachment";
import { recruitmentStatusLabels } from "@/features/recruitment/presentation";
import type { RecruitmentRequest } from "@/types/recruitment";

export function RecruitmentDetail() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { currentEmployee } = useCurrentUser();
  const [item, setItem] = useState<RecruitmentRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void getRecruitmentRequest(id)
      .then((result) => active && setItem(result))
      .catch((reason: unknown) => active && setError(reason instanceof Error ? reason.message : "채용 요청을 불러오지 못했습니다."))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [id]);

  async function submit() {
    if (!item) return;
    setProcessing(true);
    setError(null);
    try {
      const result = await submitRecruitmentRequest(item.id);
      setItem(result);
      router.push(`/approvals/${result.approval_document_id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "상신하지 못했습니다.");
    } finally {
      setProcessing(false);
    }
  }

  async function deleteRequest() {
    if (!item || !window.confirm("관리자 권한으로 채용 요청을 삭제할까요? 연결된 결재문서와 채용공고도 함께 삭제됩니다.")) return;
    setProcessing(true);
    setError(null);
    try {
      await deleteRecruitmentRequest(item.id);
      router.push("/recruitment-requests");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "채용 요청을 삭제하지 못했습니다.");
      setProcessing(false);
    }
  }

  if (loading) return <section className="content approval-page"><div className="state-box">채용 요청을 불러오는 중입니다.</div></section>;
  if (!item) return <section className="content approval-page"><div className="state-box error">{error ?? "채용 요청을 찾을 수 없습니다."}</div></section>;

  const canSubmit = item.status === "DRAFT" && item.requester_id === currentEmployee.id;

  return <section className="content approval-page"><div className="page-heading detail-heading"><div><span className="section-kicker">RECRUITMENT REQUEST</span><h1>{item.position_title}</h1><p>{item.request_department_name} · 요청자 {item.requester_name}</p></div><div className="heading-actions"><span className={`approval-status large ${item.status.toLowerCase()}`}>{recruitmentStatusLabels[item.status]}</span><Link className="secondary-button" href="/recruitment-requests">목록으로</Link>{currentEmployee.role === "SUPER_ADMIN" && <button className="danger-button" disabled={processing} onClick={() => void deleteRequest()}>삭제</button>}{canSubmit && <button className="primary-button" disabled={processing} onClick={() => void submit()}>{processing ? "상신 중..." : "결재 요청"}</button>}</div></div>{error && <div className="inline-alert error">{error}</div>}<section className="panel detail-panel"><dl className="document-meta"><div><dt>결재자</dt><dd>{item.approver_name}</dd></div><div><dt>모집 인원</dt><dd>{item.headcount}명</dd></div><div><dt>고용 형태</dt><dd>{item.employment_type}</dd></div><div><dt>경력</dt><dd>{item.experience_label}</dd></div>{item.education_level && <div><dt>학력</dt><dd>{item.education_level}</dd></div>}{item.work_location && <div><dt>근무지</dt><dd>{item.work_location}</dd></div>}{item.salary && <div><dt>급여</dt><dd>{item.salary}</dd></div>}{item.application_deadline && <div><dt>모집 마감</dt><dd>{item.application_deadline}</dd></div>}{item.apply_method && <div><dt>지원 방법</dt><dd>{item.apply_method}</dd></div>}</dl><div className="document-content"><span>채용 사유</span><p>{item.reason}</p><span>주요 업무</span><p>{item.responsibilities}</p><span>필수 역량</span><p>{item.required_skills || "없음"}</p></div><RecruitmentPosterAttachment requestId={item.id} employeeId={currentEmployee.id} originalName={item.poster_original_name} contentType={item.poster_content_type} />{item.approval_document_id && <div className="decision-comment"><Link href={`/approvals/${item.approval_document_id}`}>연결된 전자결재 문서 보기</Link></div>}{item.job_posting_id && <div className="decision-comment"><Link href="/job-postings">생성된 채용공고 목록 보기</Link></div>}</section></section>;
}
