import { expect, test, type Page } from "@playwright/test";

async function seedShell(page: Page) {
  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    const json = (v: unknown) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(v) });
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
        userId: "demo-user",
        displayName: "Demo Learner",
        role: "learner",
        state: "active",
        tenantId: "company-demo"
      })
    );
  });
}

test("genai-foundations reading lesson renders content and a course TOC", async ({ page }) => {
  await seedShell(page);
  await page.goto("/learn/genai-foundations/what-is-genai");

  // body content is rendered (not the "not found" placeholder)
  await expect(page.getByText("LLMは「次の単語」を予測している")).toBeVisible();
  await expect(page.getByText("教材が見つかりませんでした")).toHaveCount(0);

  // the table of contents lists the other course lessons
  await expect(page.getByText("主要サービスと使い分け")).toBeVisible();
  await expect(page.getByText("プロンプト設計の基本")).toBeVisible();
});

test("genai-foundations code lesson links to the real exercise runner", async ({ page }) => {
  await seedShell(page);
  await page.goto("/learn/genai-foundations/build-prompt");

  const exerciseLink = page.getByRole("link", { name: "演習へ進む" });
  await expect(exerciseLink).toHaveAttribute("href", "/learner/exercises/ex-genai-prompt-001");
});
