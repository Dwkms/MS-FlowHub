"use client";

import { useEffect, useMemo, useState } from "react";

import { listFaqs } from "@/features/manuals/api";
import type { ManualFaq } from "@/types/manual";

/** 표시 순서를 유지한 채 카테고리별로 묶는다. */
function groupByCategory(faqs: ManualFaq[]): [string, ManualFaq[]][] {
  const groups = new Map<string, ManualFaq[]>();
  for (const faq of faqs) {
    const group = groups.get(faq.category);
    if (group) group.push(faq);
    else groups.set(faq.category, [faq]);
  }
  return [...groups];
}

export function FaqList() {
  const [faqs, setFaqs] = useState<ManualFaq[]>([]);
  const [openId, setOpenId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const grouped = useMemo(() => groupByCategory(faqs), [faqs]);
  const visibleGroups = activeCategory
    ? grouped.filter(([category]) => category === activeCategory)
    : grouped;

  useEffect(() => {
    let active = true;
    void listFaqs()
      .then((result) => { if (active) setFaqs(result); })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "FAQ를 불러오지 못했습니다.");
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  return <section className="content faq-page">
    <div className="page-heading"><div><span className="section-kicker">FAQ</span><h1>자주 묻는 질문</h1><p>MS FlowHub 이용 중 자주 묻는 내용을 빠르게 확인하세요.</p></div></div>
    {loading && <div className="state-box">FAQ를 불러오는 중입니다.</div>}
    {!loading && error && <div className="state-box error">{error}</div>}
    {!loading && !error && faqs.length === 0 && <div className="state-box"><strong>등록된 FAQ가 없습니다.</strong></div>}
    {!loading && !error && faqs.length > 0 && <>
      <nav className="faq-category-nav" aria-label="카테고리 필터">
        <button
          type="button"
          className={activeCategory === null ? "active" : undefined}
          onClick={() => setActiveCategory(null)}
        >
          전체
        </button>
        {grouped.map(([category]) => <button
          type="button"
          key={category}
          className={activeCategory === category ? "active" : undefined}
          onClick={() => setActiveCategory(category)}
        >
          {category}
        </button>)}
      </nav>
      {visibleGroups.map(([category, items]) => <section className="faq-group" key={category}>
        {activeCategory === null && <h2 className="faq-group-title">{category}</h2>}
        <div className="faq-list">
          {items.map((faq) => {
            const open = openId === faq.id;
            return <div className={open ? "faq-item open" : "faq-item"} key={faq.id}>
              <button
                className="faq-question"
                aria-expanded={open}
                onClick={() => setOpenId(open ? null : faq.id)}
              >
                <span><em>Q.</em> {faq.question}</span>
                <i aria-hidden="true">{open ? "▲" : "▼"}</i>
              </button>
              {open && <div className="faq-answer">{faq.answer}</div>}
            </div>;
          })}
        </div>
      </section>)}
    </>}
  </section>;
}
