import { spawnSync } from "node:child_process";
import path from "node:path";

/**
 * E2E 보조 스크립트를 백엔드 Python으로 실행한다.
 * 기본값은 로컬 개발용 backend/.venv이며, venv가 없는 환경(CI 등)에서는
 * E2E_PYTHON 환경변수로 실행할 Python을 지정한다.
 */
export function runBackendScript(moduleName: string, args: string[] = []): void {
  const backendDirectory = path.resolve(process.cwd(), "..", "backend");
  const pythonPath =
    process.env.E2E_PYTHON ??
    path.join(
      backendDirectory,
      ".venv",
      process.platform === "win32" ? "Scripts" : "bin",
      process.platform === "win32" ? "python.exe" : "python",
    );

  const result = spawnSync(pythonPath, ["-m", moduleName, ...args], {
    cwd: backendDirectory,
    stdio: "inherit",
  });
  if (result.status !== 0) {
    throw new Error(`${moduleName} 실행에 실패했습니다.`);
  }
}
