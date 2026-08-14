"use client";

/**
 * 직원·조직 관리 화면.
 *
 * 이 파일에서 가장 조심할 곳은 아래 `canEditSelected`입니다. **화면에 편집 버튼을
 * 보일지 말지**를 정할 뿐이고, 실제 차단은 서버가 다시 합니다. 여기 조건을 느슨하게
 * 해도 API가 403을 돌려주므로 데이터가 새지는 않지만, 반대로 여기만 고치고 서버를
 * 안 고치면 사용자는 버튼을 눌렀다가 오류를 보게 됩니다.
 *
 * 목록에 **누가 보이는지는 서버가 정합니다.** 프론트에서 거르지 않습니다. 파트장이
 * 로그인하면 서버가 이미 자기 파트 직원만 담아 보냅니다
 * (백엔드 `app/domain/org_scope.py`).
 *
 * 조직도는 API가 아니라 정적 PNG를 씁니다. `GET /employees/organization`이 있는데도
 * 이미지를 쓰는 이유는 계층을 그리는 화면을 따로 만들지 않았기 때문입니다.
 * 후속 과제로 `docs/ROADMAP.md`에 남겨 뒀습니다.
 */

import Image from "next/image";
import { type FormEvent, useEffect, useState } from "react";

import {
  getAttendanceChangeHistory,
  getEmployee,
  getEmployeeDepartments,
  listEmployees,
  updateAttendanceStatus,
  updateEmploymentStatusReason,
} from "@/features/employees/api";
import { useCurrentUser } from "@/features/current-user/current-user-provider";
import type {
  AttendanceChangeHistoryItem,
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
  OTHER: "기타",
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

function teamBadgeLabel(
  teamCode: string | null,
  team: string | null,
  department: string,
  employeeName: string,
) {
  if (department === "-" && team === null) return employeeName.slice(0, 1);
  const source = `${teamCode ?? ""} ${team ?? ""} ${department}`.toUpperCase();
  if (source.includes("SW")) return "SW";
  if (source.includes("HW")) return "HW";
  if (source.includes("HR") || source.includes("인사")) return "HR";
  if (source.includes("경영") || source.includes("EXEC")) return "EX";
  return (team ?? department).slice(0, 2);
}

function teamBadgeTone(teamCode: string | null, team: string | null, department: string) {
  const source = `${teamCode ?? ""} ${team ?? ""} ${department}`.toUpperCase();
  if (source.includes("SW") || source.includes("HW") || source.includes("개발")) return "development";
  if (source.includes("CS") || source.includes("고객지원")) return "cs";
  if (source.includes("마케팅") || source.includes("MKT")) return "marketing";
  if (source.includes("인사") || source.includes("HR")) return "hr";
  if (source.includes("기획") || source.includes("PLAN")) return "planning";
  if (source.includes("QA")) return "qa";
  return "executive";
}

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

function AttendanceHistoryPanel({ items }: { items: AttendanceChangeHistoryItem[] }) {
  return <aside className="attendance-history-panel"><div className="attendance-history-heading"><div><h3>근태 변경 이력</h3><p>선택한 날짜에 발생한 상태 변경</p></div><span>{items.length}건</span></div>{items.length === 0 ? <p className="attendance-history-empty">기록된 근태 변경 이력이 없습니다.</p> : <div className="attendance-history-scroll"><ol>{items.map((item) => <li key={item.id}><time>{new Intl.DateTimeFormat("ko-KR", { hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(item.changed_at))}</time><b>{workLabels[item.before_work_status ?? ""] ?? "초기 상태"} → {workLabels[item.after_work_status] ?? item.after_work_status}</b><span>{item.after_reason_summary ?? item.before_reason_summary ?? "사유 없음"}</span><small>변경자: {item.changed_by_name ?? "-"}</small></li>)}</ol></div>}</aside>;
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
  const [attendanceHistory, setAttendanceHistory] = useState<AttendanceChangeHistoryItem[]>([]);
  const [attendanceFormOpen, setAttendanceFormOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(true);
  const [draftWorkStatus, setDraftWorkStatus] = useState("WORKING");
  const [workReasonSummary, setWorkReasonSummary] = useState("");
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
    setAttendanceHistory([]);
    setAttendanceFormOpen(false);
    setHistoryOpen(true);
    void getEmployee(employeeId).then((detail) => {
      setSelected(detail);
      setDraftWorkStatus(detail.daily_work_status ?? "WORKING");
      setWorkReasonSummary(detail.daily_work_reason?.reason_summary ?? "");
      setLeaveReasonCategory(detail.employment_status_reason?.reason_category ?? "PERSONAL");
      setLeaveReasonSummary(detail.employment_status_reason?.reason_summary ?? "");
      setLeavePrivateNote(detail.employment_status_reason?.private_note ?? "");
      return getAttendanceChangeHistory(employeeId, workDate);
    }).then((items) => {
      setAttendanceHistory(items);
    }).catch(() => setError("직원 상세 정보를 불러오지 못했습니다."));
  };
  // 편집 권한 판정 — 서버의 app/domain/org_scope.py와 같은 규칙을 씁니다.
  //   관리자          전사
  //   팀장            같은 부서면 가능
  //   파트장          같은 파트면 가능 (파트가 없으면 불가)
  //   본인            자기 정보는 언제나 가능
  // 규칙을 바꿀 때는 서버도 함께 고쳐야 화면과 판정이 어긋나지 않습니다.
  const canEditSelected = Boolean(selected && (
    ["SUPER_ADMIN", "HR_ADMIN"].includes(currentEmployee.role)
    // 팀장은 부서 전체, 파트장은 자기 파트만. 범위 기준을 역할에 고정해
    // 백엔드 app/domain/org_scope.py와 같은 규칙을 쓴다.
    || (
      currentEmployee.role === "TEAM_ADMIN"
      && currentEmployee.department_id === selected.department_id
    )
    || (
      currentEmployee.role === "PART_ADMIN"
      && currentEmployee.team_code != null
      && currentEmployee.team_code === selected.team_code
    )
    || currentEmployee.id === selected.id
  ));
  const requestCloseDetail = () => {
    const hasOpenEditor = attendanceFormOpen || Boolean(
      selected && canEditSelected && selected.employment_status === "ON_LEAVE"
    );
    if (hasOpenEditor && !window.confirm("작성 중인 내용이 사라집니다. 직원 상세를 닫을까요?")) {
      return;
    }
    setSelected(null);
    setAttendanceFormOpen(false);
  };
  const showWorkReasonInputs = !normalWorkStatuses.has(draftWorkStatus);
  const workReasonRequired = requiredWorkReasonStatuses.has(draftWorkStatus);

  const saveAttendance = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selected) return;
    setSaving(true);
    try {
      const detail = await updateAttendanceStatus(selected.id, {
        work_status: draftWorkStatus,
        reason_summary: showWorkReasonInputs ? workReasonSummary || undefined : undefined,
        work_date: workDate,
      });
      setSelected(detail);
      const history = await getAttendanceChangeHistory(selected.id, workDate);
      setAttendanceHistory(history);
      setAttendanceFormOpen(false);
      setHistoryOpen(true);
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
      const detail = await updateEmploymentStatusReason(selected.id, {
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
    <section className="panel approval-list-panel"><div className="filter-bar employee-filter-bar"><input aria-label="직원 검색" value={search} onChange={(event) => { setSearch(event.target.value); resetPage(); }} placeholder="이름, 사번, 이메일, 담당 역할 검색" /><select aria-label="부서 필터" value={department} onChange={(event) => { setDepartment(event.target.value); resetPage(); }}><option value="">전체 부서</option>{departments.map((item) => <option key={item.id} value={item.code}>{item.name}</option>)}</select><select aria-label="재직 상태 필터" value={employmentStatus} onChange={(event) => { setEmploymentStatus(event.target.value); resetPage(); }}><option value="">전체 상태</option>{Object.entries(employmentLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><select aria-label="근무 상태 필터" value={dailyWorkStatus} onChange={(event) => { setDailyWorkStatus(event.target.value); resetPage(); }}><option value="">전체 근무 상태</option>{Object.entries(workLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><button className="secondary-button organization-chart-button" onClick={() => setChartOpen(true)}>조직도 보기</button></div>
      {!data ? <div className="state-box">직원 데이터를 불러오는 중입니다.</div> : data.items.length === 0 ? <div className="state-box"><strong>검색 결과가 없습니다.</strong><p>검색어나 필터를 변경해 보세요.</p></div> : <><div className="employee-mobile-list"><div className="employee-mobile-head"><span>직원</span><span>직급</span><span>재직 상태</span><span>근무 상태</span></div>{data.items.map((item) => <div className="employee-mobile-row" key={item.id}><button className="employee-mobile-name" onClick={() => openDetail(item.id)}><span className={`team-avatar ${teamBadgeTone(item.team_code, item.team, item.department)}`}>{teamBadgeLabel(item.team_code, item.team, item.department, item.name)}</span><span><b>{item.name}</b>{!(item.department === "-" && item.team === null) && <small>{item.team ?? item.department}</small>}</span></button><span className="employee-mobile-position">{item.position}</span><span className={`employment-badge ${item.employment_status.toLowerCase()}`}>{employmentLabels[item.employment_status]}</span>{item.daily_work_status ? <span className={`work-badge ${item.daily_work_status.toLowerCase()}`}>{workLabels[item.daily_work_status]}</span> : <span className="empty-work-status">-</span>}</div>)}</div><div className="table-wrap employee-desktop-table"><table className="approval-table employee-table"><thead><tr><th>직원</th><th>부서 / 팀</th><th>직급</th><th>담당 역할</th><th>이메일</th><th>재직 상태</th><th>오늘 근무 상태</th><th>근무지</th></tr></thead><tbody>{data.items.map((item) => <tr key={item.id}><td><button className="employee-detail-button" onClick={() => openDetail(item.id)}><span className="mini-avatar">{item.name.slice(0, 1)}</span><b>{item.name}</b><small>{item.employee_no}</small></button></td><td className={item.department === "-" && item.team === null ? "department-team-empty" : undefined}>{item.department}<small>{item.team ?? "-"}</small></td><td>{item.position}</td><td>{item.job_title}</td><td>{item.email}</td><td><span className={`employment-badge ${item.employment_status.toLowerCase()}`}>{employmentLabels[item.employment_status]}</span></td><td>{item.daily_work_status ? <span className={`work-badge ${item.daily_work_status.toLowerCase()}`}>{workLabels[item.daily_work_status]}</span> : <span className="empty-work-status">-</span>}</td><td>{item.work_location}</td></tr>)}</tbody></table></div><div className="pager"><button disabled={page <= 1} onClick={() => setPage(page - 1)}>이전</button><span>{data.page} / {data.total_pages || 1}</span><button disabled={page >= data.total_pages} onClick={() => setPage(page + 1)}>다음</button></div></>}
    </section>
    {selected && <div className="modal-backdrop" onClick={requestCloseDetail}>
      <section className={`employee-modal employee-status-modal ${historyOpen ? "history-open" : "history-closed"}`} onClick={(event) => event.stopPropagation()}>
        <div className="employee-detail-main">
          <div className="employee-detail-heading"><div><h2>직원 상세</h2><p>직원 기본 정보와 오늘의 근태 상태를 확인합니다.</p></div><button className="modal-close" onClick={requestCloseDetail} aria-label="닫기">×</button></div>
          <div className="employee-profile"><span className="mini-avatar large">{selected.name.slice(0, 1)}</span><div><b>{selected.name}</b><p>{selected.position} · {selected.department}{selected.team ? ` · ${selected.team}` : ""} · {selected.employee_no}</p></div></div>
          <section className="employee-attendance-summary"><div className="employee-attendance-heading"><h3>오늘의 근태</h3><time>{workDate}</time></div><div className="employee-current-status"><div><span>현재 근무 상태</span><strong>{selected.daily_work_status ? workLabels[selected.daily_work_status] : "미등록"}</strong></div><span className={`work-badge ${selected.daily_work_status?.toLowerCase() ?? ""}`}>{selected.daily_work_status ? "상태 등록" : "등록 필요"}</span></div></section>
          <div className={`attendance-actions ${canEditSelected && selected.employment_status === "ACTIVE" ? "" : "single-action"}`}>{canEditSelected && selected.employment_status === "ACTIVE" && <button className="primary-button" type="button" onClick={() => setAttendanceFormOpen((open) => !open)}>{attendanceFormOpen ? "근무 상태 변경 닫기" : "근무 상태 변경"}</button>}<button className="secondary-button" type="button" onClick={() => setHistoryOpen((open) => !open)}>{historyOpen ? "변경 이력 닫기" : "변경 이력 보기"}</button></div>
          {selected.employment_status_reason && <ReasonPanel title="재직 상태 상세" status={employmentLabels[selected.employment_status]} reason={selected.employment_status_reason} />}
          {canEditSelected && selected.employment_status === "ACTIVE" && attendanceFormOpen && <form className="status-reason-form" onSubmit={saveAttendance}><h3>근무 상태 변경</h3><select value={draftWorkStatus} onChange={(event) => setDraftWorkStatus(event.target.value)}>{Object.entries(workLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>{showWorkReasonInputs && <textarea value={workReasonSummary} onChange={(event) => setWorkReasonSummary(event.target.value)} placeholder={workReasonRequired ? "공개 사유를 입력해 주세요 (필수)" : "공개 사유를 입력할 수 있습니다 (선택)"} required={workReasonRequired} maxLength={200} />}<button className="primary-button" disabled={saving}>{saving ? "저장 중" : "근무 상태 저장"}</button></form>}
          {canEditSelected && selected.employment_status === "ON_LEAVE" && <form className="status-reason-form" onSubmit={saveLeaveReason}><h3>휴직 사유</h3><select value={leaveReasonCategory} onChange={(event) => setLeaveReasonCategory(event.target.value)}>{Object.entries(reasonCategories).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><textarea value={leaveReasonSummary} onChange={(event) => setLeaveReasonSummary(event.target.value)} placeholder="공개 사유를 입력해 주세요 (필수)" required maxLength={200} /><textarea value={leavePrivateNote} onChange={(event) => setLeavePrivateNote(event.target.value)} placeholder="비공개 상세: 관리자·인사담당자만 조회합니다 (선택)" maxLength={500} /><button className="primary-button" disabled={saving}>{saving ? "저장 중" : "휴직 사유 저장"}</button></form>}
        </div>
        {historyOpen && <AttendanceHistoryPanel items={attendanceHistory} />}
      </section>
    </div>}
    {chartOpen && <div className="modal-backdrop chart-backdrop" onClick={() => setChartOpen(false)}><section className="organization-chart-modal" onClick={(event) => event.stopPropagation()}><div className="organization-chart-heading"><div><span className="section-kicker">ORGANIZATION CHART</span><h2>MS FlowHub 조직도</h2></div><button className="modal-close" onClick={() => setChartOpen(false)} aria-label="닫기">×</button></div><Image src="/organization-chart.png" alt="MS FlowHub 조직도" width={1680} height={943} priority /></section></div>}
  </section>;
}
