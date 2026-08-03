import type { ManualRole } from "@/types/manual";

export const manualRoleLabels: Record<ManualRole, string> = {
  SUPER_ADMIN: "최고 관리자",
  HR_ADMIN: "인사 관리자",
  TEAM_ADMIN: "팀 관리자",
  EMPLOYEE: "직원",
};

export function formatManualDate(value: string): string {
  return new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium" }).format(new Date(value));
}
