"use client";

import { type FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { getSupabaseBrowserClient } from "@/lib/supabase-browser";

export function ChangePasswordForm() {
  const router = useRouter();
  const email = typeof window === "undefined" ? "" : new URLSearchParams(window.location.search).get("email") ?? "";
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newPasswordConfirmation, setNewPasswordConfirmation] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (newPassword !== newPasswordConfirmation) {
      setError("새 비밀번호가 일치하지 않습니다.");
      return;
    }
    setSubmitting(true);
    try {
      const client = getSupabaseBrowserClient();
      if (!email) throw new Error("로그인 화면에서 이메일을 입력한 뒤 비밀번호 변경을 선택해 주세요.");
      const { error: verifyError } = await client.auth.signInWithPassword({
        email,
        password: currentPassword,
      });
      if (verifyError) throw new Error("현재 비밀번호가 올바르지 않습니다.");
      const { error: updateError } = await client.auth.updateUser({ password: newPassword });
      if (updateError) throw updateError;
      router.replace("/");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "비밀번호를 변경하지 못했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <form className="login-card password-change-form" onSubmit={(event) => void submit(event)}>
        <p className="login-kicker">ACCOUNT</p>
        <h1>비밀번호 변경</h1>
        <p>현재 비밀번호를 확인한 뒤 새 비밀번호로 변경합니다.</p>
        {error && <div className="inline-alert error">{error}</div>}
        <label className="form-field"><span>현재 비밀번호</span><input type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} required /></label>
        <label className="form-field"><span>새 비밀번호</span><input type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} minLength={8} required /></label>
        <label className="form-field"><span>새 비밀번호 다시 입력</span><input type="password" value={newPasswordConfirmation} onChange={(event) => setNewPasswordConfirmation(event.target.value)} minLength={8} required /></label>
        <div className="form-actions"><button className="primary-button" disabled={submitting}>{submitting ? "변경 중..." : "비밀번호 변경"}</button></div>
      </form>
    </main>
  );
}
