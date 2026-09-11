import { expect, test } from "@playwright/test";
const api = process.env.REVIEW_E2E_API_URL ?? "http://127.0.0.1:8107";
test.skip(process.env.REVIEW_E2E !== "1", "Requires an isolated API");
test.beforeEach(async ({ page }) => {
  await page.goto("/auth/sign-in");
  await page.locator("#sign-in-email").fill("admin@example.com");
  await page.locator("#sign-in-password").fill("Admin123!");
  await page.getByRole("button", { name: "サインイン", exact: true }).click();
  await expect(page).toHaveURL(/\/admin$/);
});

test("failed requests stay unconfirmed and retry recovers", async ({ page, request }) => {
  const auth = await request.post(`${api}/api/v1/auth/sign-in`, {data: {email: "admin@example.com", password: "Admin123!"}});
  const headers = {Authorization: `Bearer ${(await auth.json()).accessToken}`};
  const created = await request.post(`${api}/api/v1/ventures`, {headers, data: {name: "取得失敗の表示確認", scale: "S"}});
  const {id} = await created.json();
  for (const fault of [500, 403, "abort"] as const) {
    await page.route(`**/api/v1/ventures/${id}/skill-gap`, route => fault === "abort" ? route.abort() : route.fulfill({status: fault, json: {detail: "検証用エラー"}}));
    await page.goto(`/ventures/${id}/skills`);
    await expect(page.getByText("データを取得できませんでした。件数・判定は確認できていません。")).toBeVisible();
    await expect(page.getByText("不足なし", {exact: true})).toHaveCount(0);
    await page.unroute(`**/api/v1/ventures/${id}/skill-gap`);
    await page.getByRole("button", {name: "再試行", exact: true}).click();
    await expect(page.getByRole("button", {name: "再試行", exact: true})).toHaveCount(0);
  }
});

test("demo project can be archived, inspected and reopened with a reason", async ({ page, request }) => {
  const auth = await request.post(`${api}/api/v1/auth/sign-in`, {data: {email: "admin@example.com", password: "Admin123!"}});
  const headers = {Authorization: `Bearer ${(await auth.json()).accessToken}`};
  const created = await request.post(`${api}/api/v1/ventures`, {headers, data: {name: "問い合わせ支援AI / 保管デモ", scale: "S"}});
  const {id} = await created.json();
  await page.goto(`/ventures/${id}`);
  await page.getByLabel("台帳を検索", {exact: true}).fill("評価計画");
  await expect(page.locator('a[href$="/ledgers/eval_plan"]')).toContainText("入力あり 0 / 18");
  await page.getByRole("button", {name: "案件設定", exact: true}).click();
  await page.getByText("案件の保管", {exact: true}).click();
  await page.getByRole("button", {name: "案件をアーカイブ", exact: true}).click();
  await page.getByRole("button", {name: "アーカイブする", exact: true}).click();
  await expect(page.getByText("アーカイブ済み · 閲覧専用", {exact: true})).toBeVisible();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.getByRole("button", {name: "案件を再開", exact: true}).click();
  const submit = page.getByRole("button", {name: "理由を記録して再開"});
  await expect(submit).toBeDisabled();
  await page.getByLabel("再開理由", {exact: true}).fill("お客様から追加検証の依頼");
  await submit.click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByText("アーカイブ済み · 閲覧専用", {exact: true})).toHaveCount(0);
  const saved = await request.get(`${api}/api/v1/ventures/${id}`, {headers});
  expect((await saved.json()).governance.reopenReason).toBe("お客様から追加検証の依頼");
});
