"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { listApprovals } from "@/features/approvals/api";
import {
  documentTypeLabels,
  formatDate,
  statusLabels,
} from "@/features/approvals/presentation";
import type {
  ApprovalDocument,
  ApprovalStatus,
} from "@/types/approval";

export function ApprovalList() {
  const [documents, setDocuments] = useState<ApprovalDocument[]>([]);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<ApprovalStatus | "">("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void listApprovals({
      search,
      status,
    })
      .then((result) => {
        if (active) setDocuments(result);
      })
      .catch((reason: unknown) => {
        if (active) {
          setDocuments([]);
          setError(reason instanceof Error ? reason.message : "목록을 불러오지 못했습니다.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [search, status]);

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSearch(searchInput.trim());
  }

  return (
    <section className="content approval-page">
      <div className="page-heading">
        <div>
          <span className="section-kicker">APPROVALS</span>
          <h1>전자결재</h1>
          <p>관리자는 전체 문서를, 그 외 사용자는 관련 문서를 확인합니다.</p>
        </div>
        <Link className="primary-button" href="/approvals/new">
          새 문서 작성
        </Link>
      </div>

      <section className="panel approval-list-panel">
        <form className="filter-bar" onSubmit={handleSearch}>
          <input
            aria-label="문서 검색"
            placeholder="문서 제목 검색"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
          />
          <select
            aria-label="결재 상태 필터"
            value={status}
            onChange={(event) => {
              setLoading(true);
              setError(null);
              setStatus(event.target.value as ApprovalStatus | "");
            }}
          >
            <option value="">전체 상태</option>
            {Object.entries(statusLabels).map(([value, label]) => (
              <option value={value} key={value}>
                {label}
              </option>
            ))}
          </select>
          <button className="secondary-button" type="submit">
            검색
          </button>
        </form>

        {loading && <div className="state-box">전자결재 문서를 불러오는 중입니다.</div>}
        {!loading && error && <div className="state-box error">{error}</div>}
        {!loading && !error && documents.length === 0 && (
          <div className="state-box">
            <strong>표시할 전자결재 문서가 없습니다.</strong>
            <p>새 문서를 작성하거나 검색 조건을 변경해 보세요.</p>
          </div>
        )}
        {!loading && !error && documents.length > 0 && (
          <div className="table-wrap">
            <table className="approval-table">
              <thead>
                <tr>
                  <th>문서 제목</th>
                  <th>문서 종류</th>
                  <th>기안자</th>
                  <th>부서</th>
                  <th>결재 상태</th>
                  <th>작성일</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((document) => (
                  <tr key={document.id}>
                    <td>
                      <Link href={`/approvals/${document.id}`}>{document.title}</Link>
                    </td>
                    <td>{documentTypeLabels[document.document_type]}</td>
                    <td>{document.author_name}</td>
                    <td>{document.department_name}</td>
                    <td>
                      <span className={`approval-status ${document.status.toLowerCase()}`}>
                        {statusLabels[document.status]}
                      </span>
                    </td>
                    <td>{formatDate(document.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </section>
  );
}
