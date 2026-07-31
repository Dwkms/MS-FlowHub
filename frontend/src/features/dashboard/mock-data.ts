import type { DashboardData, Department, Employee } from "@/types/dashboard";

export const fallbackDepartments: Department[] = [
  { id: "dept-development", code: "DEV", name: "개발팀" },
  { id: "dept-finance", code: "FINANCE", name: "재무팀" },
  { id: "dept-hr", code: "HR", name: "인사팀" },
  { id: "dept-sales", code: "SALES", name: "영업팀" },
  { id: "dept-product", code: "PRODUCT", name: "서비스기획팀" },
];

export const fallbackEmployees: Employee[] = [
  {
    id: "emp-head",
    employee_no: "MS-1001",
    name: "김민성",
    role: "ADMIN",
    role_label: "관리자",
    department_id: "dept-product",
    department_name: "서비스기획팀",
  },
  {
    id: "emp-hr",
    employee_no: "MS-2001",
    name: "박지우",
    role: "HR_MANAGER",
    role_label: "인사 담당자",
    department_id: "dept-hr",
    department_name: "인사팀",
  },
  {
    id: "emp-sales",
    employee_no: "MS-3001",
    name: "이도윤",
    role: "SALES_REP",
    role_label: "영업사원",
    department_id: "dept-sales",
    department_name: "영업팀",
  },
  {
    id: "emp-sales-head",
    employee_no: "MS-3002",
    name: "최서윤",
    role: "SALES_MANAGER",
    role_label: "영업팀장",
    department_id: "dept-sales",
    department_name: "영업팀",
  },
];

export function createFallbackDashboard(employee: Employee): DashboardData {
  const isSales = employee.role === "SALES_REP" || employee.role === "SALES_MANAGER";

  return {
    source: "mock",
    current_employee: employee,
    accessible_modules: isSales ? ["전자결재", "CRM Lite"] : ["전자결재", "ATS Lite"],
    metrics: [
      { label: "내 결재 대기", value: 2, helper: "오늘 확인할 문서", tone: "navy" },
      { label: "진행 중 채용", value: 3, helper: "공고 2 · 지원자 4", tone: "blue" },
      { label: "승인 필요 견적", value: 1, helper: "할인 기준 초과", tone: "amber" },
      { label: "읽지 않은 알림", value: 4, helper: "최근 24시간", tone: "green" },
    ],
    recent_tasks: [
      {
        id: "task-001",
        category: "전자결재",
        title: "서비스기획팀 신규 인원 채용 요청",
        status: "결재 대기",
        owner: "김민서",
      },
      {
        id: "task-002",
        category: "ATS Lite",
        title: "Backend 개발자 채용공고 초안",
        status: "작성 중",
        owner: "박지우",
      },
      {
        id: "task-003",
        category: "CRM Lite",
        title: "한빛상사 12% 할인 견적",
        status: "승인 필요",
        owner: "이도윤",
      },
    ],
  };
}
