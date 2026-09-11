import { expect, test } from "@playwright/test";

// Run only against the dedicated local API with an isolated test database.
const api = process.env.REVIEW_E2E_API_URL ?? "http://127.0.0.1:8107";
test.skip(process.env.REVIEW_E2E !== "1", "Requires the isolated review verification server");

test("invitation link, separate reviewer appointment and risk verification complete through real UI", async ({ page, browser, request }) => {
  const identity = `review-ui-${Date.now()}`;
  const email = `${identity}@example.test`;
  const login = await request.post(`${api}/api/v1/auth/sign-in`, {data: {email: "admin@example.com", password: "Admin123!"}});
  expect(login.ok()).toBeTruthy();
  const admin = {Authorization: `Bearer ${(await login.json()).accessToken}`};
  const created = await request.post(`${api}/api/v1/ventures`, {headers: admin, data: {
    name: identity, scale: "S", riskTier: "T1", riskTierRationale: "個人情報を扱わず、人が最終判断する",
    conditions: {RAG: "対象外", Agent: "対象外"}
  }});
  expect(created.ok()).toBeTruthy();
  const vid = (await created.json()).id;

  await page.goto("/auth/sign-in");
  await page.locator("#sign-in-email").fill("admin@example.com");
  await page.locator("#sign-in-password").fill("Admin123!");
  await page.getByRole("button", {name: "サインイン", exact: true}).click();
  await expect(page).toHaveURL(/\/admin$/);
  await page.goto("/company/teams");
  await page.getByRole("button", {name: "ユーザーを招待", exact: true}).click();
  await page.locator("#invite-email").fill(email);
  await page.locator("#invite-role").selectOption("mentor");
  await page.getByRole("button", {name: "参加リンクを発行"}).click();
  const link = page.getByLabel(email, {exact: true});
  await expect(link).toHaveValue(/invitation=/);
  const invitationUrl = await link.inputValue();
  const context = await browser.newContext();
  const reviewer = await context.newPage();
  try {
    await reviewer.goto(invitationUrl);
    await expect(reviewer.locator("#sign-up-role")).toHaveCount(0);
    await expect(reviewer.locator("#sign-up-tenant-id")).toHaveCount(0);
    await reviewer.locator("#sign-up-user-id").fill(identity);
    await reviewer.locator("#sign-up-email").fill(email);
    await reviewer.locator("#sign-up-display-name").fill(identity);
    await reviewer.locator("#sign-up-password").fill("ReviewBrowser123!");
    await reviewer.getByRole("button", {name: "登録して開始"}).click();
    await expect(reviewer).toHaveURL(/\/mentor\/reviews$/);
    await page.goto(`/ventures/${vid}`);
    await page.getByRole("button", {name: "メンバー管理", exact: true}).click();
    await page.getByRole("combobox", {name: "担当者", exact: true}).selectOption(identity);
    await page.getByRole("combobox", {name: "ロール", exact: true}).selectOption("R19");
    await page.getByRole("button", {name: "要員を追加"}).click();
    await expect(page.getByRole("cell", {name: identity, exact: true})).toBeVisible();
    await reviewer.goto(new URL(`/ventures/${vid}`, invitationUrl).href);
    await reviewer.getByRole("button", {name: "案件設定", exact: true}).click();
    await reviewer.getByLabel("判定根拠のリンク").fill("https://example.test/review/risk");
    const verify = reviewer.getByRole("button", {name: "リスク判定を確認"});
    await expect(verify).toBeEnabled();
    const response = reviewer.waitForResponse(r => r.url().endsWith(`/ventures/${vid}`) && r.request().method() === "PATCH");
    await verify.click();
    expect((await response).ok()).toBeTruthy();
    const saved = await request.get(`${api}/api/v1/ventures/${vid}`, {headers: admin});
    expect((await saved.json()).governance.riskConfirmedBy).toBe(identity);
    await reviewer.screenshot({path: "test-results/review-independent-confirmation.png", fullPage: true});
  } finally {
    await context.close();
  }
});

test("assessment expiry survives UI edits, cancellation preserves history, and report downloads contain files", async ({ page, request }) => {
  const auth = await request.post(`${api}/api/v1/auth/sign-in`, {data: {email: "admin@example.com", password: "Admin123!"}});
  const admin = {Authorization: `Bearer ${(await auth.json()).accessToken}`};
  const created = await request.post(`${api}/api/v1/ventures`, {headers: admin, data: {name: `expiry-ui-${Date.now()}`, scale: "S"}});
  const vid = (await created.json()).id;
  const member = await request.post(`${api}/api/v1/ventures/${vid}/members`, {headers: admin, data: {userId: "demo-user", roleId: "R03"}});
  expect(member.ok()).toBeTruthy();
  const gap = await request.get(`${api}/api/v1/ventures/${vid}/skill-gap`, {headers: admin});
  const skill = (await gap.json()).items[0];
  const assessment = await request.post(`${api}/api/v1/ventures/${vid}/skill-assessments`, {headers: admin, data: {
    skillId: skill.skillId, userId: "demo-user", assessedLevel: 1, dueDate: "2027-01-01", evidenceUri: "https://example.test/assessment"
  }});
  expect(assessment.ok()).toBeTruthy();
  const originalId = (await assessment.json()).id;
  await page.goto("/auth/sign-in");
  await page.locator("#sign-in-email").fill("admin@example.com");
  await page.locator("#sign-in-password").fill("Admin123!");
  await page.getByRole("button", {name: "サインイン", exact: true}).click();
  await expect(page).toHaveURL(/\/admin$/);
  await page.goto(`/ventures/${vid}/skills`);
  await page.getByRole("button", {name: skill.name, exact: true}).click();
  await page.getByRole("button", {name: "評価を編集", exact: true}).click();
  await expect(page.getByLabel("評価有効期限", {exact: true})).toHaveValue("2027-01-01");
  await page.getByRole("combobox", {name: "到達Lv", exact: true}).selectOption("2");
  const saving = page.waitForResponse(r => r.url().endsWith(`/ventures/${vid}/skill-assessments`) && r.request().method() === "POST");
  await page.getByRole("button", {name: "評価を保存", exact: true}).click();
  const saved = await (await saving).json();
  expect(saved.dueDate).toBe("2027-01-01"); expect(saved.id).not.toBe(originalId);
  await page.reload();
  await page.getByRole("button", {name: skill.name, exact: true}).click();
  await page.getByRole("button", {name: "評価を編集", exact: true}).click();
  await expect(page.getByLabel("評価有効期限", {exact: true})).toHaveValue("2027-01-01");
  await page.getByRole("button", {name: "評価を取り消す", exact: true}).click();
  await page.getByLabel("取消理由", {exact: true}).fill("誤った証拠に基づく評価を取消");
  const cancelling = page.waitForResponse(r => r.url().endsWith(`/ventures/${vid}/skill-assessments`) && r.request().method() === "POST");
  await page.getByRole("dialog", {name: "評価を取り消しますか？"}).getByRole("button", {name: "評価を取り消す", exact: true}).click();
  expect((await (await cancelling).json()).revoked).toBe(true);
  const history = await request.get(`${api}/api/v1/ventures/${vid}/skill-assessments/history`, {headers: admin});
  expect((await history.json()).items).toHaveLength(3);
  await page.getByRole("button", {name: skill.name, exact: true}).click();
  await page.getByRole("button", {name: "評価履歴", exact: true}).click();
  await expect(page.getByText("誤った証拠に基づく評価を取消", {exact: true})).toBeVisible();
  await page.keyboard.press("Escape");

  await page.goto("/company/reports");
  const generation = page.waitForResponse(r => r.url().endsWith("/reports/sales-summary") && r.request().method() === "POST");
  await page.getByRole("button", {name: "提案を作成"}).click();
  const report = await (await generation).json();
  await page.reload();
  await expect(page.getByText(report.id, {exact: false}).first()).toBeVisible();
  const {readFile} = await import("node:fs/promises");
  for (const format of ["pdf", "csv"]) {
    const downloading = page.waitForEvent("download");
    await page.getByRole("button", {name: `${format.toUpperCase()}を保存`}).click();
    const download = await downloading;
    expect(download.suggestedFilename()).toBe(`${report.id}.${format}`);
    const content = await readFile((await download.path())!);
    expect(content.length).toBeGreaterThan(100);
    if (format === "pdf") expect(content.subarray(0, 5).toString()).toBe("%PDF-");
    else expect(content.toString("utf8")).toContain(report.id);
  }
});
