"use client";

import { type FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { markSeenNow } from "@/features/auth/session-timeout";
import { getSupabaseBrowserClient } from "@/lib/supabase-browser";

export function LoginForm({ timedOut = false }: { timedOut?: boolean }) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const { error: signInError } = await getSupabaseBrowserClient().auth.signInWithPassword({
        email,
        password,
      });
      if (signInError) throw signInError;
      // 지난 로그인에서 남은 시각으로 곧바로 다시 끊기지 않도록 시계를 새로 건다.
      markSeenNow();
      router.replace("/");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "로그인에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <form className="login-card" onSubmit={(event) => void submit(event)}>
        <p className="login-kicker">MS FLOWHUB</p>
        <h1>로그인</h1>
        <p>업무를 계속하려면 로그인해 주세요.</p>
        {timedOut && <div className="inline-alert warning">장시간 접속하지 않아 자동 로그아웃되었습니다. 다시 로그인해 주세요.</div>}
        {error && <div className="inline-alert error">{error}</div>}
        <label><span>이메일</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
        <label><span>비밀번호</span><input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
        <button className="primary-button" disabled={submitting}>{submitting ? "로그인 중..." : "로그인"}</button>
        <button className="password-change-entry" type="button" onClick={() => router.push(`/change-password?email=${encodeURIComponent(email)}`)}>비밀번호 변경</button>
      </form>
    </main>
  );
}
