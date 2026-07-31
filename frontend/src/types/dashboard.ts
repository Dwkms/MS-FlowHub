export type Role =
  | "EMPLOYEE"
  | "DEPARTMENT_HEAD"
  | "HR_MANAGER"
  | "SALES_REP"
  | "SALES_MANAGER"
  | "ADMIN";

export interface Employee {
  id: string;
  employee_no: string;
  name: string;
  role: Role;
  role_label: string;
  department_id: string;
  department_name: string;
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
  source: "local" | "supabase" | "mock";
  current_employee: Employee;
  accessible_modules: string[];
  metrics: DashboardMetric[];
  recent_tasks: DashboardTask[];
}
