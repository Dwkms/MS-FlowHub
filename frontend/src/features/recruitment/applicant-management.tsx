"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { useCurrentUser } from "@/features/current-user/current-user-provider";
import {
  createApplicant,
  deleteApplicant,
  getApplicant,
  listApplicants,
  listJobPostings,
  updateApplicant,
  updateApplicantStage,
} from "@/features/recruitment/api";
import type { Applicant, ApplicantInput, ApplicantStage, JobPosting } from "@/types/recruitment";

const stageLabels: Record<ApplicantStage, string> = {
  APPLIED: "지원 접수",
  SCREENING: "서류 검토",
  INTERVIEW: "1차 면접",
  OFFERED: "2차 면접",
  HIRED: "채용 확정",
  REJECTED: "불합격",
};

const editableRoles = new Set(["SUPER_ADMIN", "HR_ADMIN"]);
const initialInput: ApplicantInput = { name: "", email: "", phone: "", career_summary: "" };

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export function ApplicantManagement() {
  const { currentEmployee } = useCurrentUser();
  const [postings, setPostings] = useState<JobPosting[]>([]);
  const [items, setItems] = useState<Applicant[]>([]);
  const [selected, setSelected] = useState<Applicant | null>(null);
  const [postingId, setPostingId] = useState("");
  const [stage, setStage] = useState<ApplicantStage | "">("");
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<ApplicantInput>(initialInput);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState<ApplicantInput>(initialInput);
  const [nextStage, setNextStage] = useState<ApplicantStage | "">("");
  const [stageNote, setStageNote] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const canEdit = editableRoles.has(currentEmployee.role);

  const applyApplicantResult = useCallback((result: Applicant[]) => {
    setItems(result);
    setSelected((current) => {
      const refreshed = current && result.find((item) => item.id === current.id);
      return refreshed ? { ...current, ...refreshed, stage_histories: current.stage_histories } : null;
    });
    setError(null);
  }, []);

  const loadApplicants = useCallback(async (nextPostingId = postingId) => {
    setLoading(true);
    try {
      const result = await listApplicants({ jobPostingId: nextPostingId || undefined, stage: stage || undefined, search: search || undefined });
      applyApplicantResult(result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "지원자 정보를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, [applyApplicantResult, postingId, search, stage]);

  useEffect(() => {
    let active = true;
    void listJobPostings()
      .then((result) => {
        if (!active) return;
        setPostings(result);
        setPostingId((current) => current || result[0]?.id || "");
      })
      .catch((reason: unknown) => active && setError(reason instanceof Error ? reason.message : "채용공고를 불러오지 못했습니다."));
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    void listApplicants({ jobPostingId: postingId || undefined, stage: stage || undefined, search: search || undefined })
      .then((result) => active && applyApplicantResult(result))
      .catch((reason: unknown) => active && setError(reason instanceof Error ? reason.message : "지원자 정보를 불러오지 못했습니다."))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [applyApplicantResult, postingId, search, stage]);

  async function selectApplicant(applicantId: string) {
    try {
      setSelected(await getApplicant(applicantId));
      setNextStage("");
      setStageNote("");
      setEditing(false);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "지원자 상세를 불러오지 못했습니다.");
    }
  }

  function startEdit() {
    if (!selected) return;
    setEditForm({
      name: selected.name,
      email: selected.email,
      phone: selected.phone ?? "",
      career_summary: selected.career_summary,
    });
    setEditing(true);
  }

  async function submitEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    setSaving(true);
    try {
      const updated = await updateApplicant(selected.id, editForm);
      setSelected((current) => (current ? { ...updated, stage_histories: current.stage_histories } : updated));
      setEditing(false);
      await loadApplicants();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "지원자 정보를 수정하지 못했습니다.");
    } finally { setSaving(false); }
  }

  async function submitCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!postingId) { setError("먼저 채용공고를 선택하세요."); return; }
    setSaving(true);
    try {
      const created = await createApplicant(postingId, form);
      setShowForm(false);
      setForm(initialInput);
      await loadApplicants();
      setSelected(created);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "지원자를 등록하지 못했습니다.");
    } finally { setSaving(false); }
  }

  async function changeStage(nextStage: ApplicantStage) {
    if (!selected) return;
    setSaving(true);
    try {
      const updated = await updateApplicantStage(selected.id, nextStage, stageNote);
      setSelected(updated);
      setNextStage("");
      setStageNote("");
      await loadApplicants();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "단계를 변경하지 못했습니다.");
    } finally { setSaving(false); }
  }

  async function removeApplicant() {
    if (!selected || !window.confirm(`${selected.name} 지원자를 삭제할까요?`)) return;
    setSaving(true);
    try {
      await deleteApplicant(selected.id);
      setSelected(null);
      await loadApplicants();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "지원자를 삭제하지 못했습니다.");
    } finally { setSaving(false); }
  }

  const availableStages = useMemo(() => Object.entries(stageLabels) as [ApplicantStage, string][], []);
  return <section className="content approval-page applicants-page">
    <div className="page-heading"><div><span className="section-kicker">ATS LITE</span><h1>지원자 관리</h1><p>채용공고별 지원자를 등록하고 전형 단계를 관리합니다.</p></div><div className="heading-actions"><Link className="secondary-button" href="/job-postings">채용공고</Link>{canEdit && <button className="primary-button" onClick={() => setShowForm((open) => !open)}>{showForm ? "등록 닫기" : "지원자 등록"}</button>}</div></div>
    {error && <div className="inline-alert error">{error}</div>}
    {canEdit && showForm && <form className="panel applicant-form" onSubmit={submitCreate}><h2>지원자 등록</h2><div className="form-grid"><label className="form-field"><span>이름 *</span><input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label><label className="form-field"><span>이메일 *</span><input required type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></label><label className="form-field"><span>전화번호</span><input value={form.phone ?? ""} onChange={(event) => setForm({ ...form, phone: event.target.value })} /></label><label className="form-field full"><span>경력 요약</span><textarea value={form.career_summary ?? ""} onChange={(event) => setForm({ ...form, career_summary: event.target.value })} /></label></div><div className="form-actions"><button className="primary-button" disabled={saving}>{saving ? "등록 중..." : "등록"}</button></div></form>}
    <section className="panel applicant-filter-bar"><select value={postingId} onChange={(event) => setPostingId(event.target.value)}><option value="">전체 채용공고</option>{postings.map((posting) => <option value={posting.id} key={posting.id}>{posting.title} · {posting.request_department_name}</option>)}</select><select value={stage} onChange={(event) => setStage(event.target.value as ApplicantStage | "")}><option value="">전체 단계</option>{availableStages.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select><input placeholder="이름 또는 이메일 검색" value={search} onChange={(event) => setSearch(event.target.value)} /><button className="secondary-button" onClick={() => void loadApplicants()}>조회</button></section>
    <div className="applicant-layout"><section className="panel applicant-list-panel"><div className="applicant-list-heading"><strong>지원자 목록</strong><span>{items.length}명</span></div>{loading && <div className="state-box">지원자 정보를 불러오는 중입니다.</div>}{!loading && items.length === 0 && <div className="state-box">조건에 맞는 지원자가 없습니다.</div>}{!loading && items.map((item) => <button className={selected?.id === item.id ? "applicant-row selected" : "applicant-row"} onClick={() => void selectApplicant(item.id)} key={item.id}><span className="applicant-avatar">{item.name.slice(0, 1)}</span><span><b>{item.name}</b><small>{item.job_posting_title} · {item.request_department_name}</small></span><span className={`applicant-stage ${item.stage.toLowerCase()}`}>{stageLabels[item.stage]}</span></button>)}</section>
      <section className="panel applicant-detail-panel">{selected ? <><div className="applicant-detail-heading"><div><span className="section-kicker">APPLICANT DETAIL</span><h2>{selected.name}</h2><p>{selected.job_posting_title} · {selected.request_department_name}</p></div><span className={`applicant-stage ${selected.stage.toLowerCase()}`}>{stageLabels[selected.stage]}</span></div>
        {editing ? <form className="panel applicant-form applicant-edit-form" onSubmit={submitEdit}><h2>지원자 정보 수정</h2><div className="form-grid"><label className="form-field"><span>이름 *</span><input required value={editForm.name} onChange={(event) => setEditForm({ ...editForm, name: event.target.value })} /></label><label className="form-field"><span>이메일 *</span><input required type="email" value={editForm.email} onChange={(event) => setEditForm({ ...editForm, email: event.target.value })} /></label><label className="form-field"><span>전화번호</span><input value={editForm.phone ?? ""} onChange={(event) => setEditForm({ ...editForm, phone: event.target.value })} /></label><label className="form-field full"><span>경력 요약</span><textarea value={editForm.career_summary ?? ""} onChange={(event) => setEditForm({ ...editForm, career_summary: event.target.value })} /></label></div><div className="form-actions"><button type="button" className="secondary-button" disabled={saving} onClick={() => setEditing(false)}>취소</button><button className="primary-button" disabled={saving}>{saving ? "저장 중..." : "저장"}</button></div></form> : <>
          <dl className="applicant-meta"><div><dt>이메일</dt><dd>{selected.email}</dd></div><div><dt>전화번호</dt><dd>{selected.phone || "미등록"}</dd></div><div><dt>등록자</dt><dd>{selected.created_by_name}</dd></div></dl>
          <section className="applicant-summary"><h3>경력 요약</h3><p>{selected.career_summary || "입력된 경력 요약이 없습니다."}</p></section>
        </>}
        {canEdit && !["HIRED", "REJECTED"].includes(selected.stage) && <section className="applicant-stage-form"><h3>전형 단계 변경</h3><select value={nextStage} onChange={(event) => setNextStage(event.target.value as ApplicantStage | "")} disabled={saving}><option value="">변경할 단계 선택</option>{availableStages.filter(([value]) => value !== selected.stage).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select><textarea placeholder="변경 메모 (불합격 처리 시 필수)" value={stageNote} onChange={(event) => setStageNote(event.target.value)} /><button className="primary-button" disabled={saving || !nextStage} onClick={() => { if (nextStage) void changeStage(nextStage); }}>단계 변경</button></section>}
        <section className="applicant-history"><h3>전형 단계 이력</h3><div className="applicant-history-list">{selected.stage_histories.map((history) => <article key={history.id}><i /><div><strong>{history.from_stage ? `${stageLabels[history.from_stage]} → ` : ""}{stageLabels[history.to_stage]}</strong><p>{history.note || "메모 없음"}</p><small>{history.actor_name} · {formatDate(history.created_at)}</small></div></article>)}</div></section>
        {canEdit && <div className="applicant-detail-actions"><button className="secondary-button" disabled={saving} onClick={startEdit}>수정</button><button className="danger-button" disabled={saving} onClick={() => void removeApplicant()}>삭제</button></div>}
      </> : <div className="state-box">왼쪽 목록에서 지원자를 선택하세요.</div>}</section></div>
  </section>;
}
