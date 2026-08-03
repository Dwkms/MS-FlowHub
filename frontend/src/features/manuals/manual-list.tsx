"use client";
/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { listManualCategories, listManuals } from "@/features/manuals/api";
import { formatManualDate, manualRoleLabels } from "@/features/manuals/presentation";
import { useCurrentUser } from "@/features/current-user/current-user-provider";
import type { ManualCategory, ManualListItem } from "@/types/manual";

export function ManualList() {
  const { currentEmployee } = useCurrentUser();
  const [categories, setCategories] = useState<ManualCategory[]>([]);
  const [manuals, setManuals] = useState<ManualListItem[]>([]);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void Promise.all([listManualCategories(), listManuals({ search, categoryId })])
      .then(([nextCategories, nextManuals]) => {
        if (!active) return;
        setCategories(nextCategories);
        setManuals(nextManuals);
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "매뉴얼을 불러오지 못했습니다.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [search, categoryId]);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSearch(searchInput.trim());
  }

  return <section className="content manual-page">
    <div className="page-heading">
      <div><span className="section-kicker">EMPLOYEE MANUAL</span><h1>직원 매뉴얼</h1><p>업무 기능의 사용 방법과 핵심 흐름을 한눈에 확인하세요.</p></div>
      {["SUPER_ADMIN", "HR_ADMIN", "ADMIN"].includes(currentEmployee.role) && <Link className="primary-button" href="/manuals/new">매뉴얼 작성</Link>}
    </div>
    <section className="panel manual-list-panel">
      <form className="filter-bar" onSubmit={submitSearch}>
        <input aria-label="매뉴얼 검색" placeholder="제목 또는 내용 검색" value={searchInput} onChange={(event) => setSearchInput(event.target.value)} />
        <select aria-label="매뉴얼 카테고리" value={categoryId} onChange={(event) => { setLoading(true); setError(null); setCategoryId(event.target.value); }}>
          <option value="">전체 카테고리</option>
          {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
        </select>
        <button className="secondary-button" type="submit">검색</button>
      </form>
      {loading && <div className="state-box">매뉴얼을 불러오는 중입니다.</div>}
      {!loading && error && <div className="state-box error">{error}</div>}
      {!loading && !error && manuals.length === 0 && <div className="state-box"><strong>조건에 맞는 매뉴얼이 없습니다.</strong><p>검색어나 카테고리를 변경해 보세요.</p></div>}
      {!loading && !error && manuals.length > 0 && <div className="manual-card-grid">
        {manuals.map((manual) => <Link className="manual-card" href={`/manuals/${manual.slug}`} key={manual.id}>
          {manual.thumbnail_url && <div className="manual-card-image"><img src={manual.thumbnail_url} alt="" /></div>}
          <div className="manual-card-body"><div className="manual-card-tags">{manual.is_pinned && <span className="manual-pin">중요</span>}<span>{manual.category.name}</span></div><h2>{manual.title}</h2><p>{manual.summary}</p><div className="manual-card-footer"><span>{manual.target_roles.map((role) => manualRoleLabels[role]).join(" · ")}</span><time>{formatManualDate(manual.updated_at)} 수정</time></div></div>
        </Link>)}
      </div>}
    </section>
  </section>;
}
