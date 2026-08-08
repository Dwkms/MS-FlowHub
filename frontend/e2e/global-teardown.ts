import { runBackendScript } from "./backend-script";

export default async function globalTeardown(): Promise<void> {
  runBackendScript("app.scripts.cleanup_test_auth_accounts", ["--e2e-only"]);
}
