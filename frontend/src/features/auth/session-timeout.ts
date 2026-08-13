"use client";

import { useCallback, useEffect, useRef } from "react";

import { getSupabaseBrowserClient } from "@/lib/supabase-browser";

/**
 * 자리 비움 자동 로그아웃.
 *
 * Supabase 세션은 localStorage에 남고 토큰이 자동 갱신되므로 창을 닫아도 로그인이 유지된다.
 * "창을 닫았는지"는 직접 알 수 없지만, 화면이 열려 있는 동안 일정 간격으로 생존 신호를 남겨두면
 * 신호가 끊긴 공백이 곧 닫혀 있던 시간이 된다. 다시 열었을 때 그 공백이 기준을 넘으면 세션을 끊는다.
 *
 * 열어만 두면 조작이 없어도 로그인은 유지된다. 신호는 조작이 아니라 화면이 살아 있는 동안 남는다.
 */

const LAST_SEEN_KEY = "msflowhub.lastSeenAt";
const DEFAULT_TIMEOUT_MINUTES = 30;
/** 생존 신호 간격. 허용 시간보다 훨씬 짧아야 닫힌 시간이 정확하게 잡힌다. */
const HEARTBEAT_INTERVAL_MS = 30_000;

/** 자리를 비워도 되는 시간. 값이 없거나 이상하면 기본 30분으로 돌아간다. */
export function getSessionTimeoutMs(): number {
  const configured = Number(process.env.NEXT_PUBLIC_SESSION_TIMEOUT_MINUTES);
  const minutes =
    Number.isFinite(configured) && configured > 0 ? configured : DEFAULT_TIMEOUT_MINUTES;
  return minutes * 60_000;
}

function readLastSeenAt(): number | null {
  try {
    const stored = window.localStorage.getItem(LAST_SEEN_KEY);
    if (!stored) return null;
    const parsed = Number(stored);
    return Number.isFinite(parsed) ? parsed : null;
  } catch {
    // 시크릿 모드 등 localStorage가 막힌 환경에서는 자리 비움을 재지 않는다.
    return null;
  }
}

function writeLastSeenAt(at: number): void {
  try {
    window.localStorage.setItem(LAST_SEEN_KEY, String(at));
  } catch {
    // 저장이 막혀도 화면 동작 자체는 막지 않는다.
  }
}

/** 로그인 직후처럼 시계를 처음부터 다시 재야 할 때 호출한다. */
export function markSeenNow(): void {
  if (typeof window === "undefined") return;
  writeLastSeenAt(Date.now());
}

/** 수동 로그아웃 시 남은 시각이 다음 로그인까지 따라오지 않도록 지운다. */
export function clearLastSeenAt(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(LAST_SEEN_KEY);
  } catch {
    // 위와 같다.
  }
}

type SessionTimeoutOptions = {
  /** 로그인이 필요한 화면에서만 켠다. */
  enabled: boolean;
  /**
   * 세션을 끊기 직전에 부른다.
   * signOut()이 끝나기 전에 Supabase가 SIGNED_OUT을 먼저 알리는 경우가 있어,
   * 어느 쪽이 먼저 화면을 옮기든 같은 주소로 가도록 사유를 미리 넘긴다.
   */
  onSignOutStart: () => void;
  /** 세션을 끊은 뒤 화면을 옮기는 처리. */
  onSignOutEnd: () => void;
};

export function useSessionTimeout({
  enabled,
  onSignOutStart,
  onSignOutEnd,
}: SessionTimeoutOptions): void {
  const signingOutRef = useRef(false);
  const onSignOutStartRef = useRef(onSignOutStart);
  const onSignOutEndRef = useRef(onSignOutEnd);

  useEffect(() => {
    onSignOutStartRef.current = onSignOutStart;
    onSignOutEndRef.current = onSignOutEnd;
  }, [onSignOutStart, onSignOutEnd]);

  const signOut = useCallback(async () => {
    if (signingOutRef.current) return;
    signingOutRef.current = true;
    clearLastSeenAt();
    onSignOutStartRef.current();
    try {
      await getSupabaseBrowserClient().auth.signOut();
    } finally {
      onSignOutEndRef.current();
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;

    const limitMs = getSessionTimeoutMs();
    signingOutRef.current = false;

    // 다른 탭이 열려 있으면 그 탭이 계속 신호를 남기므로, 이 탭만 닫혔다고 로그아웃되지 않는다.
    const check = () => {
      const lastSeenAt = readLastSeenAt();
      if (lastSeenAt !== null && Date.now() - lastSeenAt > limitMs) {
        void signOut();
        return;
      }
      writeLastSeenAt(Date.now());
    };

    // 백그라운드 탭은 타이머가 느려질 수 있어, 화면으로 돌아온 순간에도 한 번 확인한다.
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") check();
    };

    check();
    const timer = window.setInterval(check, HEARTBEAT_INTERVAL_MS);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [enabled, signOut]);
}
