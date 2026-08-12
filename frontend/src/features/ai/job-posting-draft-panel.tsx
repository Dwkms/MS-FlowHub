"use client";

import { useState } from "react";

import { createJobPostingDraft, recordFinalOutput } from "@/features/ai/api";
import { updateJobPosting } from "@/features/recruitment/api";
import type { JobPostingDraftOutput } from "@/types/ai";
import type { JobPosting } from "@/types/recruitment";

type Props = {
  posting: JobPosting;
  onApplied: (updated: JobPosting) => void;
};

const EMPTY_INPUT = {
  workLocation: "",
  applicationDeadline: "",
  applyMethod: "",
  teamIntro: "",
  salary: "",
};

const bullets = (items: string[]) => items.map((item) => `- ${item}`).join("\n");
const toLines = (value: string) =>
  value
    .split("\n")
    .map((line) => line.replace(/^[-•\s]+/, "").trim())
    .filter(Boolean);

/** 구조화된 문장을 공고 본문 한 덩어리로 합친다. `JobPosting.content`가 Text 하나라
 *  결국 합쳐야 하고, 조립을 여기서 해야 사용자가 항목 단위로 고칠 수 있다. */
export function assemblePostingContent(draft: JobPostingDraftOutput): string {
  const sections: string[] = [];
  if (draft.introduction) sections.push(draft.introduction);
  if (draft.responsibilities.length) sections.push(`주요 업무\n${bullets(draft.responsibilities)}`);
  if (draft.requirements.length) sections.push(`필수 역량\n${bullets(draft.requirements)}`);
  if (draft.preferred_qualifications.length) {
    sections.push(`우대 사항\n${bullets(draft.preferred_qualifications)}`);
  }
  if (draft.team_or_recruitment_description) {
    sections.push(`팀 소개\n${draft.team_or_recruitment_description}`);
  }
  if (draft.closing_message) sections.push(draft.closing_message);
  return sections.join("\n\n");
}

export function JobPostingDraftPanel({ posting, onApplied }: Props) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState(EMPTY_INPUT);
  const [draft, setDraft] = useState<JobPostingDraftOutput | null>(null);
  const [generationId, setGenerationId] = useState<string | null>(null);
  const [isSample, setIsSample] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function update(field: keyof typeof EMPTY_INPUT, value: string) {
    setInput((previous) => ({ ...previous, [field]: value }));
  }

  function editDraft<K extends keyof JobPostingDraftOutput>(
    field: K,
    value: JobPostingDraftOutput[K],
  ) {
    setDraft((previous) => (previous ? { ...previous, [field]: value } : previous));
  }

  /** 선택 항목이지만 값을 넣었다면 최소 길이를 요구한다. 여기 적은 값은 공고에 그대로
   *  실리므로, "ㅇㅇ" 같은 입력은 공고를 오염시키거나 AI가 조용히 버린다. */
  function tooShort(): string | null {
    const rules: [string, string, number][] = [
      [input.workLocation, "근무 위치", 2],
      [input.applicationDeadline, "지원 마감일", 4],
      [input.applyMethod, "지원 방법", 5],
      [input.salary, "급여·처우", 2],
      [input.teamIntro, "팀 소개", 10],
    ];
    for (const [value, label, min] of rules) {
      const text = value.trim();
      if (text.length > 0 && text.length < min) {
        return `${label}은(는) 비워두거나 ${min}자 이상 입력해 주세요.`;
      }
    }
    return null;
  }

  async function generate() {
    setError(null);
    const invalid = tooShort();
    if (invalid) {
      setError(invalid);
      return;
    }
    setBusy(true);
    try {
      const response = await createJobPostingDraft({
        job_posting_id: posting.id,
        work_location: input.workLocation.trim() || undefined,
        application_deadline: input.applicationDeadline.trim() || undefined,
        apply_method: input.applyMethod.trim() || undefined,
        team_intro: input.teamIntro.trim() || undefined,
        salary: input.salary.trim() || undefined,
      });

      if (!response.success || !response.output) {
        setDraft(null);
        setError(response.error_message ?? "초안을 생성하지 못했습니다.");
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
    setError(null);
    setBusy(true);
    try {
      // 게시 상태는 바꾸지 않는다. 서버가 status를 받지 않는다.
      const updated = await updateJobPosting(posting.id, {
        title: draft.headline,
        content: assemblePostingContent(draft),
      });
      onApplied(updated);
      setOpen(false);
      setDraft(null);

      if (generationId) {
        try {
          await recordFinalOutput(generationId, draft);
        } catch {
          // 기록은 품질 분석용이다. 실패해도 공고 반영은 이미 끝났다.
        }
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "공고에 반영하지 못했습니다.");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <div className="ai-draft">
        <button type="button" className="secondary-button" onClick={() => setOpen(true)}>
          AI 공고 초안 생성
        </button>
        <small className="file-help">
          채용 요청의 직무·인원·업무·역량을 그대로 사용합니다. 확인·수정 후 직접 적용해야 반영됩니다.
        </small>
      </div>
    );
  }

  return (
    <section className="ai-draft ai-draft-open">
      <header className="ai-draft-header">
        <strong>AI 공고 초안 생성</strong>
        <button type="button" className="ai-draft-close" onClick={() => setOpen(false)}>
          닫기
        </button>
      </header>

      <div className="ai-draft-body">
        {error && <div className="inline-alert error">{error}</div>}

        {/* posting.title은 AI 초안을 적용하면 헤드라인으로 바뀐다. 여기서 "직무"로
            표시하면 적용 이후 문구가 어긋나므로 제목을 쓰지 않는다. */}
        <p className="file-help">
          모집 {posting.headcount}명 · {posting.employment_type} · {posting.experience_level} 등
          직무·인원·주요 업무·역량은 채용 요청에서 자동으로 가져옵니다. 아래는 DB에 없어 직접
          입력해야 하는 항목이며, 비워두면 공고에 나오지 않습니다.
        </p>

        <div className="form-grid">
          <label className="form-field">
            <span>근무 위치</span>
            <input
              value={input.workLocation}
              maxLength={200}
              onChange={(event) => update("workLocation", event.target.value)}
              placeholder="예: 서울 본사"
            />
          </label>
          <label className="form-field">
            <span>지원 마감일</span>
            <input
              value={input.applicationDeadline}
              maxLength={100}
              onChange={(event) => update("applicationDeadline", event.target.value)}
              placeholder="예: 2026-09-30"
            />
          </label>
          <label className="form-field full">
            <span>지원 방법</span>
            <input
              value={input.applyMethod}
              maxLength={500}
              onChange={(event) => update("applyMethod", event.target.value)}
              placeholder="예: 채용 담당자 이메일로 이력서 송부"
            />
          </label>
          <label className="form-field">
            <span>급여·처우</span>
            <input
              value={input.salary}
              maxLength={200}
              onChange={(event) => update("salary", event.target.value)}
              placeholder="입력하지 않으면 공고에 나오지 않습니다"
            />
          </label>
          <label className="form-field full">
            <span>팀 소개</span>
            <textarea
              rows={2}
              value={input.teamIntro}
              maxLength={1000}
              onChange={(event) => update("teamIntro", event.target.value)}
            />
          </label>
        </div>

        <div className="ai-draft-actions">
          {busy && (
            <span className="ai-draft-wait">
              AI가 초안을 작성하고 있습니다. 보통 5~10초 걸립니다.
            </span>
          )}
          <button
            type="button"
            className="primary-button"
            onClick={() => void generate()}
            disabled={busy}
          >
            {busy ? "처리 중..." : draft ? "다시 생성" : "생성"}
          </button>
        </div>

        {draft && (
          <div className="ai-preview">
            <div className="ai-preview-head">
              <strong>미리보기</strong>
              {isSample && <span className="ai-badge">샘플 응답</span>}
            </div>
            <p className="file-help">항목은 한 줄에 하나씩 입력합니다. 적용하면 공고 본문이 바뀝니다.</p>

            <label className="form-field full">
              <span>공고 제목</span>
              <input
                value={draft.headline}
                maxLength={200}
                onChange={(event) => editDraft("headline", event.target.value)}
              />
            </label>
            <label className="form-field full">
              <span>소개</span>
              <textarea
                rows={3}
                value={draft.introduction}
                onChange={(event) => editDraft("introduction", event.target.value)}
              />
            </label>
            <label className="form-field full">
              <span>주요 업무</span>
              <textarea
                rows={4}
                value={draft.responsibilities.join("\n")}
                onChange={(event) => editDraft("responsibilities", toLines(event.target.value))}
              />
            </label>
            <label className="form-field full">
              <span>필수 역량</span>
              <textarea
                rows={4}
                value={draft.requirements.join("\n")}
                onChange={(event) => editDraft("requirements", toLines(event.target.value))}
              />
            </label>
            <label className="form-field full">
              <span>우대 사항</span>
              <textarea
                rows={3}
                value={draft.preferred_qualifications.join("\n")}
                onChange={(event) =>
                  editDraft("preferred_qualifications", toLines(event.target.value))
                }
              />
            </label>
            <label className="form-field full">
              <span>팀 소개</span>
              <textarea
                rows={2}
                value={draft.team_or_recruitment_description}
                onChange={(event) =>
                  editDraft("team_or_recruitment_description", event.target.value)
                }
              />
            </label>
            <label className="form-field full">
              <span>마무리 안내</span>
              <textarea
                rows={2}
                value={draft.closing_message}
                onChange={(event) => editDraft("closing_message", event.target.value)}
              />
            </label>

            <div className="ai-draft-actions">
              <button
                type="button"
                className="primary-button"
                onClick={() => void apply()}
                disabled={busy}
              >
                공고 내용에 적용
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
