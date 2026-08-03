import { ManualDetail } from "@/features/manuals/manual-detail";

export default async function ManualDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <ManualDetail slug={slug} />;
}
