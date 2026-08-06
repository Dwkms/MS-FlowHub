"use client";
/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { deleteManual, getManual } from "@/features/manuals/api";
import { formatManualDate, manualRoleLabels } from "@/features/manuals/presentation";
import { useCurrentUser } from "@/features/current-user/current-user-provider";
import type { ManualAsset, ManualDetail as ManualDetailType } from "@/types/manual";

const manageableRoles = ["SUPER_ADMIN", "HR_ADMIN"];

export function ManualDetail({ slug }: { slug: string }) {
  const router = useRouter();
  const { currentEmployee } = useCurrentUser();
  const [manual, setManual] = useState<ManualDetailType | null>(null);
  const [selectedImage, setSelectedImage] = useState<ManualAsset | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const canManage = manageableRoles.includes(currentEmployee.role);

  useEffect(() => {
    let active = true;
    void getManual(slug).then((result) => { if (active) setManual(result); }).catch((reason: unknown) => {
      if (active) setError(reason instanceof Error ? reason.message : "매뉴얼을 불러오지 못했습니다.");
    });
    return () => { active = false; };
  }, [slug]);

  async function removeManual() {
    if (!window.confirm("이 매뉴얼을 삭제할까요?")) return;
    setDeleting(true);
    try { await deleteManual(slug); router.replace("/manuals"); } catch (reason) {
      setError(reason instanceof Error ? reason.message : "매뉴얼 삭제에 실패했습니다.");
      setDeleting(false);
    }
  }

  if (error) return <section className="content manual-page"><div className="state-box error">{error}</div></section>;
  if (!manual) return <section className="content manual-page"><div className="state-box">매뉴얼을 불러오는 중입니다.</div></section>;
  const images = manual.assets.filter((asset) => asset.asset_type === "IMAGE");
  const files = manual.assets.filter((asset) => asset.asset_type === "PDF");
  return <section className="content manual-page">
    <div className="page-heading detail-heading"><div><span className="section-kicker">{manual.category.name}</span><h1>{manual.title}</h1><p>{manual.summary}</p></div><div className="heading-actions"><Link className="secondary-button" href="/manuals">목록으로</Link>{canManage && <Link className="secondary-button" href={`/manuals/${manual.slug}/edit`}>수정</Link>}{canManage && <button className="danger-button" disabled={deleting} onClick={() => void removeManual()}>{deleting ? "삭제 중..." : "삭제"}</button>}</div></div>
    <div className="manual-detail-grid"><article className="panel manual-document"><dl className="manual-meta"><div><dt>카테고리</dt><dd>{manual.category.name}</dd></div><div><dt>대상 역할</dt><dd>{manual.target_roles.map((role) => manualRoleLabels[role]).join(" · ")}</dd></div><div><dt>최근 수정일</dt><dd>{formatManualDate(manual.updated_at)}</dd></div></dl><div className="manual-content"><h2>사용 방법</h2><p>{manual.content}</p></div>{files.length > 0 && <div className="manual-files"><h2>첨부 파일</h2>{files.map((asset) => <a href={asset.file_url} target="_blank" rel="noreferrer" key={asset.id}>PDF 열기: {asset.alt_text || "첨부 문서"}</a>)}</div>}</article>
      <aside className="panel manual-summary-panel"><span className="section-kicker">QUICK VIEW</span><h2>한눈에 보기</h2>{images.length === 0 && <p>등록된 요약 이미지가 없습니다.</p>}{images.map((asset) => <button className="manual-summary-image" onClick={() => setSelectedImage(asset)} key={asset.id}><img src={asset.thumbnail_url || asset.file_url} alt={asset.alt_text || `${manual.title} 요약 이미지`} /><span>확대 보기</span></button>)}</aside></div>
    {selectedImage && <div className="image-preview-backdrop" role="dialog" aria-modal="true" aria-label="매뉴얼 이미지 확대"><div className="image-preview-dialog"><div className="image-preview-heading"><strong>{selectedImage.alt_text || "매뉴얼 요약 이미지"}</strong><button className="modal-close" onClick={() => setSelectedImage(null)} aria-label="닫기">×</button></div><img src={selectedImage.file_url} alt={selectedImage.alt_text || "매뉴얼 요약 이미지"} /></div></div>}
  </section>;
}
