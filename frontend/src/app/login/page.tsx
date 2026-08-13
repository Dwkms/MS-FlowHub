import { LoginForm } from "@/features/auth/login-form";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ reason?: string }>;
}) {
  // 자리 비움 자동 로그아웃은 세션 가드가 ?reason=timeout 으로 알려준다.
  const { reason } = await searchParams;
  return <LoginForm timedOut={reason === "timeout"} />;
}
