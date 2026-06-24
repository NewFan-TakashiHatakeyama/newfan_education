import { expect, test, type Page } from "@playwright/test";

async function setupB2BMockApi(page: Page) {
  const submissions: Array<{ id: string; learnerId: string; status: string; exerciseId: string; code: string; createdAt: string }> = [];
  const requirements = [
    {
      id: "req-demo-001",
      title: "FAQ RAG検証支援",
      description: "顧客提案向けPoC要件",
      requiredSkills: ["Python", "RAG", "評価"]
    }
  ];

  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());
    const path = url.pathname;
    let body: Record<string, unknown> = {};
    try {
      body = (request.postDataJSON() as Record<string, unknown>) ?? {};
    } catch {
      body = {};
    }

    const baseHeaders = {
      "access-control-allow-origin": "*",
      "access-control-allow-methods": "GET,POST,PATCH,DELETE,OPTIONS",
      "access-control-allow-headers": "*"
    };

    const json = (value: unknown, status = 200) =>
      route.fulfill({
        status,
        contentType: "application/json",
        headers: baseHeaders,
        body: JSON.stringify(value)
      });

    if (method === "OPTIONS") {
      return route.fulfill({ status: 204, headers: baseHeaders });
    }

    if (method === "GET" && path === "/api/v1/companies/current") {
      return json({ id: "company-demo", name: "デモ事業会社", plan: "enterprise" });
    }
    if (method === "GET" && path === "/api/v1/dashboard") {
      return json({
        completionRate: 0.25,
        completedItems: 3,
        totalItems: 12
      });
    }
    if (method === "GET" && path === "/api/v1/skills/gap") {
      return json({
        targetRole: "AI/DX 推進",
        items: [{ skill: "RAG", current: 2, target: 4, gap: 2, evidenceCount: 1 }]
      });
    }
    if (method === "GET" && path === "/api/v1/notifications") {
      return json({ userId: "e2e-user", unreadCount: 0, items: [] });
    }
    if (method === "GET" && path === "/api/v1/messages/threads") {
      return json({ userId: "e2e-user", threads: [] });
    }
    if (method === "GET" && path === "/api/v1/learners") {
      return json({
        items: [
          {
            id: "learner-demo-001",
            name: "田中 一郎",
            teamName: "DX推進チーム",
            targetRole: "RAG検証補助",
            roadmapCompletionRate: 62,
            readiness: "Almost"
          }
        ]
      });
    }
    if (method === "GET" && path === "/api/v1/learners/learner-demo-001") {
      return json({
        id: "learner-demo-001",
        name: "田中 一郎",
        teamName: "DX推進チーム",
        targetRole: "RAG検証補助",
        roadmapCompletionRate: 62,
        readiness: "Almost",
        pendingSubmissionCount: 1,
        strongSkills: ["Python"],
        gapSkills: ["SQL"]
      });
    }
    if (method === "GET" && path === "/api/v1/role-templates") {
      return json({
        items: [
          { id: "role-rag", code: "rag_assistant", name: "RAG検証補助", description: "RAG実務", targetSkills: ["Python", "RAG"] }
        ]
      });
    }
    if (method === "POST" && path === "/api/v1/roadmaps/assign") {
      return json({ roadmapId: "roadmap-001", status: "assigned" });
    }
    if (method === "GET" && path === "/api/v1/requirements") {
      return json({ items: requirements });
    }
    if (method === "POST" && path === "/api/v1/requirements") {
      const created = {
        id: `req-${requirements.length + 1}`,
        title: String(body?.title ?? "new"),
        description: String(body?.description ?? ""),
        requiredSkills: Array.isArray(body?.requiredSkills) ? body.requiredSkills : []
      };
      requirements.push(created);
      return json(created);
    }
    if (method === "GET" && path === "/api/v1/evidence") {
      return json({ items: [{ id: "evidence-001", learnerId: "learner-demo-001", title: "RAG検証", summary: "改善提案", skillTags: ["RAG"] }] });
    }
    if (method === "POST" && path === "/api/v1/reports/sales-summary") {
      return json({ id: "report-001", title: "AIプロジェクト候補レポート", summary: "受講者はRAG評価タスクを完了しています。" });
    }
    if (method === "GET" && path === "/api/v1/exercises/ex-python-api-001") {
      return json({
        id: "ex-python-api-001",
        kind: "notebook",
        title: "Python API演習",
        prompt: "辞書一覧からnameを連結する関数を作成してください。",
        starterCode: "def solve(items):\n    return ''\n",
        metadata: { language: "python" }
      });
    }
    if (method === "POST" && path === "/api/v1/exercises/ex-python-api-001/run") {
      return json({
        status: "passed",
        stdout: "Executed ex-python-api-001: passed",
        stderr: "",
        engine: "pyodide",
        pipeline: "notebook",
        details: {}
      });
    }
    if (method === "POST" && path === "/api/v1/exercises/ex-python-api-001/submit") {
      const created = {
        id: "submission-001",
        learnerId: "learner-demo-001",
        exerciseId: "ex-python-api-001",
        status: "submitted",
        code: String(body?.code ?? ""),
        createdAt: new Date().toISOString()
      };
      submissions.push(created);
      return json(created);
    }
    if (method === "GET" && path === "/api/v1/submissions") {
      return json({ items: submissions });
    }
    if (method === "GET" && path === "/api/v1/submissions/submission-001") {
      return json(submissions[0]);
    }
    if (method === "POST" && path === "/api/v1/submissions/submission-001/ai-review") {
      return json({ submissionId: "submission-001", reviewerType: "ai", status: "pass_with_comment", score: 78, comments: "良好です。" });
    }
    if (method === "POST" && path === "/api/v1/submissions/submission-001/mentor-review") {
      return json({ submissionId: "submission-001", reviewerType: "mentor", status: "approved", score: 85, comments: "承認しました。" });
    }
    if (method === "GET" && path === "/api/v1/notifications/settings") {
      return json({ userId: "e2e-user", items: [] });
    }
    if (method === "PATCH" && path.startsWith("/api/v1/notifications/settings/")) {
      return json({ category: "learning", emailEnabled: false, inAppEnabled: true, pushEnabled: false, updatedAt: new Date().toISOString() });
    }
    return json({ detail: "not mocked" }, 404);
  });
}

test("B2B must flow works on revised routes", async ({ page }) => {
  await setupB2BMockApi(page);
  await page.addInitScript(() => {
    window.localStorage.setItem(
      "newfan.auth.session-cache",
      JSON.stringify({
        accessToken: "e2e-demo-token",
        tokenType: "bearer",
        expiresIn: 3600,
        userId: "admin-user",
        displayName: "Admin User",
        role: "admin",
        state: "active",
        tenantId: "company-demo"
      })
    );
  });

  await page.goto("/company/dashboard");
  await expect(page.getByLabel("企業ダッシュボード")).toBeVisible();

  await page.goto("/company/learners");
  await expect(page.getByRole("heading", { name: /育成進捗.*一覧で確認/ })).toBeVisible();

  await page.goto("/company/roadmaps");
  await expect(page.getByRole("heading", { name: /育成ロードマップ/ })).toBeVisible();

  await page.goto("/learner/learn");
  await expect(page.getByRole("heading", { name: "受講者ホーム" })).toBeAttached();
  await expect(page.getByRole("heading", { name: "12週間 Enterprise カリキュラム" })).toBeVisible();

  await page.goto("/mentor/reviews");
  await expect(page.getByLabel("メンターレビュー")).toBeVisible();

  await page.goto("/company/reports");
  await expect(page.getByLabel("AIプロジェクト候補")).toBeVisible();
});
