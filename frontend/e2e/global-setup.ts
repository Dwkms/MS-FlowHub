import { runBackendScript } from "./backend-script";

export default async function globalSetup(): Promise<void> {
  runBackendScript("app.scripts.seed_e2e_auth_accounts");
}
