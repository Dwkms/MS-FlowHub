import { apiGet, apiRequest } from "@/lib/api-client";
import type { AttendanceChangeHistoryItem, Department, EmployeeDetail, EmployeePage, OrganizationNode } from "@/types/employee";

export type EmployeeFilters = {
  page: number;
  search?: string;
  department_code?: string;
  employment_status?: string;
  daily_work_status?: string;
  work_date?: string;
};
export function listEmployees(filters: EmployeeFilters): Promise<EmployeePage> {
  const query = new URLSearchParams({ page: String(filters.page), page_size: "20" });
  for (const [key, value] of Object.entries(filters)) {
    if (value && key !== "page") query.set(key, String(value));
  }
  return apiGet<EmployeePage>(`/api/v1/employees?${query}`);
}
export const getEmployee = (id: string) => apiGet<EmployeeDetail>(`/api/v1/employees/${id}`);
export const getAttendanceChangeHistory = (id: string, workDate: string) =>
  apiGet<AttendanceChangeHistoryItem[]>(`/api/v1/employees/${id}/attendance-history?work_date=${workDate}`);
export const updateAttendanceStatus = (
  employeeId: string,
  payload: {
    work_status: string;
    reason_category?: string;
    reason_summary?: string;
    private_note?: string;
    work_date?: string;
  },
) => apiRequest<EmployeeDetail>(
  `/api/v1/employees/${employeeId}/attendance`,
  { method: "PUT", body: payload },
);
export const updateEmploymentStatusReason = (
  employeeId: string,
  payload: {
    reason_category?: string;
    reason_summary: string;
    private_note?: string;
    effective_from?: string;
  },
) =>
  apiRequest<EmployeeDetail>(
    `/api/v1/employees/${employeeId}/employment-status-reason`,
    { method: "PATCH", body: payload },
  );
export const getEmployeeDepartments = () => apiGet<Department[]>("/api/v1/departments");
export const getOrganization = () => apiGet<OrganizationNode>("/api/v1/employees/organization");
