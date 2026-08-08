import { defineConfig, devices } from "@playwright/test";
import { config as loadEnvironment } from "dotenv";

loadEnvironment({ path: ".env.e2e", quiet: true });

const baseURL = process.env.E2E_BASE_URL ?? "http://127.0.0.1:3000";

// 로컬(Windows)은 backend/.venv를 그대로 쓰고, CI처럼 venv가 없는 환경에서는
// E2E_BACKEND_COMMAND로 백엔드 실행 명령을 덮어쓴다.
const backendCommand =
  process.env.E2E_BACKEND_COMMAND ?? ".\\run-backend.cmd";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }]],
  globalSetup: "./e2e/global-setup.ts",
  globalTeardown: "./e2e/global-teardown.ts",
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: backendCommand,
      cwd: "..",
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: !process.env.CI,
    },
    {
      command: "npm run dev",
      url: baseURL,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
