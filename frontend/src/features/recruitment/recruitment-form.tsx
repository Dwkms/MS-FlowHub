"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { useCurrentUser } from "@/features/current-user/current-user-provider";
import { getDepartments } from "@/features/dashboard/api";
import { isManagerLevelApprover } from "@/lib/approver-policy";
import {
  createRecruitmentRequest,
  uploadRecruitmentPoster,
} from "@/features/recruitment/api";
import {
  APPLY_METHODS,
  EDUCATION_LEVELS,
  EMPLOYMENT_TYPES,
  EXPERIENCE_CHOICES,
  EXPERIENCE_YEARS,
  type ApplyMethod,
  type EducationLevel,
  type EmploymentType,
  type ExperienceLevel,
} from "@/features/recruitment/recruitment-options";
import type { Department } from "@/types/dashboard";

const MAX_POSTER_SIZE = 5 * 1024 * 1024;
const POSTER_TYPES = ["image/jpeg", "image/png", "image/webp", "application/pdf"];
export function RecruitmentForm() {
  const router = useRouter();
  const { currentEmployee, employees } = useCurrentUser();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [departmentId, setDepartmentId] = useState(currentEmployee.department_id);
  const [approverId, setApproverId] = useState("");
  const [posterFile, setPosterFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [departmentError, setDepartmentError] = useState<string | null>(null);
  const [form, setForm] = useState({
    positionTitle: "",
    headcount: "1",
    employmentType: "정규직" as EmploymentType,
    experienceLevel: "NEW" as ExperienceLevel,
    // 경력을 골랐을 때만 쓰인다. 되돌리면 서버가 잘라내지만 여기서도 보내지 않는다.
    experienceYearsMin: "3",
    educationLevel: "학력무관" as EducationLevel,
    workLocation: "",
    salary: "",
    applicationDeadline: "",
    applyMethod: "이메일" as ApplyMethod,
    reason: "",
    responsibilities: "",
    requiredSkills: "",
    preferredSkills: "",
    desiredStartDate: "",
  });
  const availableDepartments = departments.filter((department) => department.code !== "EXEC");
  const canSelectDepartment = availableDepartments.length > 1;
  const selectedDepartmentId = availableDepartments.some(
    (department) => department.id === departmentId,
  )
    ? departmentId
    : (availableDepartments[0]?.id ?? currentEmployee.department_id);
  const canSelectSelfAsApprover = currentEmployee.role === "SUPER_ADMIN";
  const approvers = useMemo(
    () =>
      employees.filter(
        (item) =>
          (canSelectSelfAsApprover || item.id !== currentEmployee.id) &&
          isManagerLevelApprover(item.position),
      ),
    [canSelectSelfAsApprover, currentEmployee.id, employees],
  );
  const selectedApproverId = approvers.some((employee) => employee.id === approverId)
    ? approverId
    : (approvers[0]?.id ?? "");

  useEffect(() => {
    void getDepartments()
      .then((result) => {
        setDepartments(result);
        setDepartmentError(result.length > 0 ? null : "요청할 수 있는 부서 정보가 없습니다.");
      })
      .catch(() => setDepartmentError("부서 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요."));
  }, []);

  useEffect(() => {
    if (!approvers.some((employee) => employee.id === approverId)) {
      queueMicrotask(() => setApproverId(approvers[0]?.id ?? ""));
    }
  }, [approverId, approvers]);

  function change(name: keyof typeof form, value: string) {
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  function changePoster(file: File | null) {
    if (!file) {
      setPosterFile(null);
      return;
    }
    if (!POSTER_TYPES.includes(file.type) || file.size > MAX_POSTER_SIZE) {
      setPosterFile(null);
      setError("채용 포스터는 5MB 이하의 JPG, PNG, WEBP 또는 PDF 파일만 첨부할 수 있습니다.");
      return;
    }
    setError(null);
    setPosterFile(file);
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (departmentError || !selectedDepartmentId || !form.positionTitle.trim() || !form.reason.trim() || !form.responsibilities.trim() || !selectedApproverId) {
      setError("필수 항목을 모두 입력해 주세요.");
      return;
    }
    setSaving(true);
    try {
      const created = await createRecruitmentRequest({
        request_department_id: selectedDepartmentId,
        approver_id: selectedApproverId,
        position_title: form.positionTitle.trim(),
        headcount: Number(form.headcount),
        employment_type: form.employmentType,
        experience_level: form.experienceLevel,
        experience_years_min:
          form.experienceLevel === "EXPERIENCED" ? Number(form.experienceYearsMin) : null,
        education_level: form.educationLevel,
        work_location: form.workLocation.trim() || null,
        salary: form.salary.trim() || null,
        application_deadline: form.applicationDeadline || null,
        apply_method: form.applyMethod,
        reason: form.reason.trim(),
        responsibilities: form.responsibilities.trim(),
        required_skills: form.requiredSkills.trim() || null,
        preferred_skills: form.preferredSkills.trim() || null,
        desired_start_date: form.desiredStartDate || null,
      });
      if (posterFile) {
        await uploadRecruitmentPoster(created.id, posterFile);
      }
      router.push(`/recruitment-requests/${created.id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "채용 요청을 저장하지 못했습니다.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="content approval-page">
      <div className="page-heading"><div><span className="section-kicker">NEW RECRUITMENT REQUEST</span><h1>채용 요청 작성</h1><p>저장한 요청은 상세 화면에서 전자결재로 상신합니다. 근무지·급여·마감일은 결재자가 보고 승인하며, 이후 AI 채용 포스터가 그대로 사용합니다.</p></div></div>
      <form className="panel approval-form" onSubmit={(event) => void save(event)}>
        {(error || departmentError) && <div className="inline-alert error">{error ?? departmentError}</div>}
        <div className="form-grid">
          <label className="form-field"><span>모집 직무 *</span><input value={form.positionTitle} onChange={(event) => change("positionTitle", event.target.value)} /></label>
          <label className="form-field"><span>모집 인원 *</span><input type="number" min="1" value={form.headcount} onChange={(event) => change("headcount", event.target.value)} /></label>
          <label className="form-field"><span>요청 부서 *</span><select value={selectedDepartmentId} disabled={Boolean(departmentError) || !canSelectDepartment} onChange={(event) => setDepartmentId(event.target.value)}>{availableDepartments.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select>{!canSelectDepartment && !departmentError && <small className="file-help">현재 역할은 소속 부서로만 요청할 수 있습니다.</small>}</label>
          <label className="form-field"><span>결재자 *</span><select value={approverId} onChange={(event) => setApproverId(event.target.value)}>{approvers.map((item) => <option value={item.id} key={item.id}>{item.name} · {item.role_label}</option>)}</select></label>
          <label className="form-field"><span>고용 형태 *</span><select value={form.employmentType} onChange={(event) => change("employmentType", event.target.value)}>{EMPLOYMENT_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
          <label className="form-field"><span>학력 *</span><select value={form.educationLevel} onChange={(event) => change("educationLevel", event.target.value)}>{EDUCATION_LEVELS.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
          <fieldset className="form-field full experience-field">
            <legend>경력 조건 *</legend>
            <div className="experience-choices">{EXPERIENCE_CHOICES.map((choice) => (
              <label className="experience-choice" key={choice.value}>
                <input checked={form.experienceLevel === choice.value} name="experienceLevel" onChange={() => change("experienceLevel", choice.value)} type="radio" value={choice.value} />
                {choice.label}
              </label>
            ))}</div>
            {/* 년수는 '경력'일 때만 뜬다. 신입에 년수를 남겨두면 공고 표기와 어긋난다. */}
            {form.experienceLevel === "EXPERIENCED" && (
              <label className="experience-years"><span>최소 경력</span><select value={form.experienceYearsMin} onChange={(event) => change("experienceYearsMin", event.target.value)}>{EXPERIENCE_YEARS.map((year) => <option key={year} value={String(year)}>{year}년 이상</option>)}</select></label>
            )}
          </fieldset>
          <label className="form-field"><span>근무지</span><input placeholder="서울 강남구" value={form.workLocation} onChange={(event) => change("workLocation", event.target.value)} /></label>
          <label className="form-field"><span>급여</span><input placeholder="면접 후 협의" value={form.salary} onChange={(event) => change("salary", event.target.value)} /></label>
          <label className="form-field"><span>모집 마감일</span><input type="date" value={form.applicationDeadline} onChange={(event) => change("applicationDeadline", event.target.value)} /></label>
          <label className="form-field"><span>지원 방법</span><select value={form.applyMethod} onChange={(event) => change("applyMethod", event.target.value)}>{APPLY_METHODS.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
          <label className="form-field full"><span>채용 사유 *</span><textarea rows={4} value={form.reason} onChange={(event) => change("reason", event.target.value)} /></label>
          <label className="form-field full"><span>주요 업무 *</span><textarea rows={4} value={form.responsibilities} onChange={(event) => change("responsibilities", event.target.value)} /></label>
          <label className="form-field"><span>필수 역량</span><textarea rows={3} value={form.requiredSkills} onChange={(event) => change("requiredSkills", event.target.value)} /></label>
          <label className="form-field"><span>우대 사항</span><textarea rows={3} value={form.preferredSkills} onChange={(event) => change("preferredSkills", event.target.value)} /></label>
          <label className="form-field"><span>희망 입사일</span><input type="date" value={form.desiredStartDate} onChange={(event) => change("desiredStartDate", event.target.value)} /></label>
          <label className="form-field"><span>채용 포스터 첨부</span><input type="file" accept="image/jpeg,image/png,image/webp,application/pdf" onChange={(event) => changePoster(event.target.files?.[0] ?? null)} /><small className="file-help">JPG, PNG, WEBP, PDF · 최대 5MB</small>{posterFile && <strong className="selected-file">첨부 예정: {posterFile.name}</strong>}</label>
        </div>
        <div className="form-actions"><button className="primary-button" disabled={saving}>{saving ? "저장 중..." : "임시 저장"}</button></div>
      </form>
    </section>
  );
}
