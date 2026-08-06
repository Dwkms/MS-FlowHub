// employees.role (legacy job classification, shown via role_label for any employee in a list)
export type LegacyJobRole =
  | "EMPLOYEE"
  | "DEPARTMENT_HEAD"
  | "HR_MANAGER"
  | "SALES_REP"
  | "SALES_MANAGER"
  | "ADMIN";

// employee_accounts.role (actual RBAC role, only accurate for the signed-in currentEmployee —
// see current-user-provider.tsx, which overrides this field with the value from /api/v1/auth/me)
export type AuthRole = "SUPER_ADMIN" | "HR_ADMIN" | "TEAM_ADMIN" | "EMPLOYEE";

export type Role = LegacyJobRole | AuthRole;

export interface Employee {
  id: string;
  employee_no: string;
  name: string;
  role: Role;
  role_label: string;
  position?: string;
  department_id: string;
  department_name: string;
  team_code: string | null;
}

export interface Department {
  id: string;
  code: string;
  name: string;
}

export interface DashboardMetric {
  label: string;
  value: number;
  helper: string;
  tone: "navy" | "blue" | "amber" | "green";
}

export interface DashboardTask {
  id: string;
  category: string;
  title: string;
  status: string;
  owner: string;
  href?: string | null;
}

export interface DashboardData {
  source: "local" | "supabase";
  current_employee: Employee;
  accessible_modules: string[];
  metrics: DashboardMetric[];
  recent_tasks: DashboardTask[];
}
