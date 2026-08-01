"use client";

import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { getEmployees } from "@/features/dashboard/api";
import { fallbackEmployees } from "@/features/dashboard/mock-data";
import {
  getStoredEmployeeId,
  setStoredEmployeeId,
} from "@/storage/current-user-storage";
import type { Employee } from "@/types/dashboard";

interface CurrentUserContextValue {
  employees: Employee[];
  currentEmployee: Employee;
  selectedId: string;
  setSelectedId: (employeeId: string) => void;
  apiConnected: boolean;
  isLoadingCurrentUser: boolean;
}

const CurrentUserContext = createContext<CurrentUserContextValue | null>(null);

export function CurrentUserProvider({ children }: { children: ReactNode }) {
  const [employees, setEmployees] = useState<Employee[]>(fallbackEmployees);
  const [selectedId, setSelectedIdState] = useState(fallbackEmployees[0].id);
  const [apiConnected, setApiConnected] = useState(false);
  const [isLoadingCurrentUser, setIsLoadingCurrentUser] = useState(true);

  useEffect(() => {
    const storedId = getStoredEmployeeId();

    let active = true;
    void getEmployees()
      .then((result) => {
        if (!active || result.length === 0) return;
        setEmployees(result);
        const validStored = result.some((employee) => employee.id === storedId);
        setSelectedIdState(validStored && storedId ? storedId : result[0].id);
        setApiConnected(true);
      })
      .catch(() => {
        if (active) {
          if (storedId && fallbackEmployees.some((employee) => employee.id === storedId)) {
            setSelectedIdState(storedId);
          }
          setApiConnected(false);
        }
      })
      .finally(() => {
        if (active) setIsLoadingCurrentUser(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const currentEmployee =
    employees.find((employee) => employee.id === selectedId) ?? employees[0];

  const value = useMemo(
    () => ({
      employees,
      currentEmployee,
      selectedId,
      setSelectedId: (employeeId: string) => {
        setSelectedIdState(employeeId);
        setStoredEmployeeId(employeeId);
      },
      apiConnected,
      isLoadingCurrentUser,
    }),
    [apiConnected, currentEmployee, employees, isLoadingCurrentUser, selectedId],
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
