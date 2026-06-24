import fs from "node:fs/promises";
import path from "node:path";

export type CurriculumMdxModule = {
  slug: string;
  title: string;
  skillTags: string[];
  estimatedMinutes?: number;
  difficulty?: number;
  version: string;
  week?: number;
  phase?: string;
  deliverable?: string;
  body: string;
  mdxPath: string;
};

const REPO_ROOT = path.resolve(process.cwd(), "..", "..");
const ENTERPRISE_CURRICULUM_DIR = path.join(
  REPO_ROOT,
  "content/curriculum/ai-field-ready-enterprise"
);

function parseFrontmatter(raw: string): { meta: Record<string, string>; body: string } {
  const match = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  if (!match) {
    return { meta: {}, body: raw.trim() };
  }
  const meta: Record<string, string> = {};
  for (const line of match[1].split("\n")) {
    const colon = line.indexOf(":");
    if (colon === -1) continue;
    const key = line.slice(0, colon).trim();
    const value = line.slice(colon + 1).trim();
    meta[key] = value;
  }
  return { meta, body: match[2].trim() };
}

function parseSkillTags(value: string | undefined): string[] {
  if (!value) return [];
  const inner = value.replace(/^\[/, "").replace(/\]$/, "");
  return inner
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

async function parseMdxFile(filePath: string, mdxPath: string): Promise<CurriculumMdxModule | null> {
  try {
    const raw = await fs.readFile(filePath, "utf8");
    const { meta, body } = parseFrontmatter(raw);
    const slug = meta.slug?.trim();
    if (!slug) return null;
    return {
      slug,
      title: meta.title?.trim() ?? slug,
      skillTags: parseSkillTags(meta.skill_tags),
      estimatedMinutes: meta.estimated_minutes ? Number(meta.estimated_minutes) : undefined,
      difficulty: meta.difficulty ? Number(meta.difficulty) : undefined,
      version: meta.version?.trim() ?? "1.0.0",
      week: meta.week ? Number(meta.week) : undefined,
      phase: meta.phase?.trim(),
      deliverable: meta.deliverable?.trim(),
      body,
      mdxPath
    };
  } catch {
    return null;
  }
}

export async function listEnterpriseCurriculumModules(): Promise<CurriculumMdxModule[]> {
  try {
    const entries = await fs.readdir(ENTERPRISE_CURRICULUM_DIR);
    const modules: CurriculumMdxModule[] = [];
    for (const entry of entries) {
      if (!entry.endsWith(".mdx")) continue;
      const mdxPath = `content/curriculum/ai-field-ready-enterprise/${entry}`;
      const parsed = await parseMdxFile(path.join(ENTERPRISE_CURRICULUM_DIR, entry), mdxPath);
      if (parsed) modules.push(parsed);
    }
    return modules.sort((a, b) => (a.week ?? 0) - (b.week ?? 0));
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return [];
    }
    throw error;
  }
}

export async function loadEnterpriseCurriculumBySlug(slug: string): Promise<CurriculumMdxModule | null> {
  const modules = await listEnterpriseCurriculumModules();
  return modules.find((module) => module.slug === slug) ?? null;
}

// ---------------------------------------------------------------------------
// Course curriculum: a directory per course under content/curriculum/<slug>/,
// with one MDX file per lesson. Used by the course-catalog learning player.
// ---------------------------------------------------------------------------

const CURRICULUM_ROOT = path.join(REPO_ROOT, "content/curriculum");

export type CourseLessonModule = CurriculumMdxModule & {
  order: number;
  kind: "reading" | "code";
  exerciseId?: string;
  section?: string;
};

async function parseCourseLessonFile(
  filePath: string,
  mdxPath: string
): Promise<CourseLessonModule | null> {
  const base = await parseMdxFile(filePath, mdxPath);
  if (!base) return null;
  const raw = await fs.readFile(filePath, "utf8");
  const { meta } = parseFrontmatter(raw);
  const kind = meta.kind?.trim() === "code" ? "code" : "reading";
  return {
    ...base,
    order: meta.order ? Number(meta.order) : 0,
    kind,
    exerciseId: meta.exercise_id?.trim() || undefined,
    section: meta.section?.trim() || undefined
  };
}

export async function listCourseLessons(courseSlug: string): Promise<CourseLessonModule[]> {
  const dir = path.join(CURRICULUM_ROOT, courseSlug);
  try {
    const entries = await fs.readdir(dir);
    const lessons: CourseLessonModule[] = [];
    for (const entry of entries) {
      if (!entry.endsWith(".mdx")) continue;
      const mdxPath = `content/curriculum/${courseSlug}/${entry}`;
      const parsed = await parseCourseLessonFile(path.join(dir, entry), mdxPath);
      if (parsed) lessons.push(parsed);
    }
    return lessons.sort((a, b) => a.order - b.order);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return [];
    }
    throw error;
  }
}

export async function loadCourseLesson(
  courseSlug: string,
  lessonSlug: string
): Promise<CourseLessonModule | null> {
  const lessons = await listCourseLessons(courseSlug);
  return lessons.find((lesson) => lesson.slug === lessonSlug) ?? null;
}
