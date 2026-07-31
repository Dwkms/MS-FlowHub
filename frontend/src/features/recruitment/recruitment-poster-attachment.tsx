"use client";

import Image from "next/image";
import { useState } from "react";

import { getRecruitmentPosterUrl } from "@/features/recruitment/api";

interface RecruitmentPosterAttachmentProps {
  requestId: string;
  employeeId: string;
  originalName: string | null;
  contentType: string | null;
}

export function RecruitmentPosterAttachment({
  requestId,
  employeeId,
  originalName,
  contentType,
}: RecruitmentPosterAttachmentProps) {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  if (!originalName) return null;

  const attachmentUrl = getRecruitmentPosterUrl(requestId, employeeId);
  const isImage = contentType?.startsWith("image/") ?? false;
  const fileKind = isImage ? "이미지 파일" : "문서 파일";

  return (
    <section className="poster-attachment">
      <div>
        <span>첨부 파일 · {fileKind}</span>
        <strong>{originalName}</strong>
        <div className="attachment-actions">
          {isImage && <button type="button" className="text-button" onClick={() => setIsPreviewOpen(true)}>확대 보기</button>}
          <a href={attachmentUrl} download={originalName}>다운로드</a>
        </div>
      </div>
      {isImage && (
        <button type="button" className="poster-preview" onClick={() => setIsPreviewOpen(true)} aria-label={`${originalName} 확대 보기`}>
          <Image src={attachmentUrl} alt={`${originalName} 미리보기`} width={360} height={200} unoptimized />
        </button>
      )}
      {isImage && isPreviewOpen && (
        <div className="image-preview-backdrop" role="presentation" onClick={() => setIsPreviewOpen(false)}>
          <section className="image-preview-dialog" role="dialog" aria-modal="true" aria-label={`${originalName} 확대 보기`} onClick={(event) => event.stopPropagation()}>
            <div className="image-preview-heading"><strong>{originalName}</strong><button type="button" className="secondary-button" onClick={() => setIsPreviewOpen(false)}>닫기</button></div>
            <Image src={attachmentUrl} alt={`${originalName} 확대 미리보기`} width={1400} height={1000} unoptimized />
          </section>
        </div>
      )}
    </section>
  );
}
