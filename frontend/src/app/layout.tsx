import type { Metadata } from "next";

import { PortalShell } from "@/components/portal-shell";
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
          <PortalShell>{children}</PortalShell>
        </CurrentUserProvider>
      </body>
    </html>
  );
}
