"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { listRecruitmentRequests } from "@/features/recruitment/api";
import { recruitmentStatusLabels } from "@/features/recruitment/presentation";
import type { RecruitmentRequest } from "@/types/recruitment";

export function RecruitmentList() {
  const [items, setItems] = useState<RecruitmentRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void listRecruitmentRequests()
      .then((result) => active && setItems(result))
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "채용 요청을 불러오지 못했습니다.");
      })
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  return (
    <section className="content approval-page">
      <div className="page-heading">
        <div><span className="section-kicker">ATS LITE</span><h1>채용 요청</h1><p>채용 요청을 결재로 상신하고 결과를 확인합니다.</p></div>
        <div className="heading-actions"><Link className="secondary-button" href="/job-postings">채용공고</Link><Link className="primary-button" href="/recruitment-requests/new">새 채용 요청</Link></div>
      </div>
      <section className="panel approval-list-panel">
        {loading && <div className="state-box">채용 요청을 불러오는 중입니다.</div>}
        {!loading && error && <div className="state-box error">{error}</div>}
        {!loading && !error && items.length === 0 && <div className="state-box"><strong>표시할 채용 요청이 없습니다.</strong><p>새 채용 요청을 작성해 결재로 상신해 보세요.</p></div>}
        {!loading && !error && items.length > 0 && <div className="table-wrap"><table className="approval-table"><thead><tr><th>모집 직무</th><th>요청 부서</th><th>요청자</th><th>결재자</th><th>상태</th><th>작성일</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td><Link href={`/recruitment-requests/${item.id}`}>{item.position_title}</Link></td><td>{item.request_department_name}</td><td>{item.requester_name}</td><td>{item.approver_name}</td><td><span className={`approval-status ${item.status.toLowerCase()}`}>{recruitmentStatusLabels[item.status]}</span></td><td>{new Intl.DateTimeFormat("ko-KR").format(new Date(item.created_at))}</td></tr>)}</tbody></table></div>}
      </section>
    </section>
  );
}
