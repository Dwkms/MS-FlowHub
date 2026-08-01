"use client";

import Image from "next/image";
import { type FormEvent, useEffect, useState } from "react";

import {
  getEmployee,
  getEmployeeDepartments,
  listEmployees,
  updateAttendanceStatus,
  updateEmploymentStatusReason,
} from "@/features/employees/api";
import { useCurrentUser } from "@/features/current-user/current-user-provider";
import type {
  Department,
  EmployeeDetail,
  EmployeePage,
  StatusReasonDetail,
} from "@/types/employee";

const employmentLabels: Record<string, string> = {
  ACTIVE: "재직",
  ON_LEAVE: "휴직",
  SCHEDULED: "입사 예정",
  RESIGNED: "퇴직",
};
const workLabels: Record<string, string> = {
  WORKING: "근무 중",
  REMOTE_WORK: "재택근무",
  OUT_OF_OFFICE: "외근",
  BUSINESS_TRIP: "출장",
  ANNUAL_LEAVE: "휴가",
  MORNING_HALF: "오전 반차",
  AFTERNOON_HALF: "오후 반차",
  SICK_LEAVE: "병가",
  TRAINING: "교육",
  OFF_WORK: "퇴근",
  ABSENT: "결근",
};
const reasonCategories = {
  HEALTH: "건강",
  PERSONAL: "개인 일정",
  BUSINESS: "업무",
  TRAINING: "교육",
  WORK: "업무 방식",
  OTHER: "기타",
};
const normalWorkStatuses = new Set(["WORKING", "OFF_WORK"]);
const requiredWorkReasonStatuses = new Set(["SICK_LEAVE", "ABSENT"]);

function queryValue(name: string, fallback = "") {
  if (typeof window === "undefined") return fallback;
  return new URLSearchParams(window.location.search).get(name) ?? fallback;
}

function formatDate(value: string | null) {
  return value ? new Intl.DateTimeFormat("ko-KR").format(new Date(value)) : "-";
}

function formatPeriod(reason: StatusReasonDetail) {
  const start = formatDate(reason.period_start);
  const end = reason.period_end ? formatDate(reason.period_end) : null;
  return end && end !== start ? `${start} ~ ${end}` : start;
}

function ReasonPanel({ title, status, reason }: { title: string; status: string; reason: StatusReasonDetail }) {
  return <section className="status-detail-panel"><h3>{title} · {status}</h3><dl><div><dt>적용 기간</dt><dd>{formatPeriod(reason)}</dd></div><div><dt>공개 사유</dt><dd>{reason.reason_summary ?? "등록된 공개 사유가 없습니다."}</dd></div>{reason.private_note && <div><dt>비공개 상세</dt><dd>{reason.private_note}</dd></div>}<div><dt>등록자</dt><dd>{reason.registered_by_name ?? "-"}</dd></div><div><dt>등록일</dt><dd>{reason.registered_at ? new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(reason.registered_at)) : "-"}</dd></div></dl></section>;
}

export function EmployeeManagement() {
  const { currentEmployee } = useCurrentUser();
  const [data, setData] = useState<EmployeePage | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [search, setSearch] = useState(() => queryValue("search"));
  const [department, setDepartment] = useState(() => queryValue("department_code"));
  const [employmentStatus, setEmploymentStatus] = useState(() => queryValue("employment_status"));
  const [dailyWorkStatus, setDailyWorkStatus] = useState(() => queryValue("daily_work_status"));
  const [workDate] = useState(() => queryValue("work_date", new Date().toISOString().slice(0, 10)));
  const [page, setPage] = useState(() => Number(queryValue("page", "1")) || 1);
  const [reloadToken, setReloadToken] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<EmployeeDetail | null>(null);
  const [draftWorkStatus, setDraftWorkStatus] = useState("WORKING");
  const [workReasonCategory, setWorkReasonCategory] = useState("OTHER");
  const [workReasonSummary, setWorkReasonSummary] = useState("");
  const [workPrivateNote, setWorkPrivateNote] = useState("");
  const [leaveReasonCategory, setLeaveReasonCategory] = useState("PERSONAL");
  const [leaveReasonSummary, setLeaveReasonSummary] = useState("");
  const [leavePrivateNote, setLeavePrivateNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [chartOpen, setChartOpen] = useState(false);

  useEffect(() => {
    void getEmployeeDepartments().then(setDepartments).catch(() => setError("부서 정보를 불러오지 못했습니다."));
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (department) params.set("department_code", department);
    if (employmentStatus) params.set("employment_status", employmentStatus);
    if (dailyWorkStatus) params.set("daily_work_status", dailyWorkStatus);
    params.set("work_date", workDate);
    if (page > 1) params.set("page", String(page));
    window.history.replaceState(null, "", `/employees?${params}`);

    let active = true;
    void listEmployees({ page, search: search || undefined, department_code: department || undefined, employment_status: employmentStatus || undefined, daily_work_status: dailyWorkStatus || undefined, work_date: workDate })
      .then((result) => { if (active) { setData(result); setError(null); } })
      .catch(() => active && setError("직원 목록을 불러오지 못했습니다."));
    return () => { active = false; };
  }, [dailyWorkStatus, department, employmentStatus, page, reloadToken, search, workDate]);

  const resetPage = () => setPage(1);
  const openDetail = (employeeId: string) => {
    void getEmployee(employeeId, currentEmployee.id).then((detail) => {
      setSelected(detail);
      setDraftWorkStatus(detail.daily_work_status ?? "WORKING");
      setWorkReasonCategory(detail.daily_work_reason?.reason_category ?? "OTHER");
      setWorkReasonSummary(detail.daily_work_reason?.reason_summary ?? "");
      setWorkPrivateNote(detail.daily_work_reason?.private_note ?? "");
      setLeaveReasonCategory(detail.employment_status_reason?.reason_category ?? "PERSONAL");
      setLeaveReasonSummary(detail.employment_status_reason?.reason_summary ?? "");
      setLeavePrivateNote(detail.employment_status_reason?.private_note ?? "");
    }).catch(() => setError("직원 상세 정보를 불러오지 못했습니다."));
  };
  const canEditSelected = Boolean(selected && (currentEmployee.role === "ADMIN" || currentEmployee.id === selected.id));
  const showWorkReasonInputs = !normalWorkStatuses.has(draftWorkStatus);
  const workReasonRequired = requiredWorkReasonStatuses.has(draftWorkStatus);

  const saveAttendance = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selected) return;
    setSaving(true);
    try {
      const detail = await updateAttendanceStatus(selected.id, currentEmployee.id, {
        work_status: draftWorkStatus,
        reason_category: showWorkReasonInputs ? workReasonCategory : undefined,
        reason_summary: showWorkReasonInputs ? workReasonSummary || undefined : undefined,
        private_note: showWorkReasonInputs ? workPrivateNote || undefined : undefined,
        work_date: workDate,
      });
      setSelected(detail);
      setReloadToken((value) => value + 1);
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "근무 상태를 저장하지 못했습니다.");
    } finally { setSaving(false); }
  };

  const saveLeaveReason = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selected) return;
    setSaving(true);
    try {
      const detail = await updateEmploymentStatusReason(selected.id, currentEmployee.id, {
        reason_category: leaveReasonCategory,
        reason_summary: leaveReasonSummary,
        private_note: leavePrivateNote || undefined,
      });
      setSelected(detail);
      setReloadToken((value) => value + 1);
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "휴직 사유를 저장하지 못했습니다.");
    } finally { setSaving(false); }
  };

  return <section className="content approval-page employee-page">
    <div className="page-heading"><div><span className="section-kicker">EMPLOYEE MANAGEMENT</span><h1>직원 · 조직 관리</h1><p>조직과 직원 정보를 실제 DB 데이터로 조회합니다.</p></div><span className="employee-count">{data ? `${data.total}명` : "불러오는 중"}</span></div>
    {error && <div className="inline-alert error">{error}</div>}
    <section className="panel approval-list-panel"><div className="filter-bar employee-filter-bar"><input value={search} onChange={(event) => { setSearch(event.target.value); resetPage(); }} placeholder="이름, 사번, 이메일, 담당 역할 검색" /><select value={department} onChange={(event) => { setDepartment(event.target.value); resetPage(); }}><option value="">전체 부서</option>{departments.map((item) => <option key={item.id} value={item.code}>{item.name}</option>)}</select><select value={employmentStatus} onChange={(event) => { setEmploymentStatus(event.target.value); resetPage(); }}><option value="">전체 상태</option>{Object.entries(employmentLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><select value={dailyWorkStatus} onChange={(event) => { setDailyWorkStatus(event.target.value); resetPage(); }}><option value="">전체 근무 상태</option>{Object.entries(workLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><button className="secondary-button organization-chart-button" onClick={() => setChartOpen(true)}>조직도 보기</button></div>
      {!data ? <div className="state-box">직원 데이터를 불러오는 중입니다.</div> : data.items.length === 0 ? <div className="state-box"><strong>검색 결과가 없습니다.</strong><p>검색어나 필터를 변경해 보세요.</p></div> : <><div className="table-wrap"><table className="approval-table employee-table"><thead><tr><th>직원</th><th>부서 / 팀</th><th>직급</th><th>담당 역할</th><th>이메일</th><th>재직 상태</th><th>오늘 근무 상태</th><th>근무지</th></tr></thead><tbody>{data.items.map((item) => <tr key={item.id}><td><button className="employee-detail-button" onClick={() => openDetail(item.id)}><span className="mini-avatar">{item.name.slice(0, 1)}</span><b>{item.name}</b><small>{item.employee_no}</small></button></td><td>{item.department}<small>{item.team ?? "-"}</small></td><td>{item.position}</td><td>{item.job_title}</td><td>{item.email}</td><td><span className="status-with-info"><span className={`employment-badge ${item.employment_status.toLowerCase()}`}>{employmentLabels[item.employment_status]}</span>{item.has_employment_status_reason && <button className="reason-info-button" onClick={() => openDetail(item.id)} aria-label={`${item.name} 재직 상태 사유 보기`} title="상태 사유 보기">ⓘ</button>}</span></td><td>{item.daily_work_status ? <span className="status-with-info"><span className={`work-badge ${item.daily_work_status.toLowerCase()}`}>{workLabels[item.daily_work_status]}</span>{item.has_daily_work_reason && <button className="reason-info-button" onClick={() => openDetail(item.id)} aria-label={`${item.name} 근무 상태 사유 보기`} title="상태 사유 보기">ⓘ</button>}</span> : <span className="empty-work-status">-</span>}</td><td>{item.work_location}</td></tr>)}</tbody></table></div><div className="pager"><button disabled={page <= 1} onClick={() => setPage(page - 1)}>이전</button><span>{data.page} / {data.total_pages || 1}</span><button disabled={page >= data.total_pages} onClick={() => setPage(page + 1)}>다음</button></div></>}
    </section>
    {selected && <div className="modal-backdrop" onClick={() => setSelected(null)}><section className="employee-modal employee-status-modal" onClick={(event) => event.stopPropagation()}><button className="modal-close" onClick={() => setSelected(null)} aria-label="닫기">×</button><span className="mini-avatar large">{selected.name.slice(0, 1)}</span><h2>{selected.name} <small>{selected.employee_no}</small></h2><p>{selected.department}{selected.team ? ` · ${selected.team}` : ""} · {selected.position}</p><dl><div><dt>담당 역할</dt><dd>{selected.job_title}</dd></div><div><dt>재직 / 근무</dt><dd>{employmentLabels[selected.employment_status]} / {selected.daily_work_status ? workLabels[selected.daily_work_status] : "-"}</dd></div></dl>{selected.daily_work_reason && <ReasonPanel title="근무 상태 상세" status={workLabels[selected.daily_work_status ?? ""] ?? "-"} reason={selected.daily_work_reason} />}{selected.employment_status_reason && <ReasonPanel title="재직 상태 상세" status={employmentLabels[selected.employment_status]} reason={selected.employment_status_reason} />}
      {canEditSelected && selected.employment_status === "ACTIVE" && <form className="status-reason-form" onSubmit={saveAttendance}><h3>오늘의 근무 상태</h3><select value={draftWorkStatus} onChange={(event) => setDraftWorkStatus(event.target.value)}>{Object.entries(workLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>{showWorkReasonInputs && <><select value={workReasonCategory} onChange={(event) => setWorkReasonCategory(event.target.value)}>{Object.entries(reasonCategories).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><textarea value={workReasonSummary} onChange={(event) => setWorkReasonSummary(event.target.value)} placeholder={workReasonRequired ? "공개 사유를 입력해 주세요 (필수)" : "공개 사유를 입력할 수 있습니다 (선택)"} required={workReasonRequired} maxLength={200} /><textarea value={workPrivateNote} onChange={(event) => setWorkPrivateNote(event.target.value)} placeholder="비공개 상세: 관리자·인사담당자만 조회합니다 (선택)" maxLength={500} /></>}<button className="primary-button" disabled={saving}>{saving ? "저장 중" : "근무 상태 저장"}</button></form>}
      {canEditSelected && selected.employment_status === "ON_LEAVE" && <form className="status-reason-form" onSubmit={saveLeaveReason}><h3>휴직 사유</h3><select value={leaveReasonCategory} onChange={(event) => setLeaveReasonCategory(event.target.value)}>{Object.entries(reasonCategories).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><textarea value={leaveReasonSummary} onChange={(event) => setLeaveReasonSummary(event.target.value)} placeholder="공개 사유를 입력해 주세요 (필수)" required maxLength={200} /><textarea value={leavePrivateNote} onChange={(event) => setLeavePrivateNote(event.target.value)} placeholder="비공개 상세: 관리자·인사담당자만 조회합니다 (선택)" maxLength={500} /><button className="primary-button" disabled={saving}>{saving ? "저장 중" : "휴직 사유 저장"}</button></form>}
    </section></div>}
    {chartOpen && <div className="modal-backdrop chart-backdrop" onClick={() => setChartOpen(false)}><section className="organization-chart-modal" onClick={(event) => event.stopPropagation()}><div className="organization-chart-heading"><div><span className="section-kicker">ORGANIZATION CHART</span><h2>MS FlowHub 조직도</h2></div><button className="modal-close" onClick={() => setChartOpen(false)} aria-label="닫기">×</button></div><Image src="/organization-chart.png" alt="MS FlowHub 조직도" width={1536} height={1024} priority /></section></div>}
  </section>;
}
