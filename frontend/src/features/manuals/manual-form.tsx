"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { createManual, getManual, listManualCategories, updateManual } from "@/features/manuals/api";
import type { ManualAssetInput, ManualCategory, ManualInput, ManualRole, ManualStatus } from "@/types/manual";

const roles: { value: ManualRole; label: string }[] = [
  { value: "SUPER_ADMIN", label: "최고 관리자" }, { value: "HR_ADMIN", label: "인사 관리자" }, { value: "TEAM_ADMIN", label: "팀 관리자" }, { value: "EMPLOYEE", label: "직원" },
];
const initialInput: ManualInput = { category_id: "", title: "", summary: "", content: "", target_roles: roles.map((role) => role.value), is_pinned: false, status: "PUBLISHED", assets: [] };

export function ManualForm({ slug }: { slug?: string }) {
  const router = useRouter();
  const [categories, setCategories] = useState<ManualCategory[]>([]);
  const [input, setInput] = useState<ManualInput>(initialInput);
  const [loading, setLoading] = useState(Boolean(slug));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const requests: Promise<unknown>[] = [listManualCategories().then((result) => { if (active) setCategories(result); })];
    if (slug) requests.push(getManual(slug).then((manual) => { if (active) setInput({ category_id: manual.category.id, title: manual.title, summary: manual.summary, content: manual.content, target_roles: manual.target_roles, is_pinned: manual.is_pinned, status: manual.status, assets: manual.assets.map((asset) => ({ asset_type: asset.asset_type, file_url: asset.file_url, thumbnail_url: asset.thumbnail_url, alt_text: asset.alt_text, display_order: asset.display_order })) }); }));
    void Promise.all(requests).catch((reason: unknown) => { if (active) setError(reason instanceof Error ? reason.message : "작성 화면을 준비하지 못했습니다."); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [slug]);

  function updateField<Key extends keyof ManualInput>(field: Key, value: ManualInput[Key]) { setInput((current) => ({ ...current, [field]: value })); }
  function changeRole(role: ManualRole, checked: boolean) { updateField("target_roles", checked ? [...input.target_roles, role] : input.target_roles.filter((value) => value !== role)); }
  function updateAsset(index: number, field: keyof ManualAssetInput, value: string) { updateField("assets", input.assets.map((asset, position) => position === index ? { ...asset, [field]: field === "display_order" ? Number(value) : value } : asset)); }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(null);
    if (!input.category_id || input.target_roles.length === 0) { setError("카테고리와 대상 역할을 선택하세요."); return; }
    setSaving(true);
    try { const saved = slug ? await updateManual(slug, input) : await createManual(input); router.replace(`/manuals/${saved.slug}`); } catch (reason) { setError(reason instanceof Error ? reason.message : "매뉴얼 저장에 실패했습니다."); setSaving(false); }
  }

  if (loading) return <section className="content manual-page"><div className="state-box">작성 화면을 불러오는 중입니다.</div></section>;
  return <section className="content manual-page"><div className="page-heading"><div><span className="section-kicker">MANUAL ADMIN</span><h1>{slug ? "매뉴얼 수정" : "매뉴얼 작성"}</h1><p>텍스트 원본과 한눈에 보는 이미지 요약을 함께 관리합니다.</p></div><Link className="secondary-button" href={slug ? `/manuals/${slug}` : "/manuals"}>취소</Link></div><form className="panel approval-form manual-form" onSubmit={submit}>{error && <div className="inline-alert error">{error}</div>}<div className="form-grid"><label className="form-field"><span>카테고리</span><select value={input.category_id} onChange={(event) => updateField("category_id", event.target.value)} required><option value="">선택하세요</option>{categories.map((category) => <option value={category.id} key={category.id}>{category.name}</option>)}</select></label><label className="form-field"><span>공개 상태</span><select value={input.status} onChange={(event) => updateField("status", event.target.value as ManualStatus)}><option value="PUBLISHED">공개</option><option value="DRAFT">초안</option></select></label><label className="form-field full"><span>제목</span><input value={input.title} maxLength={200} onChange={(event) => updateField("title", event.target.value)} required /></label><label className="form-field full"><span>요약</span><input value={input.summary} maxLength={500} onChange={(event) => updateField("summary", event.target.value)} required /></label><label className="form-field full"><span>본문</span><textarea rows={12} value={input.content} onChange={(event) => updateField("content", event.target.value)} required /></label><fieldset className="form-field full manual-role-field"><legend>대상 역할</legend><div>{roles.map((role) => <label key={role.value}><input type="checkbox" checked={input.target_roles.includes(role.value)} onChange={(event) => changeRole(role.value, event.target.checked)} /> {role.label}</label>)}</div></fieldset><label className="form-field full manual-pin-field"><input type="checkbox" checked={input.is_pinned} onChange={(event) => updateField("is_pinned", event.target.checked)} /> 중요 매뉴얼로 상단 고정</label></div><section className="manual-asset-editor"><div><h2>요약 이미지 · 파일 URL</h2><p>이미지는 여러 장 등록할 수 있습니다. 이번 MVP는 URL 등록 방식이며 대용량 파일 업로드는 지원하지 않습니다.</p></div>{input.assets.map((asset, index) => <div className="manual-asset-row" key={index}><select value={asset.asset_type} onChange={(event) => updateAsset(index, "asset_type", event.target.value)}><option value="IMAGE">이미지</option><option value="PDF">PDF</option></select><input placeholder="이미지 또는 PDF URL" value={asset.file_url} onChange={(event) => updateAsset(index, "file_url", event.target.value)} required /><input placeholder="대체 텍스트" value={asset.alt_text || ""} onChange={(event) => updateAsset(index, "alt_text", event.target.value)} /><button className="text-button" type="button" onClick={() => updateField("assets", input.assets.filter((_, position) => position !== index))}>삭제</button></div>)}<button className="secondary-button" type="button" onClick={() => updateField("assets", [...input.assets, { asset_type: "IMAGE", file_url: "", alt_text: "", display_order: input.assets.length }])}>이미지·파일 URL 추가</button></section><div className="form-actions"><button className="primary-button" disabled={saving}>{saving ? "저장 중..." : slug ? "수정 저장" : "매뉴얼 저장"}</button></div></form></section>;
}
