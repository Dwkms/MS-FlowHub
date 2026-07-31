const CURRENT_EMPLOYEE_KEY = "ms-flowhub.current-employee-id";

export function getStoredEmployeeId(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(CURRENT_EMPLOYEE_KEY);
}

export function setStoredEmployeeId(employeeId: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(CURRENT_EMPLOYEE_KEY, employeeId);
}
