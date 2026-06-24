"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import type { CourseDetail } from "@newfan/contracts";

import { getCourse } from "@/lib/api";
import { AppIcon } from "@/app/components/ui/Icon";

import styles from "./Courses.module.css";
import uiStyles from "@/app/components/ui/ui.module.css";

const LEVEL_LABEL: Record<CourseDetail["level"], string> = {
  beginner: "入門",
  intermediate: "中級",
  advanced: "実践"
};

function formatHours(minutes: number): string {
  const hours = minutes / 60;
  if (hours >= 1) {
    return `${hours % 1 === 0 ? hours : hours.toFixed(1)}時間`;
  }
  return `${minutes}分`;
}

export function CourseDetailView({ courseSlug }: { courseSlug: string }) {
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openSections, setOpenSections] = useState<Set<number>>(new Set([0]));

  useEffect(() => {
    let active = true;
    getCourse(courseSlug)
      .then((result) => {
        if (!active) return;
        setCourse(result);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "コースの取得に失敗しました。");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [courseSlug]);

  if (loading) {
    return (
      <main className={uiStyles.page}>
        <div className={styles.skeletonCard} style={{ height: 120 }} />
        <div className={styles.skeletonCard} style={{ height: 320 }} />
      </main>
    );
  }

  if (!course) {
    return (
      <main className={uiStyles.page}>
        <div className={styles.emptyState}>
          <p style={{ margin: 0, fontWeight: 600 }}>コースが見つかりませんでした。</p>
          <p style={{ margin: "0.4rem 0 0.9rem", fontSize: "0.85rem" }}>
            {error ?? "URL を確認するか、カタログから選び直してください。"}
          </p>
          <Link href="/courses" className={uiStyles.actionPrimary}>
            コース一覧へ戻る
          </Link>
        </div>
      </main>
    );
  }

  const firstLesson = course.sections[0]?.lessons[0];

  const toggleSection = (index: number) => {
    setOpenSections((current) => {
      const next = new Set(current);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  return (
    <main className={uiStyles.page}>
      <nav className={styles.breadcrumb} aria-label="パンくず">
        <Link href="/courses">コースを探す</Link>
        <AppIcon name="arrowRight" size={12} />
        <span>{course.category}</span>
        <AppIcon name="arrowRight" size={12} />
        <span>{course.title}</span>
      </nav>

      <h1 className={styles.detailTitle}>{course.title}</h1>
      <p className={styles.detailSubtitle}>{course.subtitle}</p>
      <div className={styles.detailMetaRow}>
        <span className={styles.cardRating}>
          <AppIcon name="sparkles" size={14} className={styles.star} />
          <span className={styles.ratingValue}>{course.rating.toFixed(1)}</span>
          <span className={styles.ratingCount}>（{course.ratingCount.toLocaleString()}件）</span>
        </span>
        <span className={styles.metaItem}>
          <AppIcon name="users" size={14} />
          {course.enrolledCount.toLocaleString()} 受講
        </span>
        <span className={styles.metaItem}>
          <AppIcon name="graduationCap" size={14} />
          講師: {course.instructor}
        </span>
        <span className={styles.levelTag}>{LEVEL_LABEL[course.level]}</span>
      </div>

      <div className={styles.detailGrid} style={{ marginTop: "1.1rem" }}>
        <div className={styles.mainCol}>
          <section className={uiStyles.section}>
            <h2 className={uiStyles.sectionTitle}>このコースで学べること</h2>
            <div className={styles.outcomesGrid} style={{ marginTop: "0.7rem" }}>
              {course.outcomes.map((outcome) => (
                <div key={outcome} className={styles.outcomeItem}>
                  <AppIcon name="checkCircle2" size={16} className={styles.outcomeCheck} />
                  <span>{outcome}</span>
                </div>
              ))}
            </div>
          </section>

          <section>
            <h2 className={uiStyles.sectionTitle} style={{ marginBottom: "0.6rem" }}>
              カリキュラム{" "}
              <span style={{ fontSize: "0.8rem", color: "#94a3b8", fontWeight: 500 }}>
                {course.sections.length} セクション ・ {course.totalLessons} レッスン ・{" "}
                {formatHours(course.estimatedMinutes)}
              </span>
            </h2>
            <div className={styles.accordion}>
              {course.sections.map((section, index) => {
                const open = openSections.has(index);
                return (
                  <div key={`${section.title}-${index}`}>
                    <button
                      type="button"
                      className={styles.sectionHead}
                      onClick={() => toggleSection(index)}
                      aria-expanded={open}
                    >
                      <span className={styles.sectionHeadLeft}>
                        <span
                          aria-hidden
                          style={{
                            display: "inline-flex",
                            transition: "transform 0.15s ease",
                            transform: open ? "rotate(90deg)" : "rotate(0deg)"
                          }}
                        >
                          <AppIcon name="arrowRight" size={14} />
                        </span>
                        {index + 1}. {section.title}
                      </span>
                      <span className={styles.sectionHeadMeta}>
                        {section.lessonCount} レッスン ・ {formatHours(section.estimatedMinutes)}
                      </span>
                    </button>
                    {open
                      ? section.lessons.map((lesson) => (
                          <div key={lesson.lessonSlug} className={styles.lessonRow}>
                            <AppIcon
                              name={lesson.kind === "code" ? "fileCode2" : "bookOpen"}
                              size={15}
                              className={
                                lesson.kind === "code"
                                  ? styles.lessonIconCode
                                  : styles.lessonIconReading
                              }
                            />
                            <span className={styles.lessonTitle}>{lesson.title}</span>
                            {lesson.isPreview ? (
                              <span className={styles.previewTag}>プレビュー</span>
                            ) : null}
                            <span className={styles.lessonMin}>{lesson.estimatedMinutes}分</span>
                          </div>
                        ))
                      : null}
                  </div>
                );
              })}
            </div>
          </section>

          <section className={uiStyles.section}>
            <h2 className={uiStyles.sectionTitle}>このコースの説明</h2>
            <p style={{ margin: "0.6rem 0 0", fontSize: "0.9rem", lineHeight: 1.75, color: "#334155" }}>
              {course.description}
            </p>
            {course.prerequisites.length > 0 ? (
              <p style={{ margin: "0.8rem 0 0", fontSize: "0.85rem", color: "#475569" }}>
                <strong>前提条件:</strong> {course.prerequisites.join(" / ")}
              </p>
            ) : null}
            {course.targetAudience.length > 0 ? (
              <p style={{ margin: "0.4rem 0 0", fontSize: "0.85rem", color: "#475569" }}>
                <strong>対象者:</strong> {course.targetAudience.join(" / ")}
              </p>
            ) : null}
          </section>
        </div>

        <aside className={styles.sideCol}>
          <div className={styles.enrollCard}>
            <span className={styles.enrollBadge}>
              <AppIcon name="fileCode2" size={13} />
              コードを書いて学ぶ
            </span>
            {firstLesson ? (
              <Link
                href={`/learn/${course.slug}/${firstLesson.lessonSlug}`}
                className={uiStyles.actionPrimary}
                style={{ justifyContent: "center" }}
              >
                このコースを開始
              </Link>
            ) : (
              <button type="button" className={uiStyles.actionPrimary} disabled>
                準備中
              </button>
            )}
            <div className={styles.metaList}>
              <div className={styles.metaListRow}>
                <span>レッスン</span>
                <span className={styles.metaListValue}>{course.totalLessons}</span>
              </div>
              <div className={styles.metaListRow}>
                <span>コード演習</span>
                <span className={styles.metaListValue}>{course.totalExercises}</span>
              </div>
              <div className={styles.metaListRow}>
                <span>推定時間</span>
                <span className={styles.metaListValue}>{formatHours(course.estimatedMinutes)}</span>
              </div>
              <div className={styles.metaListRow}>
                <span>レベル</span>
                <span className={styles.metaListValue}>{LEVEL_LABEL[course.level]}</span>
              </div>
              <div className={styles.metaListRow}>
                <span>修了証</span>
                <span className={styles.metaListValue}>あり</span>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </main>
  );
}
