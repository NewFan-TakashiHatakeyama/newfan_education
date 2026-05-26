import { expect, test } from "@playwright/test";

const API_BASE_URL = process.env.E2E_API_BASE_URL ?? "http://127.0.0.1:8000";

test.describe("real integration api flow", () => {
  test.skip(
    process.env.REAL_INTEGRATION_E2E !== "1",
    "Set REAL_INTEGRATION_E2E=1 to run against docker services."
  );

  test("auth + exercise run/submit works with docker api", async ({ request, page, baseURL }) => {
    const health = await request.get(`${API_BASE_URL}/healthz`);
    expect(health.ok()).toBeTruthy();

    const signIn = await request.post(`${API_BASE_URL}/api/v1/auth/sign-in`, {
      data: { email: "learner@example.com", password: "Learner123!" }
    });
    expect(signIn.ok()).toBeTruthy();
    const session = await signIn.json();
    const authHeader = { Authorization: `Bearer ${session.accessToken}` };

    const exercises = await request.get(`${API_BASE_URL}/api/v1/exercises`, {
      headers: authHeader
    });
    expect(exercises.ok()).toBeTruthy();
    const exerciseItems = (await exercises.json()).items as Array<{ id: string; kind: string }>;
    const notebookExercise = exerciseItems.find((item) => item.kind === "notebook") ?? exerciseItems[0];
    expect(notebookExercise).toBeTruthy();

    const run = await request.post(`${API_BASE_URL}/api/v1/exercises/${notebookExercise.id}/run`, {
      headers: authHeader,
      data: { code: "scores=[0.7,0.9]\nprint('avg_score=0.80')" }
    });
    expect(run.ok()).toBeTruthy();
    const runBody = await run.json();
    expect(runBody.engine).toBe("pyodide");

    const submit = await request.post(`${API_BASE_URL}/api/v1/exercises/${notebookExercise.id}/submit`, {
      headers: authHeader,
      data: { code: "scores=[0.7,0.9]\nprint('avg_score=0.80')" }
    });
    expect(submit.ok()).toBeTruthy();
    const submitBody = await submit.json();
    expect(submitBody.id).toBeTruthy();

    await page.goto(baseURL ?? "http://127.0.0.1:3000");
    await expect(page.getByRole("heading", { name: "AI Field Ready", exact: true })).toBeVisible();
  });
});
