"use client";

import { type FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { getSupabaseBrowserClient } from "@/lib/supabase-browser";

export function LoginForm() {
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
        {error && <div className="inline-alert error">{error}</div>}
        <label><span>이메일</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
        <label><span>비밀번호</span><input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
        <button className="primary-button" disabled={submitting}>{submitting ? "로그인 중..." : "로그인"}</button>
        <button className="password-change-entry" type="button" onClick={() => router.push(`/change-password?email=${encodeURIComponent(email)}`)}>비밀번호 변경</button>
      </form>
    </main>
  );
}
