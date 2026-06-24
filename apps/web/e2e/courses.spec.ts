import { expect, test, type Page } from "@playwright/test";

type Lesson = {
  lessonSlug: string;
  title: string;
  kind: "reading" | "code";
  estimatedMinutes: number;
  skillTags: string[];
  contentRef: string | null;
  exerciseId: string | null;
  isPreview: boolean;
};

function summary(overrides: Record<string, unknown>) {
  return {
    id: "course-x",
    slug: "course-x",
    title: "Course X",
    subtitle: "subtitle",
    category: "生成AI基礎",
    level: "beginner",
    instructor: "講師",
    summary: "summary",
    tags: [],
    rating: 4.5,
    ratingCount: 100,
    enrolledCount: 100,
    isBestseller: false,
    isTopRated: false,
    totalLessons: 2,
    totalExercises: 1,
    estimatedMinutes: 60,
    updatedAt: "2026-05-01T00:00:00+00:00",
    ...overrides
  };
}

const RAG = summary({
  id: "course-rag",
  slug: "rag-eval-bootcamp",
  title: "RAG評価ハンズオン入門",
  category: "LLMアプリ / RAG",
  level: "intermediate",
  tags: ["RAG", "評価", "LLM"],
  rating: 4.6,
  ratingCount: 312,
  enrolledCount: 1240,
  isBestseller: true,
  totalExercises: 2,
  estimatedMinutes: 90
});

const FASTAPI = summary({
  id: "course-fastapi",
  slug: "fastapi-business-api",
  title: "FastAPIで作る業務API",
  category: "Python API",
  tags: ["FastAPI", "Python"],
  rating: 4.4,
  ratingCount: 188,
  enrolledCount: 980
});

const ALL_COURSES = [RAG, FASTAPI];

const RAG_DETAIL = {
  ...RAG,
  description: "RAGの品質を評価する指標を実装します。",
  outcomes: ["Hit@K / MRR を実装できる", "評価レポートを作成できる"],
  targetAudience: ["LLMアプリ開発者"],
  prerequisites: ["Pythonの基礎"],
  sections: [
    {
      title: "評価の基礎",
      lessonCount: 2,
      estimatedMinutes: 33,
      lessons: [
        {
          lessonSlug: "why-evaluate-rag",
          title: "RAG評価とは何か",
          kind: "reading",
          estimatedMinutes: 8,
          skillTags: ["rag.eval"],
          contentRef: null,
          exerciseId: null,
          isPreview: true
        } satisfies Lesson,
        {
          lessonSlug: "retrieval-metrics",
          title: "検索精度を評価する",
          kind: "code",
          estimatedMinutes: 25,
          skillTags: ["rag.eval"],
          contentRef: null,
          exerciseId: "ex-rag-001",
          isPreview: false
        } satisfies Lesson
      ]
    }
  ]
};

async function setupCoursesMockApi(page: Page) {
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;

    const json = (value: unknown, status = 200) =>
      route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(value)
      });

    if (path === "/api/v1/notifications") {
      return json({ userId: "e2e-user", unreadCount: 0, items: [] });
    }
    if (path === "/api/v1/messages/threads") {
      return json({ userId: "e2e-user", threads: [] });
    }
    if (path === "/api/v1/courses/categories") {
      return json({
        items: [
          { category: "LLMアプリ / RAG", courseCount: 1 },
          { category: "Python API", courseCount: 1 }
        ]
      });
    }
    if (path === "/api/v1/courses/trending") {
      return json({ items: ["RAG", "FastAPI"] });
    }
    if (path.startsWith("/api/v1/courses/")) {
      const slug = path.replace("/api/v1/courses/", "");
      if (slug === "rag-eval-bootcamp") {
        return json(RAG_DETAIL);
      }
      return json({ detail: "Course not found" }, 404);
    }
    if (path === "/api/v1/courses") {
      const q = (url.searchParams.get("q") ?? "").toLowerCase();
      const category = url.searchParams.get("category");
      let items = ALL_COURSES;
      if (q) {
        items = items.filter((course) =>
          `${course.title} ${course.tags.join(" ")} ${course.category}`.toLowerCase().includes(q)
        );
      }
      if (category) {
        items = items.filter((course) => course.category === category);
      }
      return json({ items });
    }
    return json({ detail: "not mocked" }, 404);
  });
}

async function seedAuth(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.setItem(
      "newfan.auth.session-cache",
      JSON.stringify({
        accessToken: "e2e-token",
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

test("learner can browse the course catalog and search", async ({ page }) => {
  await setupCoursesMockApi(page);
  await seedAuth(page);

  await page.goto("/courses");

  await expect(page.getByRole("heading", { name: "AI講座カタログ" })).toBeVisible();
  await expect(page.getByText("RAG評価ハンズオン入門")).toBeVisible();
  await expect(page.getByText("FastAPIで作る業務API")).toBeVisible();

  // searching filters the grid (server-side filter is mocked)
  await page.getByLabel("コース検索").fill("RAG");
  await expect(page.getByText("RAG評価ハンズオン入門")).toBeVisible();
  await expect(page.getByText("FastAPIで作る業務API")).toHaveCount(0);
});

test("learner can open a course detail page with curriculum", async ({ page }) => {
  await setupCoursesMockApi(page);
  await seedAuth(page);

  await page.goto("/courses");
  await page.getByRole("link", { name: "RAG評価ハンズオン入門" }).click();

  await expect(page).toHaveURL(/\/courses\/rag-eval-bootcamp$/);
  await expect(page.getByRole("heading", { name: "RAG評価ハンズオン入門" })).toBeVisible();
  await expect(page.getByText("このコースで学べること")).toBeVisible();
  await expect(page.getByText("検索精度を評価する")).toBeVisible();
  await expect(page.getByRole("link", { name: "このコースを開始" })).toBeVisible();
});
