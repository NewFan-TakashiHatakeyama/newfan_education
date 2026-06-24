import Link from "next/link";
import type { ReactNode } from "react";
import styles from "./LearningTemplate.module.css";

export type LessonTocItem = {
  slug: string;
  title: string;
  kind: "reading" | "code";
};

export type LearningLessonExperienceProps = {
  courseSlug: string;
  lessonSlug: string;
  // Course-aware mode: the full ordered lesson list for the table of contents.
  // Empty for the enterprise single-MDX fallback.
  lessons: LessonTocItem[];
  title: string;
  body: string | null;
  kind: "reading" | "code";
  exerciseId?: string;
  skillTags: string[];
  estimatedMinutes?: number;
  section?: string;
  // Enterprise single-MDX extras.
  week?: number;
  phase?: string;
  deliverable?: string;
};

function renderMarkdownBody(body: string) {
  const lines = body.split("\n");
  const nodes: ReactNode[] = [];
  let listItems: string[] = [];

  const flushList = () => {
    if (listItems.length === 0) return;
    nodes.push(
      <ul key={`list-${nodes.length}`} className={styles.tocList}>
        {listItems.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    );
    listItems = [];
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      flushList();
      continue;
    }
    if (trimmed.startsWith("# ")) {
      flushList();
      nodes.push(
        <h2 key={`h-${nodes.length}`} className={styles.sectionTitle}>
          {trimmed.slice(2)}
        </h2>
      );
      continue;
    }
    if (trimmed.startsWith("## ")) {
      flushList();
      nodes.push(
        <h3 key={`h3-${nodes.length}`} style={{ margin: "0.9rem 0 0.35rem", fontSize: "1rem" }}>
          {trimmed.slice(3)}
        </h3>
      );
      continue;
    }
    if (trimmed.startsWith("- ")) {
      listItems.push(trimmed.slice(2));
      continue;
    }
    flushList();
    nodes.push(
      <p key={`p-${nodes.length}`} style={{ margin: "0.45rem 0", lineHeight: 1.8 }}>
        {trimmed}
      </p>
    );
  }
  flushList();
  return nodes;
}

export function LearningLessonExperience(props: LearningLessonExperienceProps) {
  const {
    courseSlug,
    lessonSlug,
    lessons,
    title,
    body,
    kind,
    exerciseId,
    skillTags,
    estimatedMinutes,
    section,
    week,
    phase,
    deliverable
  } = props;

  const isCourseMode = lessons.length > 0;
  const currentIndex = lessons.findIndex((lesson) => lesson.slug === lessonSlug);
  const prevLesson = currentIndex > 0 ? lessons[currentIndex - 1] : null;
  const nextLesson =
    currentIndex >= 0 && currentIndex < lessons.length - 1 ? lessons[currentIndex + 1] : null;

  // Enterprise fallback builds its TOC from the body's "## " headings.
  const headingToc = body
    ? body
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line.startsWith("## "))
        .map((line) => line.slice(3))
    : [];

  return (
    <div className={styles.learningShell}>
      <section className={styles.sectionCard}>
        <div className={styles.sectionHeader}>
          <h1 className={styles.sectionTitle}>{title}</h1>
          <p className={styles.muted}>
            {isCourseMode ? `コース: ${courseSlug}` : `curriculum: ${courseSlug}`}
            {section ? ` · ${section}` : ""}
            {week ? ` · Week ${week}` : ""}
            {phase ? ` · ${phase}` : ""}
            {isCourseMode ? ` · ${kind === "code" ? "コード演習" : "解説"}` : ""}
          </p>
          <p className={styles.muted} style={{ marginTop: "0.35rem" }}>
            想定学習時間: {estimatedMinutes ?? "—"} 分
            {deliverable ? ` · 成果物: ${deliverable}` : ""}
          </p>
        </div>
        <div className={styles.lessonLayout}>
          <aside className={styles.panel}>
            <h2 className={styles.sectionTitle}>目次</h2>
            {isCourseMode ? (
              <ol className={styles.tocList}>
                {lessons.map((lesson) => {
                  const active = lesson.slug === lessonSlug;
                  return (
                    <li key={lesson.slug}>
                      <Link
                        href={`/learn/${courseSlug}/${lesson.slug}`}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "0.4rem",
                          textDecoration: "none",
                          color: active ? "#1a21bc" : "#475569",
                          fontWeight: active ? 700 : 400
                        }}
                      >
                        <span
                          aria-hidden
                          style={{
                            fontSize: "0.65rem",
                            border: "1px solid #dde5ff",
                            borderRadius: 6,
                            padding: "0 4px",
                            color: lesson.kind === "code" ? "#6556ff" : "#2563eb"
                          }}
                        >
                          {lesson.kind === "code" ? "演習" : "解説"}
                        </span>
                        {lesson.title}
                      </Link>
                    </li>
                  );
                })}
              </ol>
            ) : headingToc.length > 0 ? (
              <ol className={styles.tocList}>
                {headingToc.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ol>
            ) : (
              <p className={styles.muted}>教材の目次を読み込めませんでした。</p>
            )}
            {skillTags.length ? (
              <>
                <h2 className={styles.sectionTitle} style={{ marginTop: "1rem" }}>
                  スキルタグ
                </h2>
                <ul className={styles.tocList}>
                  {skillTags.map((tag) => (
                    <li key={tag}>{tag}</li>
                  ))}
                </ul>
              </>
            ) : null}
          </aside>

          <section className={styles.panel}>
            <h2 className={styles.sectionTitle}>教材本文</h2>
            <div className={styles.contentBody}>
              {body ? (
                renderMarkdownBody(body)
              ) : (
                <p>
                  指定されたカリキュラム（{courseSlug}）の MDX 教材が見つかりませんでした。
                  管理者が教材を公開しているか、スラッグを確認してください。
                </p>
              )}
            </div>
            <div className={styles.actionRow}>
              {kind === "code" && exerciseId ? (
                <Link href={`/learner/exercises/${exerciseId}`} className={styles.actionButton}>
                  演習へ進む
                </Link>
              ) : nextLesson ? (
                <Link href={`/learn/${courseSlug}/${nextLesson.slug}`} className={styles.actionButton}>
                  次のレッスンへ
                </Link>
              ) : (
                <Link
                  href={`/learn/${courseSlug}/${lessonSlug}/exercise`}
                  className={styles.actionButton}
                >
                  演習へ進む
                </Link>
              )}
              {prevLesson ? (
                <Link
                  href={`/learn/${courseSlug}/${prevLesson.slug}`}
                  className={`${styles.actionButton} ${styles.actionSecondary}`}
                >
                  前のレッスン
                </Link>
              ) : null}
              {nextLesson && kind === "code" ? (
                <Link
                  href={`/learn/${courseSlug}/${nextLesson.slug}`}
                  className={`${styles.actionButton} ${styles.actionSecondary}`}
                >
                  次のレッスン
                </Link>
              ) : null}
              <Link href="/courses" className={`${styles.actionButton} ${styles.actionSecondary}`}>
                コース一覧へ
              </Link>
            </div>
          </section>

          <aside className={styles.panel}>
            <h2 className={styles.sectionTitle}>AIガイド</h2>
            <ul className={styles.tocList}>
              {kind === "code" ? (
                <>
                  <li>まず課題の入出力例を確認する</li>
                  <li>境界条件（空・欠損）を1ケース試す</li>
                  <li>実行して出力を確認し、提出する</li>
                  <li>AIレビュー結果を次の改善に活かす</li>
                </>
              ) : (
                <>
                  <li>業務のどの課題に使えるかをメモする</li>
                  <li>用語は手を動かす前に整理する</li>
                  <li>次の演習で実際にコードに落とす</li>
                  <li>つまずいたら前のレッスンに戻る</li>
                </>
              )}
            </ul>
          </aside>
        </div>
      </section>
    </div>
  );
}
