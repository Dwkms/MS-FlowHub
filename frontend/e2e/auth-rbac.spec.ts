import { expect, test, type Page } from "@playwright/test";

type Credentials = { email: string; password: string };

function requiredEnvironment(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`${name} must be set in the local E2E environment.`);
  return value;
}

function account(prefix: "E2E_EMPLOYEE" | "E2E_SUPER_ADMIN"): Credentials {
  return {
    email: requiredEnvironment(`${prefix}_EMAIL`),
    password: requiredEnvironment(`${prefix}_PASSWORD`),
  };
}

async function login(page: Page, credentials: Credentials): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("이메일").fill(credentials.email);
  await page.getByLabel("비밀번호").fill(credentials.password);
  await page.getByRole("button", { name: "로그인", exact: true }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.locator(".connection.ok")).toHaveCount(1);
}

async function logout(page: Page): Promise<void> {
  await page.getByRole("button", { name: "설정" }).click();
  await page.getByRole("button", { name: "로그아웃" }).click();
  await expect(page).toHaveURL(/\/login$/);
}

async function changePassword(
  page: Page,
  email: string,
  currentPassword: string,
  newPassword: string,
): Promise<void> {
  await page.goto(`/change-password?email=${encodeURIComponent(email)}`);
  await page.getByLabel("현재 비밀번호").fill(currentPassword);
  await page.getByLabel("새 비밀번호", { exact: true }).fill(newPassword);
  await page.getByLabel("새 비밀번호 다시 입력").fill(newPassword);
  await page.getByRole("button", { name: "비밀번호 변경", exact: true }).click();
  await expect(page).toHaveURL(/\/$/);
}

test("잘못된 로그인 정보는 오류를 표시한다", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("이메일").fill("e2e-invalid@msflowhub.test");
  await page.getByLabel("비밀번호").fill("not-a-valid-password");
  await page.getByRole("button", { name: "로그인", exact: true }).click();

  await expect(page.getByText("Invalid login credentials")).toBeVisible();
});

test.describe("테스트 전용 인증 계정", () => {
  test.skip(
    !process.env.E2E_EMPLOYEE_EMAIL ||
      !process.env.E2E_EMPLOYEE_PASSWORD ||
      !process.env.E2E_SUPER_ADMIN_EMAIL ||
      !process.env.E2E_SUPER_ADMIN_PASSWORD ||
      !process.env.E2E_SUPER_ADMIN_EMPLOYEE_ID,
    "E2E 전용 일반 직원·SUPER_ADMIN 계정 환경변수가 필요합니다.",
  );

  test("로그인, 새로고침 세션 유지, 로그아웃을 확인한다", async ({ page }) => {
    await login(page, account("E2E_EMPLOYEE"));
    await page.reload();
    await expect(page.locator(".connection.ok")).toHaveCount(1);
    await logout(page);
  });

  test("일반 직원은 본인 범위만 보고 관리자는 직원 화면에 접근한다", async ({ page }) => {
    await login(page, account("E2E_EMPLOYEE"));
    await page.goto("/employees");
    await expect(page.getByRole("heading", { name: "직원 · 조직 관리" })).toBeVisible();
    await expect(
      page.locator(".employee-desktop-table:visible tbody tr, .employee-mobile-list:visible .employee-mobile-row"),
    ).toHaveCount(1);
    await logout(page);

    await login(page, account("E2E_SUPER_ADMIN"));
    await page.goto("/employees");
    await expect(page.getByRole("heading", { name: "직원 · 조직 관리" })).toBeVisible();
    await expect(
      page.locator(".employee-desktop-table:visible tbody tr, .employee-mobile-list:visible .employee-mobile-row"),
    ).not.toHaveCount(0);
  });

  test("직원 검색과 부서·재직·근무 상태 필터를 적용한다", async ({ page }) => {
    await login(page, account("E2E_SUPER_ADMIN"));
    await page.goto("/employees");
    await page.getByLabel("직원 검색").fill("김");
    await expect(page).toHaveURL(/search=%EA%B9%80/);
    await page.getByLabel("부서 필터").selectOption({ index: 1 });
    await page.getByLabel("재직 상태 필터").selectOption("ACTIVE");
    await page.getByLabel("근무 상태 필터").selectOption("WORKING");
    await expect(
      page.locator(".employee-desktop-table:visible, .employee-mobile-list:visible").or(page.getByText("검색 결과가 없습니다.")),
    ).toBeVisible();
  });

  test("직원 화면에서 최신 조직도 이미지를 표시한다", async ({ page }) => {
    await login(page, account("E2E_SUPER_ADMIN"));
    await page.goto("/employees");
    await page.getByRole("button", { name: "조직도 보기" }).click();
    const chart = page.getByRole("img", { name: "MS FlowHub 조직도" });
    await expect(chart).toBeVisible();
    await expect(chart).toHaveAttribute("src", /organization-chart.png/);
    await expect
      .poll(() => chart.evaluate((image: HTMLImageElement) => image.naturalWidth))
      .toBeGreaterThan(0);
  });

  test("일반 직원이 작성한 전자결재를 SUPER_ADMIN이 승인한다", async ({ page }) => {
    const title = `E2E 결재 ${Date.now()}`;
    await login(page, account("E2E_EMPLOYEE"));
    await page.goto("/approvals/new");
    await page.getByLabel("제목 *").fill(title);
    await page.getByLabel("결재자 *").selectOption(
      requiredEnvironment("E2E_SUPER_ADMIN_EMPLOYEE_ID"),
    );
    await page.getByLabel("내용 *").fill("Playwright E2E 결재 승인 검증 문서입니다.");
    await page.getByRole("button", { name: "결재 요청", exact: true }).click();
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    await expect(page.locator(".approval-status")).toHaveText("결재 대기");
    const approvalUrl = page.url();
    await logout(page);

    await login(page, account("E2E_SUPER_ADMIN"));
    await page.goto(approvalUrl);
    await page.getByRole("button", { name: "승인", exact: true }).click();
    await expect(page.getByText("문서를 승인했습니다.")).toBeVisible();
  });
});

test.describe("테스트 전용 비밀번호 변경 계정", () => {
  test.skip(
    !process.env.E2E_PASSWORD_CHANGE_NEW_PASSWORD,
    "E2E 전용 비밀번호 변경용 임시 비밀번호 환경변수가 필요합니다.",
  );

  test("비밀번호를 변경한 뒤 원래 비밀번호로 복구한다", async ({ page }) => {
    const employeeAccount = account("E2E_EMPLOYEE");
    const { email, password: originalPassword } = employeeAccount;
    const temporaryPassword = requiredEnvironment("E2E_PASSWORD_CHANGE_NEW_PASSWORD");
    let changed = false;

    try {
      await changePassword(page, email, originalPassword, temporaryPassword);
      changed = true;
      await logout(page);
      await login(page, { email, password: temporaryPassword });
    } finally {
      if (changed) {
        await changePassword(page, email, temporaryPassword, originalPassword);
      }
    }
  });
});
