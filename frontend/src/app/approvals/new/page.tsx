"use client";

import { ApprovalForm } from "@/features/approvals/approval-form";
import { useCurrentUser } from "@/features/current-user/current-user-provider";

export default function NewApprovalPage() {
  const { currentEmployee } = useCurrentUser();

  return <ApprovalForm key={currentEmployee.id} />;
}
