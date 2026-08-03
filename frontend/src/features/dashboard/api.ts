import { apiGet } from "@/lib/api-client";
import type { DashboardData, Department, Employee } from "@/types/dashboard";

export function getEmployees(): Promise<Employee[]> {
  return apiGet<Employee[]>("/api/v1/employee-options");
}

export function getDepartments(): Promise<Department[]> {
  return apiGet<Department[]>("/api/v1/departments");
}

export function getDashboard(): Promise<DashboardData> {
  return apiGet<DashboardData>("/api/v1/dashboard");
}
