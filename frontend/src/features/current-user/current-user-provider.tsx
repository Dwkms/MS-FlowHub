"use client";

/**
 * 로그인한 직원 정보를 앱 전체에 공급합니다.
 *
 * 화면마다 "지금 누가 보고 있나"를 각자 조회하면 같은 API를 여러 번 부르게 되고,
 * 한 화면에서 역할이 바뀌어도 다른 화면은 옛 값을 들고 있게 됩니다. React Context로
 * 한 곳에 두고 필요한 컴포넌트가 `useCurrentUser()`로 꺼내 씁니다.
 *
 * 여기 담긴 `role`은 **화면 표시 판단에만** 씁니다. 편집 버튼을 보일지 말지 같은
 * 것입니다. 실제 차단은 항상 서버가 다시 합니다. 브라우저 값은 사용자가 바꿀 수
 * 있으므로 이것만 믿으면 안 됩니다.
 */

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
