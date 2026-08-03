import { ManualForm } from "@/features/manuals/manual-form";

export default async function EditManualPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <ManualForm slug={slug} />;
}
