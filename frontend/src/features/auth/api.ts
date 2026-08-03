import type { Employee } from "@/types/dashboard";

import { apiRequest } from "@/lib/api-client";

type AuthMeResponse = {
  employee_id: string;
};

export async function getAuthenticatedEmployee(): Promise<string> {
  const response = await apiRequest<AuthMeResponse>("/api/v1/auth/me");
  return response.employee_id;
}

export function findAuthenticatedEmployee(
  employees: Employee[],
  employeeId: string,
): Employee | undefined {
  return employees.find((employee) => employee.id === employeeId);
}
