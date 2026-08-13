"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

import { createJobPoster } from "@/features/ai/api";
import { ApiError } from "@/lib/api-client";
import type { JobPosterGenerateResponse } from "@/types/ai";
import type { JobPosting } from "@/types/recruitment";

interface Props {
  posting: JobPosting;
  isLimitExempt: boolean;
}

interface PosterCandidate {
  id: string;
  result: JobPosterGenerateResponse;
  designDirection: string | null;
}

function displayDate(value: string | null): string {
  return value ? value.replaceAll("-", ". ") : "미정";
}

function downloadPoster(
  posting: JobPosting,
  candidate: PosterCandidate,
  candidateNumber: number,
): void {
  const { result } = candidate;
  if (!result.image_base64 || !result.content_type) return;

  const bytes = Uint8Array.from(atob(result.image_base64), (character) =>
    character.charCodeAt(0),
  );
  const url = URL.createObjectURL(new Blob([bytes], { type: result.content_type }));
  const link = document.createElement("a");
  const safeTitle = posting.title.replace(/[^0-9A-Za-z가-힣_-]+/g, "-");
  link.href = url;
  link.download = `${safeTitle || "채용공고"}-AI-포스터-시안-${candidateNumber}.png`;
  link.click();
  URL.revokeObjectURL(url);
}

export function JobPosterPanel({ posting, isLimitExempt }: Props) {
  const [open, setOpen] = useState(false);
  const [designDirection, setDesignDirection] = useState("");
  const [generating, setGenerating] = useState(false);
  const [candidates, setCandidates] = useState<PosterCandidate[]>([]);
  const [activeCandidateIndex, setActiveCandidateIndex] = useState(0);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [zoomedCandidateId, setZoomedCandidateId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!zoomedCandidateId) return;

    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setZoomedCandidateId(null);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [zoomedCandidateId]);

  async function generate(): Promise<void> {
    const direction = designDirection.trim();
    if (direction.length > 0 && direction.length < 4) {
      setError("디자인 요청은 4자 이상 입력하거나 비워 주세요.");
      return;
    }

    setGenerating(true);
    setError(null);
    try {
      const response = await createJobPoster({
        job_posting_id: posting.id,
        ...(direction ? { design_direction: direction } : {}),
      });
      if (!response.success || !response.image_base64 || !response.content_type) {
        setError(response.error_message || "포스터 이미지를 생성하지 못했습니다.");
        return;
      }
      const candidate: PosterCandidate = {
        id: response.generation_id,
        result: response,
        designDirection: direction || null,
      };
      setCandidates((current) => [...current, candidate]);
      setActiveCandidateIndex(candidates.length);
      setSelectedCandidateId((current) => current ?? candidate.id);
    } catch (reason) {
      setError(
        reason instanceof ApiError && reason.status && reason.status >= 500
          ? "이미지 응답 연결이 중단되었습니다. 서버에서는 생성됐을 수 있으므로 연속으로 다시 누르지 말고 잠시 후 관리자에게 생성 기록을 확인해 주세요."
          : reason instanceof Error
            ? reason.message
            : "포스터 이미지 생성 중 오류가 발생했습니다.",
      );
    } finally {
      setGenerating(false);
    }
  }

  if (!open) {
    return (
      <div className="ai-draft">
        <button className="secondary-button" type="button" onClick={() => setOpen(true)}>
          AI 채용 포스터 생성
        </button>
        <p className="file-help">승인된 공고 내용으로 검토용 포스터 이미지를 만듭니다.</p>
      </div>
    );
  }

  const selectedCandidateIndex = Math.max(
    0,
    candidates.findIndex((candidate) => candidate.id === selectedCandidateId),
  );
  const selectedCandidate = candidates[selectedCandidateIndex] ?? null;
  const zoomedCandidateIndex = candidates.findIndex(
    (candidate) => candidate.id === zoomedCandidateId,
  );
  const zoomedCandidate = candidates[zoomedCandidateIndex] ?? null;
  const zoomedImageSource = zoomedCandidate?.result.image_base64
    && zoomedCandidate.result.content_type
    ? `data:${zoomedCandidate.result.content_type};base64,${zoomedCandidate.result.image_base64}`
    : null;

  return (
    <section className="ai-draft ai-draft-open ai-poster-panel">
      <header className="ai-draft-header">
        <strong>AI 채용 포스터 이미지 생성</strong>
        <button
          type="button"
          className="ai-draft-close"
          disabled={generating}
          onClick={() => setOpen(false)}
        >
          닫기
        </button>
      </header>

      <div className="ai-draft-body">
        <p className="ai-poster-description">
          승인된 채용정보를 그대로 사용합니다. 아래 디자인 요청만 선택적으로 추가할 수
          있으며, 생성 결과는 공고에 자동 저장되지 않습니다.
        </p>

        <div className="ai-source-grid">
          <div className="ai-source-field"><span>모집 직무</span><strong>{posting.title}</strong></div>
          <div className="ai-source-field"><span>모집 인원</span><strong>{posting.headcount}명</strong></div>
          <div className="ai-source-field"><span>고용 형태</span><strong>{posting.employment_type}</strong></div>
          <div className="ai-source-field"><span>경력</span><strong>{posting.experience_label}</strong></div>
          {posting.work_location && <div className="ai-source-field"><span>근무지</span><strong>{posting.work_location}</strong></div>}
          {posting.salary && <div className="ai-source-field"><span>급여</span><strong>{posting.salary}</strong></div>}
          <div className="ai-source-field"><span>모집 마감</span><strong>{displayDate(posting.application_deadline)}</strong></div>
          {posting.apply_method && <div className="ai-source-field"><span>지원 방법</span><strong>{posting.apply_method}</strong></div>}
          <div className="ai-source-field full"><span>주요 업무</span><p>{posting.responsibilities}</p></div>
          {posting.required_skills && <div className="ai-source-field full"><span>필수 역량</span><p>{posting.required_skills}</p></div>}
          {posting.preferred_skills && <div className="ai-source-field full"><span>우대 사항</span><p>{posting.preferred_skills}</p></div>}
        </div>

        <label className="form-field full">
          <span>디자인 요청 (선택)</span>
          <textarea
            maxLength={500}
            value={designDirection}
            placeholder="예: 차분한 네이비 톤, 개발자 채용에 어울리는 현대적인 분위기"
            onChange={(event) => setDesignDirection(event.target.value)}
          />
        </label>

        <p className="ai-poster-cost-note">
          {isLimitExempt
            ? "생성 버튼을 누를 때 OpenAI 이미지 API를 1회 호출합니다."
            : "생성 버튼을 누를 때 OpenAI 이미지 API를 1회 호출합니다. 최근 24시간 기준 사용자당 2회, 전체 5회로 제한됩니다."}
        </p>
        {error && <div className="state-box error">{error}</div>}

        <div className="ai-draft-actions">
          {generating && <span className="ai-draft-wait">이미지 생성은 최대 2분 정도 걸릴 수 있습니다.</span>}
          <button className="primary-button" type="button" disabled={generating} onClick={() => void generate()}>
            {generating ? "생성 중..." : candidates.length > 0 ? "시안 추가 생성" : "포스터 생성"}
          </button>
        </div>

        {candidates.length > 0 && selectedCandidate && (
          <div className="ai-poster-preview">
            <div className="ai-poster-preview-heading">
              <div>
                <strong>생성 시안 비교</strong>
                <span>마음에 드는 시안을 선택하세요. 선택 상태는 현재 화면에서만 유지됩니다.</span>
              </div>
              <button
                className="secondary-button"
                type="button"
                onClick={() => downloadPoster(posting, selectedCandidate, selectedCandidateIndex + 1)}
              >
                선택 시안 PNG 다운로드
              </button>
            </div>

            <div className="ai-poster-mobile-navigation" aria-label="포스터 시안 이동">
              <button
                type="button"
                disabled={activeCandidateIndex === 0}
                onClick={() => setActiveCandidateIndex((index) => Math.max(0, index - 1))}
              >
                이전
              </button>
              <strong>{activeCandidateIndex + 1} / {candidates.length}</strong>
              <button
                type="button"
                disabled={activeCandidateIndex === candidates.length - 1}
                onClick={() => setActiveCandidateIndex((index) => Math.min(candidates.length - 1, index + 1))}
              >
                다음
              </button>
            </div>

            <div className="ai-poster-candidate-grid">
              {candidates.map((candidate, index) => {
                const imageSource = candidate.result.image_base64 && candidate.result.content_type
                  ? `data:${candidate.result.content_type};base64,${candidate.result.image_base64}`
                  : null;
                const selected = candidate.id === selectedCandidateId;
                const active = index === activeCandidateIndex;
                if (!imageSource) return null;

                return (
                  <article
                    className={`ai-poster-candidate${selected ? " is-selected" : ""}${active ? " is-active" : ""}`}
                    key={candidate.id}
                  >
                    <div className="ai-poster-candidate-heading">
                      <div>
                        <strong>시안 {index + 1}</strong>
                        <span>{candidate.designDirection || "기본 디자인"}</span>
                      </div>
                      {selected && <em>선택됨</em>}
                    </div>
                    <button
                      className="ai-poster-image-button"
                      type="button"
                      aria-label={`시안 ${index + 1} 크게 보기`}
                      onClick={() => setZoomedCandidateId(candidate.id)}
                    >
                      <Image
                        src={imageSource}
                        alt={`${posting.title} AI 채용 포스터 시안 ${index + 1}`}
                        width={1024}
                        height={1536}
                        unoptimized
                      />
                      <span>클릭해서 확대</span>
                    </button>
                    <button
                      className={selected ? "primary-button" : "secondary-button"}
                      type="button"
                      aria-pressed={selected}
                      onClick={() => {
                        setSelectedCandidateId(candidate.id);
                        setActiveCandidateIndex(index);
                      }}
                    >
                      {selected ? "선택한 시안" : "이 시안 선택"}
                    </button>
                  </article>
                );
              })}
            </div>
            <p className="file-help">내용과 한글 표기를 확인한 뒤 사용하세요. 공고 첨부에는 자동 반영되지 않습니다.</p>
          </div>
        )}
      </div>

      {zoomedCandidate && zoomedImageSource && (
        <div
          className="image-preview-backdrop"
          role="presentation"
          onClick={() => setZoomedCandidateId(null)}
        >
          <section
            className="image-preview-dialog ai-poster-zoom-dialog"
            role="dialog"
            aria-modal="true"
            aria-label={`포스터 시안 ${zoomedCandidateIndex + 1} 크게 보기`}
            onClick={(event) => event.stopPropagation()}
          >
            <div className="image-preview-heading">
              <div>
                <strong>시안 {zoomedCandidateIndex + 1}</strong>
                <span>{zoomedCandidate.designDirection || "기본 디자인"}</span>
              </div>
              <button
                type="button"
                className="secondary-button"
                onClick={() => setZoomedCandidateId(null)}
              >
                닫기
              </button>
            </div>
            <Image
              src={zoomedImageSource}
              alt={`${posting.title} AI 채용 포스터 시안 ${zoomedCandidateIndex + 1} 확대 이미지`}
              width={1024}
              height={1536}
              unoptimized
            />
          </section>
        </div>
      )}
    </section>
  );
}
