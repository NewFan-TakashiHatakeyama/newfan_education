import { expect, test } from "@playwright/test";

const api = process.env.REVIEW_E2E_API_URL ?? "http://127.0.0.1:8107";
test.skip(process.env.REVIEW_E2E !== "1", "Requires an isolated local API");

test.beforeEach(async ({ page }) => {
  await page.goto("/auth/sign-in");
  await page.locator("#sign-in-email").fill("admin@example.com");
  await page.locator("#sign-in-password").fill("Admin123!");
  await page.getByRole("button", { name: "サインイン", exact: true }).click();
  await expect(page).toHaveURL(/\/admin$/);
});

test("modal contains keyboard focus and preserves or discards an unsaved draft explicitly", async ({ page }) => {
  await page.goto("/company/teams");
  const trigger = page.getByRole("button", { name: "チームを作成", exact: true });
  await expect(page.locator("#team-name")).toHaveCount(0);
  await trigger.click();
  const dialog = page.getByRole("dialog", { name: "チーム作成", exact: true });
  await dialog.getByLabel("チーム名", { exact: true }).fill("未保存のチーム");
  for (let index = 0; index < 8; index++) {
    await page.keyboard.press("Tab");
    expect(await dialog.evaluate(node => node.contains(document.activeElement))).toBe(true);
  }
  await page.keyboard.press("Escape");
  await expect(dialog.getByText("変更を破棄しますか？")).toBeVisible();
  await dialog.getByRole("button", { name: "編集を続ける" }).click();
  await expect(dialog.getByLabel("チーム名", { exact: true })).toHaveValue("未保存のチーム");
  await page.keyboard.press("Escape");
  await dialog.getByRole("button", { name: "変更を破棄して閉じる" }).click();
  await expect(dialog).toHaveCount(0);
  await expect(trigger).toBeFocused();
  await trigger.click();
  await expect(dialog.getByLabel("チーム名", { exact: true })).toHaveValue("");
});

test("overview prioritizes actions and progress; desktop and mobile screens stay usable", async ({ page, request }) => {
  const login = await request.post(`${api}/api/v1/auth/sign-in`, { data: { email: "admin@example.com", password: "Admin123!" } });
  const headers = { Authorization: `Bearer ${(await login.json()).accessToken}` };
  const created = await request.post(`${api}/api/v1/ventures`, { headers, data: { name: "問い合わせ支援AI / UX検証", summary: "問い合わせ対応を短縮するPoC", scale: "S" } });
  expect(created.ok()).toBeTruthy();
  const venture = await created.json();
  await page.goto(`/ventures/${venture.id}`);
  await expect(page.getByRole("heading", { name: "次に対応すること" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "工程の進捗" })).toBeVisible();
  await expect(page.getByRole("combobox")).toHaveCount(0);
  await page.screenshot({ path: "test-results/ux-overview.png", fullPage: true });
  await page.getByLabel("台帳を検索", {exact: true}).fill("評価");
  await expect(page.locator(`a[href*="/ledgers/eval_plan"]`)).toBeVisible();
  await page.getByLabel("台帳を検索", {exact: true}).clear();
  await page.getByRole("button", { name: "案件設定", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "案件設定", exact: true })).toBeVisible();
  await page.screenshot({ path: "test-results/ux-settings.png" });
  await page.keyboard.press("Escape");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "案件設定", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "案件設定", exact: true });
  const bounds = await dialog.boundingBox();
  expect(bounds!.width).toBeLessThanOrEqual(390);
  await expect(dialog.getByRole("button", { name: "閉じる", exact: true })).toBeInViewport();
  await page.screenshot({ path: "test-results/ux-mobile-settings.png" });
  await page.keyboard.press("Escape");
  await page.setViewportSize({ width: 1280, height: 900 });
  for (const route of ["/company/dashboard", "/company/requirements", "/company/reports", "/company/learners", "/company/roadmaps", "/company/evidence", "/company/fit-assessments", "/admin/users", "/notifications", `/ventures/${venture.id}/gates`, `/ventures/${venture.id}/tasks`]) {
    await page.goto(route);
    await expect(page.locator("body")).not.toContainText("Application error");
    await expect(page.locator("h1, h2").first()).toBeVisible();
  }
  await page.screenshot({ path: "test-results/ux-tasks.png", fullPage: true });
});

test("learner and mentor screens present the next task and honest availability", async ({ page }) => {
  await page.evaluate(() => localStorage.clear());
  for (const account of [
    {email: "learner@example.com", password: "Learner123!", home: "/learner/learn", routes: ["/learner/learn", "/learner/evidence", "/courses", "/notifications"]},
    {email: "mentor@example.com", password: "Mentor123!", home: "/mentor/reviews", routes: ["/mentor/reviews", "/notifications"]}
  ]) {
    await page.goto("/auth/sign-in");
    await page.locator("#sign-in-email").fill(account.email);
    await page.locator("#sign-in-password").fill(account.password);
    await page.getByRole("button", {name: "サインイン", exact: true}).click();
    await expect(page).toHaveURL(new RegExp(account.home + "$"));
    for (const route of account.routes) {
      await page.goto(route);
      await expect(page.locator("h1").first()).toBeVisible();
      await expect(page.locator("body")).not.toContainText("Application error");
      if (route === account.home) await page.screenshot({path: `test-results/ux-${account.email.split("@")[0]}.png`, fullPage: true});
    }
    await page.evaluate(() => localStorage.clear());
  }
});
