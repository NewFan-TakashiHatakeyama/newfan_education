import { expect, test, type Page } from "@playwright/test";

async function setupShell(page: Page) {
  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    const json = (value: unknown) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(value) });
    if (path === "/api/v1/notifications") return json({ userId: "u", unreadCount: 0, items: [] });
    if (path === "/api/v1/messages/threads") return json({ userId: "u", threads: [] });
    return json({ items: [] });
  });
  await page.addInitScript(() => {
    window.localStorage.setItem(
      "newfan.auth.session-cache",
      JSON.stringify({
        accessToken: "tok",
        tokenType: "bearer",
        expiresIn: 7200,
        userId: "admin-user",
        displayName: "Admin",
        role: "admin",
        state: "active",
        tenantId: "company-demo"
      })
    );
  });
}

test("company nav is consolidated into 4 top-level menus with collapsible groups", async ({ page }) => {
  await setupShell(page);
  await page.goto("/courses");
  await expect(page.getByRole("heading", { name: "AI講座カタログ" })).toBeVisible();

  const nav = page.locator(".side-nav");
  // 4 top-level company entries: 1 leaf + 3 group toggles
  await expect(nav.getByRole("link", { name: "ダッシュボード", exact: true })).toBeVisible();
  for (const group of ["育成管理", "AIプロジェクト", "組織・設定"]) {
    await expect(nav.getByRole("button", { name: group, exact: true })).toBeVisible();
  }

  // groups start collapsed, so their children are hidden
  await expect(nav.getByRole("link", { name: "受講者進捗", exact: true })).toHaveCount(0);

  // expanding a group reveals its children
  await nav.getByRole("button", { name: "育成管理", exact: true }).click();
  await expect(nav.getByRole("link", { name: "受講者進捗", exact: true })).toBeVisible();
  await expect(nav.getByRole("link", { name: "育成ロードマップ", exact: true })).toBeVisible();
  await expect(nav.getByRole("link", { name: "成果物一覧", exact: true })).toBeVisible();

  // collapsing hides them again
  await nav.getByRole("button", { name: "育成管理", exact: true }).click();
  await expect(nav.getByRole("link", { name: "受講者進捗", exact: true })).toHaveCount(0);
});
