"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

import { getEmployees } from "@/features/dashboard/api";
import type { Employee } from "@/types/dashboard";

interface CurrentUserContextValue {
  employees: Employee[];
  currentEmployee: Employee;
  authenticatedEmployeeId: string;
  syncAuthenticatedEmployee: (employeeId: string, role: string) => Promise<boolean>;
  apiConnected: boolean;
  isLoadingCurrentUser: boolean;
}

const CurrentUserContext = createContext<CurrentUserContextValue | null>(null);

export function CurrentUserProvider({ children }: { children: ReactNode }) {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [authenticatedEmployeeId, setAuthenticatedEmployeeId] = useState("");
  const [apiConnected, setApiConnected] = useState(false);
  const [isLoadingCurrentUser, setIsLoadingCurrentUser] = useState(false);
  const currentEmployee = employees.find((employee) => employee.id === authenticatedEmployeeId);

  const syncAuthenticatedEmployee = useCallback(async (employeeId: string, role: string) => {
    setIsLoadingCurrentUser(true);
    try {
      const result = await getEmployees();
      const authenticatedEmployee = result.find((employee) => employee.id === employeeId);
      if (!authenticatedEmployee) {
        setEmployees([]);
        setAuthenticatedEmployeeId("");
        setApiConnected(false);
        return false;
      }
      // employee-options returns employees.role (legacy job classification). Only the signed-in
      // user's entry is patched with the real employee_accounts.role from /auth/me, since every
      // permission check in the app reads currentEmployee.role expecting the RBAC value.
      const patched = result.map((employee) =>
        employee.id === employeeId ? { ...employee, role: role as Employee["role"] } : employee,
      );
      setEmployees(patched);
      setAuthenticatedEmployeeId(employeeId);
      setApiConnected(true);
      return true;
    } catch {
      setEmployees([]);
      setAuthenticatedEmployeeId("");
      setApiConnected(false);
      return false;
    } finally {
      setIsLoadingCurrentUser(false);
    }
  }, []);

  const value = useMemo(
    () => ({
      employees,
      currentEmployee: currentEmployee as Employee,
      authenticatedEmployeeId,
      syncAuthenticatedEmployee,
      apiConnected,
      isLoadingCurrentUser,
    }),
    [apiConnected, authenticatedEmployeeId, currentEmployee, employees, isLoadingCurrentUser, syncAuthenticatedEmployee],
  );

  return (
    <CurrentUserContext.Provider value={value}>
      {children}
    </CurrentUserContext.Provider>
  );
}

export function useCurrentUser(): CurrentUserContextValue {
  const context = useContext(CurrentUserContext);
  if (!context) throw new Error("CurrentUserProvider 안에서 사용해야 합니다.");
  return context;
}
