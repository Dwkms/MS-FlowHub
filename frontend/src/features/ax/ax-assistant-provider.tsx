"use client";

import { createContext, type ReactNode, useCallback, useContext, useMemo, useRef, useState } from "react";

import type { Position } from "@/features/ax/use-draggable";
import type { AxChatResponse } from "@/types/ax";

export interface Turn {
  question: string;
  answer: AxChatResponse | null;
  error: string | null;
}

interface Positions {
  panel: Position | null;
  launcher: Position | null;
}

interface AxAssistantContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
  turns: Turn[];
  addTurn: (turn: Turn) => void;
  clearTurns: () => void;
  getPosition: (key: keyof Positions) => Position | null;
  savePosition: (key: keyof Positions, position: Position) => void;
}

const AxAssistantContext = createContext<AxAssistantContextValue | null>(null);

const STORAGE_KEY = "msflowhub.ax.positions";

/**
 * 도우미 상태를 `AuthSessionGuard` 바깥에 둔다.
 *
 * 세션 가드는 경로가 바뀔 때마다 children을 로딩 화면으로 교체하므로, 도우미를
 * 그 안에 두면 메뉴를 옮길 때마다 언마운트되어 열림 상태와 대화가 사라진다.
 *
 * 저장 정책(기획서 3장·7장):
 * - 위치만 localStorage에 남긴다. 좌표는 개인정보가 아니다.
 * - 열림 상태는 남기지 않는다. 새로고침마다 저절로 열리면 화면을 가린다.
 * - **대화 내용은 절대 남기지 않는다.** 질문 원문이 공용 PC 디스크에 남으면
 *   서버에 익명 로그만 남기기로 한 결정과 앞뒤가 맞지 않는다.
 */
export function AxAssistantProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  // 위치는 화면에 DOM으로 직접 반영되므로 state로 들고 있지 않는다(리렌더 불필요).
  const positionsRef = useRef<Positions | null>(null);

  const readPositions = useCallback((): Positions => {
    if (positionsRef.current) return positionsRef.current;
    let loaded: Positions = { panel: null, launcher: null };
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved) loaded = { ...loaded, ...(JSON.parse(saved) as Positions) };
    } catch {
      // 저장값이 깨졌으면 기본 위치를 쓴다.
    }
    positionsRef.current = loaded;
    return loaded;
  }, []);

  const getPosition = useCallback(
    (key: keyof Positions) => readPositions()[key],
    [readPositions],
  );

  const savePosition = useCallback(
    (key: keyof Positions, position: Position) => {
      const next = { ...readPositions(), [key]: position };
      positionsRef.current = next;
      try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {
        // 저장에 실패해도 이번 세션 동안은 옮긴 위치를 그대로 쓴다.
      }
    },
    [readPositions],
  );

  const addTurn = useCallback((turn: Turn) => setTurns((current) => [...current, turn]), []);
  const clearTurns = useCallback(() => setTurns([]), []);

  const value = useMemo(
    () => ({ open, setOpen, turns, addTurn, clearTurns, getPosition, savePosition }),
    [addTurn, clearTurns, getPosition, open, savePosition, turns],
  );

  return <AxAssistantContext.Provider value={value}>{children}</AxAssistantContext.Provider>;
}

export function useAxAssistant(): AxAssistantContextValue {
  const context = useContext(AxAssistantContext);
  if (!context) throw new Error("AxAssistantProvider 안에서 사용해야 합니다.");
  return context;
}
