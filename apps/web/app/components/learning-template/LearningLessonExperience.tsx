import Link from "next/link";
import type { ReactNode } from "react";
import styles from "./LearningTemplate.module.css";

export type LearningLessonContent = {
  title: string;
  skillTags: string[];
  estimatedMinutes?: number;
  week?: number;
  phase?: string;
  deliverable?: string;
  body: string;
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
        <h3 key={`h3-${nodes.length}`} style={{ margin: "0.75rem 0 0.35rem", fontSize: "1rem" }}>
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
      <p key={`p-${nodes.length}`} style={{ margin: "0.35rem 0", lineHeight: 1.7 }}>
        {trimmed}
      </p>
    );
  }
  flushList();
  return nodes;
}

export function LearningLessonExperience({
  curriculumSlug,
  lessonSlug,
  content
}: {
  curriculumSlug: string;
  lessonSlug: string;
  content: LearningLessonContent | null;
}) {
  const tocItems = content?.body
    ? content.body
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line.startsWith("## "))
        .map((line) => line.slice(3))
    : [];

  return (
    <div className={styles.learningShell}>
      <section className={styles.sectionCard}>
        <div className={styles.sectionHeader}>
          <h1 className={styles.sectionTitle}>
            {content?.title ?? "Enterprise カリキュラム"}
          </h1>
          <p className={styles.muted}>
            curriculum: {curriculumSlug} / lesson: {lessonSlug}
            {content?.week ? ` · Week ${content.week}` : ""}
            {content?.phase ? ` · ${content.phase}` : ""}
          </p>
          {content ? (
            <p className={styles.muted} style={{ marginTop: "0.35rem" }}>
              想定学習時間: {content.estimatedMinutes ?? "—"} 分
              {content.deliverable ? ` · 成果物: ${content.deliverable}` : ""}
            </p>
          ) : null}
        </div>
        <div className={styles.lessonLayout}>
          <aside className={styles.panel}>
            <h2 className={styles.sectionTitle}>目次</h2>
            {tocItems.length > 0 ? (
              <ol className={styles.tocList}>
                {tocItems.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ol>
            ) : (
              <p className={styles.muted}>教材の目次を読み込めませんでした。</p>
            )}
            {content?.skillTags.length ? (
              <>
                <h2 className={styles.sectionTitle} style={{ marginTop: "1rem" }}>スキルタグ</h2>
                <ul className={styles.tocList}>
                  {content.skillTags.map((tag) => (
                    <li key={tag}>{tag}</li>
                  ))}
                </ul>
              </>
            ) : null}
          </aside>

          <section className={styles.panel}>
            <h2 className={styles.sectionTitle}>教材本文</h2>
            <div className={styles.contentBody}>
              {content ? renderMarkdownBody(content.body) : (
                <p>
                  指定されたカリキュラム（{curriculumSlug}）の MDX 教材が見つかりませんでした。
                  管理者が教材を公開しているか、スラッグを確認してください。
                </p>
              )}
            </div>
            <div className={styles.actionRow}>
              <Link
                href={`/learn/${curriculumSlug}/${lessonSlug}/exercise`}
                className={styles.actionButton}
              >
                演習へ進む
              </Link>
              <Link href="/learner/learn" className={`${styles.actionButton} ${styles.actionSecondary}`}>
                学習ホームへ
              </Link>
            </div>
          </section>

          <aside className={styles.panel}>
            <h2 className={styles.sectionTitle}>AIガイド</h2>
            <ul className={styles.tocList}>
              <li>この週の成果物を先に確認する</li>
              <li>業務課題との接続をメモする</li>
              <li>演習前に評価観点をチェック</li>
              <li>提出後は AI レビュー結果を改善に活かす</li>
            </ul>
          </aside>
        </div>
      </section>
    </div>
  );
}
