import { spawnSync } from "node:child_process";
import path from "node:path";

export default async function globalTeardown(): Promise<void> {
  const backendDirectory = path.resolve(process.cwd(), "..", "backend");
  const pythonPath = path.join(backendDirectory, ".venv", "Scripts", "python.exe");
  const result = spawnSync(
    pythonPath,
    ["-m", "app.scripts.cleanup_test_auth_accounts", "--e2e-only"],
    { cwd: backendDirectory, stdio: "inherit" },
  );
  if (result.status !== 0) {
    throw new Error("E2E 테스트 계정 정리에 실패했습니다.");
  }
}
