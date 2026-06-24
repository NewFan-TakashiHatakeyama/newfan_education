import { expect, test, type Page } from "@playwright/test";

const SESSION = {
  accessToken: "tok-abc-123",
  tokenType: "bearer",
  expiresIn: 7200,
  userId: "demo-user",
  displayName: "Demo Learner",
  role: "learner",
  state: "active",
  tenantId: "company-demo"
};

async function setupAuthMockApi(page: Page, seen: { authHeader: string | null }) {
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const auth = request.headers()["authorization"] ?? null;

    const json = (value: unknown, status = 200) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(value) });

    if (path === "/api/v1/auth/sign-in") {
      return json(SESSION);
    }
    if (path === "/api/v1/auth/sign-out") {
      return json({ signedOut: true });
    }
    if (path === "/api/v1/notifications") {
      return json({ userId: "demo-user", unreadCount: 0, items: [] });
    }
    if (path === "/api/v1/messages/threads") {
      return json({ userId: "demo-user", threads: [] });
    }
    // Authed data endpoints used by the learner home — record the bearer token.
    if (path === "/api/v1/dashboard") {
      if (auth) seen.authHeader = auth;
      return json({ userId: "demo-user", completedItems: 0, totalItems: 0, completionRate: 0, recentEvents: [] });
    }
    if (path === "/api/v1/evidence") {
      if (auth) seen.authHeader = auth;
      return json({ items: [] });
    }
    return json({ detail: "not mocked" }, 404);
  });
}

test("sign-in attaches bearer token and lands on the role home", async ({ page }) => {
  const seen: { authHeader: string | null } = { authHeader: null };
  await setupAuthMockApi(page, seen);

  await page.goto("/auth/sign-in");
  await page.fill("#sign-in-email", "learner@example.com");
  await page.fill("#sign-in-password", "Learner123!");
  await page.click('button:has-text("サインイン")');

  // deterministic redirect to the learner role home (no /onboarding race)
  await expect(page).toHaveURL(/\/learner\/learn$/);

  // the JWT must be sent as a bearer header, not relying on the cookie alone
  await expect.poll(() => seen.authHeader).toBe("Bearer tok-abc-123");
});

test("sign-out clears the session and protects routes", async ({ page }) => {
  const seen: { authHeader: string | null } = { authHeader: null };
  await setupAuthMockApi(page, seen);

  await page.goto("/auth/sign-in");
  await page.fill("#sign-in-email", "learner@example.com");
  await page.fill("#sign-in-password", "Learner123!");
  await page.click('button:has-text("サインイン")');
  await expect(page).toHaveURL(/\/learner\/learn$/);

  await page.getByRole("button", { name: "サインアウト" }).click();
  await expect(page).toHaveURL(/\/auth\/sign-in$/);

  const stored = await page.evaluate(() =>
    window.localStorage.getItem("newfan.auth.session-cache")
  );
  expect(stored).toBeNull();

  // protected route now bounces back to sign-in
  await page.goto("/learner/learn");
  await expect(page).toHaveURL(/\/auth\/sign-in$/);
});
