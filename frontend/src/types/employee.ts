export interface EmployeeManager { id: string; employee_no: string; name: string; position: string }
export interface EmployeeSummary {
  id: string; employee_no: string; name: string; email: string; department: string;
  department_code: string; team: string | null; team_code: string | null; position: string;
  job_title: string; manager: EmployeeManager | null; employment_status: string;
  daily_work_status: string | null; has_employment_status_reason: boolean; has_daily_work_reason: boolean;
  check_in_at: string | null; check_out_at: string | null; work_location: string;
}
export interface StatusReasonDetail {
  reason_category: string | null; reason_summary: string | null; private_note: string | null;
  period_start: string; period_end: string | null; registered_by_name: string | null; registered_at: string | null;
}
export interface EmployeeDetail extends EmployeeSummary {
  role: string; department_id: string; team_id: string | null; job_description: string | null;
  employment_type: string; hire_date: string | null; phone_extension: string | null; profile_image_url: string | null;
  employment_status_reason: StatusReasonDetail | null; daily_work_reason: StatusReasonDetail | null;
}
export interface EmployeePage { items: EmployeeSummary[]; page: number; page_size: number; total: number; total_pages: number }
export interface Department { id: string; code: string; name: string; description: string | null }
export interface OrganizationNode { id: string; employee_no: string; name: string; position: string; department: string; children: OrganizationNode[] }
