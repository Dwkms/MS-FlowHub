"use client";

import { useState } from "react";

import { createApprovalDraft, recordFinalOutput } from "@/features/ai/api";
import type { ApprovalDraftOutput } from "@/types/ai";
import type { DocumentType } from "@/types/approval";

type AppliedDraft = { title: string; content: string };

type Props = {
  documentType: DocumentType;
  onApply: (draft: AppliedDraft) => void;
};

const EMPTY_INPUT = {
  purpose: "",
  mainContent: "",
  amount: "",
  quantity: "",
  desiredDate: "",
  extraNote: "",
};

/**
 * 구조화된 초안을 본문 한 덩어리로 합친다.
 *
 * `ApprovalDocument.content`가 Text 하나라 결국 합쳐야 한다. 조립을 백엔드가 아니라
 * 여기서 하는 이유는, 사용자가 미리보기에서 `purpose`만 고치고 `details`는 그대로 두는
 * 식의 필드 단위 수정을 해야 하기 때문이다. 백엔드가 미리 합치면 그 단위가 사라진다.
 */
export function assembleContent(draft: ApprovalDraftOutput): string {
  return [
    `요청 목적\n${draft.purpose}`,
    `주요 내용\n${draft.details}`,
    `기대 효과\n${draft.expected_effect}`,
  ].join("\n\n");
}

export function ApprovalDraftPanel({ documentType, onApply }: Props) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState(EMPTY_INPUT);
  const [draft, setDraft] = useState<ApprovalDraftOutput | null>(null);
  const [generationId, setGenerationId] = useState<string | null>(null);
  const [isSample, setIsSample] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function update(field: keyof typeof EMPTY_INPUT, value: string) {
    setInput((previous) => ({ ...previous, [field]: value }));
  }

  function editDraft(field: keyof ApprovalDraftOutput, value: string) {
    setDraft((previous) => (previous ? { ...previous, [field]: value } : previous));
  }

  async function generate() {
    setError(null);
    // 너무 짧은 입력은 AI가 쓸 근거가 없어 결국 실패한다. 그때는 이미 호출 비용이
    // 나간 뒤이므로, 서버에 보내기 전에 여기서 막는다.
    if (input.purpose.trim().length < 4) {
      setError("요청 목적을 4자 이상 구체적으로 입력해 주세요.");
      return;
    }
    if (input.mainContent.trim().length < 10) {
      setError("주요 내용을 10자 이상 입력해 주세요. AI는 여기 적힌 사실만 문장으로 옮깁니다.");
      return;
    }

    setBusy(true);
    try {
      const response = await createApprovalDraft({
        document_type: documentType,
        purpose: input.purpose.trim(),
        main_content: input.mainContent.trim(),
        amount: input.amount.trim() || undefined,
        quantity: input.quantity.trim() || undefined,
        desired_date: input.desiredDate.trim() || undefined,
        extra_note: input.extraNote.trim() || undefined,
      });

      if (!response.success || !response.output) {
        setDraft(null);
        setError(response.error_message ?? "초안을 생성하지 못했습니다. 직접 작성할 수 있습니다.");
        return;
      }

      setDraft(response.output);
      setGenerationId(response.generation_id);
      setIsSample(response.is_sample);
    } catch (reason) {
      setDraft(null);
      setError(reason instanceof Error ? reason.message : "초안을 생성하지 못했습니다.");
    } finally {
      setBusy(false);
    }
  }

  async function apply() {
    if (!draft) return;

    // 폼에 값을 넣을 뿐 저장하지 않는다. 저장은 사용자가 [임시 저장] 또는 [결재 요청]을
    // 눌렀을 때 기존 경로로만 일어난다.
    onApply({ title: draft.title, content: assembleContent(draft) });
    setOpen(false);

    if (!generationId) return;
    try {
      await recordFinalOutput(generationId, draft);
    } catch {
      // 최종본 기록은 품질 분석용이다. 실패해도 이미 폼에 반영됐으므로 사용자를 막지 않는다.
    }
  }

  if (!open) {
    return (
      <div className="ai-draft full">
        <button type="button" className="secondary-button" onClick={() => setOpen(true)}>
          AI 초안 생성
        </button>
        <small className="file-help">
          입력한 사실을 바탕으로 제목과 내용을 작성합니다. 확인·수정 후 직접 적용해야 반영됩니다.
        </small>
      </div>
    );
  }

  return (
    <section className="ai-draft ai-draft-open full">
      <header className="ai-draft-header">
        <strong>AI 초안 생성</strong>
        <button type="button" className="ai-draft-close" onClick={() => setOpen(false)}>
          닫기
        </button>
      </header>

      <div className="ai-draft-body">
        {error && <div className="inline-alert error">{error}</div>}

        <div className="form-grid">
          <label className="form-field full">
            <span>요청 목적 *</span>
            <input
              value={input.purpose}
              maxLength={500}
              onChange={(event) => update("purpose", event.target.value)}
              placeholder="예: 개발용 노트북 교체"
            />
          </label>
          <label className="form-field full">
            <span>주요 내용 *</span>
            <textarea
              rows={4}
              value={input.mainContent}
              maxLength={2000}
              onChange={(event) => update("mainContent", event.target.value)}
              placeholder="사실 위주로 적어 주세요. 여기 없는 내용은 AI가 만들지 않습니다."
            />
          </label>
          <label className="form-field">
            <span>금액</span>
            <input
              value={input.amount}
              maxLength={100}
              onChange={(event) => update("amount", event.target.value)}
              placeholder="예: 6,000,000원"
            />
          </label>
          <label className="form-field">
            <span>수량</span>
            <input
              value={input.quantity}
              maxLength={100}
              onChange={(event) => update("quantity", event.target.value)}
              placeholder="예: 3대"
            />
          </label>
          <label className="form-field">
            <span>희망 시점</span>
            <input
              value={input.desiredDate}
              maxLength={100}
              onChange={(event) => update("desiredDate", event.target.value)}
              placeholder="예: 2026년 9월 중"
            />
          </label>
          <label className="form-field full">
            <span>추가 설명</span>
            <textarea
              rows={2}
              value={input.extraNote}
              maxLength={1000}
              onChange={(event) => update("extraNote", event.target.value)}
            />
          </label>
        </div>

        <div className="ai-draft-actions">
          {/* 대기 시간을 미리 알려주면 같은 6초도 짧게 느껴진다. 응답을 빠르게 만드는
              것보다 이쪽이 비용 0에 효과가 크다. */}
          {busy && (
            <span className="ai-draft-wait">
              AI가 초안을 작성하고 있습니다. 보통 5~10초 걸립니다.
            </span>
          )}
          <button type="button" className="primary-button" onClick={() => void generate()} disabled={busy}>
            {busy ? "생성 중..." : draft ? "다시 생성" : "생성"}
          </button>
        </div>

        {draft && (
          <div className="ai-preview">
            <div className="ai-preview-head">
              <strong>미리보기</strong>
              {isSample && <span className="ai-badge">샘플 응답</span>}
            </div>
            <p className="file-help">
              내용을 확인하고 필요하면 직접 고친 뒤 적용하세요. 적용해도 저장되지 않습니다.
            </p>

            <label className="form-field full">
              <span>제목</span>
              <input
                value={draft.title}
                maxLength={200}
                onChange={(event) => editDraft("title", event.target.value)}
              />
            </label>
            <label className="form-field full">
              <span>요청 목적</span>
              <textarea
                rows={2}
                value={draft.purpose}
                onChange={(event) => editDraft("purpose", event.target.value)}
              />
            </label>
            <label className="form-field full">
              <span>주요 내용</span>
              <textarea
                rows={6}
                value={draft.details}
                onChange={(event) => editDraft("details", event.target.value)}
              />
            </label>
            <label className="form-field full">
              <span>기대 효과</span>
              <textarea
                rows={2}
                value={draft.expected_effect}
                onChange={(event) => editDraft("expected_effect", event.target.value)}
              />
            </label>

            <div className="ai-draft-actions">
              <button type="button" className="primary-button" onClick={() => void apply()}>
                전자결재에 적용
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
