"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { ApprovalDraftPanel } from "@/features/ai/approval-draft-panel";
import { createApproval, submitApproval } from "@/features/approvals/api";
import { useCurrentUser } from "@/features/current-user/current-user-provider";
import { getDepartments } from "@/features/dashboard/api";
import { isManagerLevelApprover } from "@/lib/approver-policy";
import type { DocumentType } from "@/types/approval";
import type { Department } from "@/types/dashboard";

export function ApprovalForm() {
  const router = useRouter();
  const { currentEmployee, employees } = useCurrentUser();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [title, setTitle] = useState("");
  const [documentType, setDocumentType] = useState<DocumentType>("GENERAL");
  const [content, setContent] = useState("");
  const [departmentId, setDepartmentId] = useState(currentEmployee.department_id);
  const [approverId, setApproverId] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const approvers = useMemo(
    () => employees.filter((employee) => employee.id !== currentEmployee.id && isManagerLevelApprover(employee.position)),
    [currentEmployee.id, employees],
  );
  const effectiveApproverId =
    approverId && approverId !== currentEmployee.id
      ? approverId
      : approvers[0]?.id ?? "";
  const canDraftForAnyDepartment = currentEmployee.role === "SUPER_ADMIN";
  const availableDepartments = canDraftForAnyDepartment
    ? departments
    : departments.filter((department) => department.id === currentEmployee.department_id);

  useEffect(() => {
    let active = true;
    void getDepartments()
      .then((result) => {
        if (active) setDepartments(result);
      })
      .catch(() => {
        if (active) {
          setDepartments([
            {
              id: currentEmployee.department_id,
              code: "",
              name: currentEmployee.department_name,
            },
          ]);
        }
      });
    return () => {
      active = false;
    };
  }, [currentEmployee]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const submitter = (event.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null;
    const submit = submitter?.value === "submit";
    setError(null);
    if (!title.trim() || !content.trim() || !departmentId || !effectiveApproverId) {
      setError("필수 항목을 모두 입력해 주세요.");
      return;
    }
    if (effectiveApproverId === currentEmployee.id) {
      setError("작성자와 결재자는 같을 수 없습니다.");
      return;
    }

    setSaving(true);
    try {
      const created = await createApproval({
        title: title.trim(),
        document_type: documentType,
        content: content.trim(),
        department_id: departmentId,
        approver_id: effectiveApproverId,
      });
      const result = submit
        ? await submitApproval(created.id)
        : created;
      router.push(`/approvals/${result.id}?saved=${submit ? "submitted" : "draft"}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "문서를 저장하지 못했습니다.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="content approval-page">
      <div className="page-heading">
        <div>
          <span className="section-kicker">NEW APPROVAL</span>
          <h1>전자결재 문서 작성</h1>
          <p>필수 항목을 입력한 뒤 임시 저장하거나 결재를 요청합니다.</p>
        </div>
      </div>

      <form className="panel approval-form" onSubmit={(event) => void save(event)}>
        {error && <div className="inline-alert error">{error}</div>}
        <div className="form-grid">
          <label className="form-field full">
            <span>제목 *</span>
            <input
              required
              maxLength={200}
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="문서 제목을 입력하세요"
            />
          </label>
          <label className="form-field">
            <span>문서 종류 *</span>
            <select
              value={documentType}
              onChange={(event) => setDocumentType(event.target.value as DocumentType)}
            >
              <option value="GENERAL">일반 품의</option>
              <option value="RECRUITMENT_REQUEST">채용 요청</option>
              <option value="EXPENSE">비용 품의</option>
              <option value="QUOTATION_DISCOUNT">견적 할인</option>
            </select>
          </label>
          <label className="form-field">
            <span>기안 부서 *</span>
            <select
              required
              value={departmentId}
              disabled={!canDraftForAnyDepartment}
              onChange={(event) => setDepartmentId(event.target.value)}
            >
              {availableDepartments.map((department) => (
                <option value={department.id} key={department.id}>
                  {department.name}
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            <span>기안자</span>
            <input value={`${currentEmployee.name} · ${currentEmployee.role_label}`} disabled />
          </label>
          <label className="form-field">
            <span>결재자 *</span>
            <select
              required
              value={effectiveApproverId}
              onChange={(event) => setApproverId(event.target.value)}
            >
              {approvers.map((employee) => (
                <option value={employee.id} key={employee.id}>
                  {employee.name} · {employee.role_label} · {employee.department_name}
                </option>
              ))}
            </select>
            <small className="file-help">팀장급 이상만 결재자로 지정할 수 있습니다.</small>
          </label>
          <ApprovalDraftPanel
            documentType={documentType}
            onApply={(draft) => {
              // 폼 값을 채울 뿐이다. 저장은 아래 [임시 저장]/[결재 요청]으로만 일어난다.
              setTitle(draft.title);
              setContent(draft.content);
            }}
          />
          <label className="form-field full">
            <span>내용 *</span>
            <textarea
              required
              rows={12}
              value={content}
              onChange={(event) => setContent(event.target.value)}
              placeholder="결재받을 내용을 구체적으로 입력하세요"
            />
          </label>
        </div>
        <div className="form-actions">
          <button
            className="secondary-button"
            type="submit"
            name="intent"
            value="draft"
            disabled={saving}
          >
            {saving ? "저장 중..." : "임시 저장"}
          </button>
          <button
            className="primary-button"
            type="submit"
            name="intent"
            value="submit"
            disabled={saving}
          >
            {saving ? "처리 중..." : "결재 요청"}
          </button>
        </div>
      </form>
    </section>
  );
}
