import type { Metadata } from "next";

import { PortalShell } from "@/components/portal-shell";
import { AuthSessionGuard } from "@/features/auth/auth-session-guard";
import { AxAssistantProvider } from "@/features/ax/ax-assistant-provider";
import { CurrentUserProvider } from "@/features/current-user/current-user-provider";

import "./globals.css";

export const metadata: Metadata = {
  title: "MS FlowHub",
  description: "전자결재 중심 사내 업무 통합 플랫폼",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>
        <CurrentUserProvider>
          {/* 세션 가드는 경로가 바뀔 때 children을 로딩 화면으로 교체한다.
              도우미 상태를 그 바깥에 둬야 메뉴를 옮겨도 열림 상태와 대화가 유지된다. */}
          <AxAssistantProvider>
            <AuthSessionGuard>
              <PortalShell>{children}</PortalShell>
            </AuthSessionGuard>
          </AxAssistantProvider>
        </CurrentUserProvider>
      </body>
    </html>
  );
}
