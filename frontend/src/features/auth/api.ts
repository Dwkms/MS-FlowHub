import { apiRequest } from "@/lib/api-client";

type AuthMeResponse = {
  employee_id: string;
  role: string;
};

export async function getAuthenticatedEmployee(): Promise<{ employeeId: string; role: string }> {
  const response = await apiRequest<AuthMeResponse>("/api/v1/auth/me");
  return { employeeId: response.employee_id, role: response.role };
}
