"use client";
/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { useEffect, useState } from "react";

import { getManual } from "@/features/manuals/api";
import type { ManualDetail } from "@/types/manual";

export function ManualDetailView({ slug }: { slug: string }) {
  const [manual, setManual] = useState<ManualDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void getManual(slug)
      .then((detail) => {
        if (active) setManual(detail);
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "매뉴얼을 불러오지 못했습니다.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [slug]);

  if (loading) return <section className="content"><div className="state-box">매뉴얼을 불러오는 중입니다.</div></section>;
  if (error || !manual) {
    return (
      <section className="content">
        <div className="state-box error">
          <strong>매뉴얼을 열 수 없습니다.</strong>
          <p>{error ?? "요청한 매뉴얼을 찾지 못했습니다."}</p>
          <Link className="secondary-button" href="/manuals">매뉴얼 목록으로</Link>
        </div>
      </section>
    );
  }

  return (
    <section className="content manual-detail">
      <div className="page-heading">
        <div>
          <span className="section-kicker">{manual.category.name}</span>
          <h1>{manual.title}</h1>
          <p>{manual.summary}</p>
        </div>
        <div className="heading-actions">
          <Link className="secondary-button" href="/manuals">목록으로</Link>
        </div>
      </div>
      <section className="panel manual-detail-panel">
        {/* 본문은 문단 단위 평문이다. 줄바꿈을 그대로 살려 문단으로 나눈다. */}
        {manual.content.split("\n\n").map((block, index) => (
          <p className="manual-detail-block" key={index}>{block}</p>
        ))}
        {manual.assets.map((asset) => (
          asset.asset_type === "IMAGE" ? (
            <img alt={asset.alt_text ?? manual.title} className="manual-detail-image" key={asset.id} src={asset.file_url} />
          ) : (
            <a className="secondary-button" href={asset.file_url} key={asset.id} rel="noreferrer" target="_blank">첨부 파일 열기</a>
          )
        ))}
      </section>
    </section>
  );
}
