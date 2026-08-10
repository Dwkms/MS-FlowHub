import { ManualDetailView } from "@/features/manuals/manual-detail";

export default async function ManualDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <ManualDetailView slug={slug} />;
}
