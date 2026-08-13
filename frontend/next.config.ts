import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // 이미지 생성은 최대 120초가 걸릴 수 있다. rewrite 프록시 기본 30초를 그대로 쓰면
  // 백엔드는 생성을 마치고도 브라우저에는 socket hang up 500이 반환된다.
  experimental: {
    proxyTimeout: 180_000,
  },
  // 개발 모드 인디케이터가 사이드바 좌측 하단의 설정 버튼을 덮어 Playwright 클릭을 가로막는다.
  devIndicators: false,
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;
