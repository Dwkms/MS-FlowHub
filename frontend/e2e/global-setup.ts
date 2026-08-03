import { spawnSync } from "node:child_process";
import path from "node:path";

function runBackendScript(moduleName: string): void {
  const backendDirectory = path.resolve(process.cwd(), "..", "backend");
  const pythonPath = path.join(backendDirectory, ".venv", "Scripts", "python.exe");
  const result = spawnSync(pythonPath, ["-m", moduleName], {
    cwd: backendDirectory,
    stdio: "inherit",
  });
  if (result.status !== 0) {
    throw new Error(`${moduleName} 실행에 실패했습니다.`);
  }
}

export default async function globalSetup(): Promise<void> {
  runBackendScript("app.scripts.seed_e2e_auth_accounts");
}
