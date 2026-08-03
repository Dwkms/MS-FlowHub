"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useCurrentUser } from "@/features/current-user/current-user-provider";
import { listJobPostings } from "@/features/recruitment/api";
import { RecruitmentPosterAttachment } from "@/features/recruitment/recruitment-poster-attachment";
import type { JobPosting } from "@/types/recruitment";

function formatDate(value: string | null): string {
  return value ? value.replaceAll("-", ". ") : "협의 후 결정";
}

export function JobPostingList() {
  const { currentEmployee } = useCurrentUser();
  const [items, setItems] = useState<JobPosting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void listJobPostings()
      .then((result) => active && setItems(result))
      .catch((reason: unknown) => active && setError(reason instanceof Error ? reason.message : "채용공고를 불러오지 못했습니다."))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  return (
    <section className="content approval-page">
      <div className="page-heading"><div><span className="section-kicker">ATS LITE</span><h1>채용공고</h1><p>승인된 채용 요청에서 생성된 내부 채용공고 초안입니다.</p></div><Link className="secondary-button" href="/recruitment-requests">채용 요청</Link></div>
      <section className="panel approval-list-panel">
        {loading && <div className="state-box">채용공고를 불러오는 중입니다.</div>}
        {!loading && error && <div className="state-box error">{error}</div>}
        {!loading && !error && items.length === 0 && <div className="state-box"><strong>생성된 채용공고가 없습니다.</strong><p>채용 요청 결재가 승인되면 공고 초안이 생성됩니다.</p></div>}
        {!loading && !error && items.length > 0 && <div className="posting-list">{items.map((item) => {
          return <article className="job-posting-card" key={item.id}>
            <header className="job-posting-hero"><div><span className="approval-status approved">공고 초안</span><p className="job-posting-department">{item.request_department_name} · 요청자 {item.requester_name}</p><h2>{item.title}</h2></div><dl><div><dt>모집 인원</dt><dd>{item.headcount}명</dd></div><div><dt>고용 형태</dt><dd>{item.employment_type}</dd></div><div><dt>경력</dt><dd>{item.experience_level}</dd></div><div><dt>희망 입사일</dt><dd>{formatDate(item.desired_start_date)}</dd></div></dl></header>
            <div className="job-posting-body"><section><h3>주요 업무</h3><p>{item.responsibilities}</p></section><section><h3>필수 역량</h3><p>{item.required_skills || "채용 담당자와 협의 후 확정"}</p></section><section><h3>우대 사항</h3><p>{item.preferred_skills || "없음"}</p></section>
            <RecruitmentPosterAttachment requestId={item.recruitment_request_id} employeeId={currentEmployee.id} originalName={item.poster_original_name} contentType={item.poster_content_type} /></div>
          </article>;
        })}</div>}
      </section>
    </section>
  );
}
