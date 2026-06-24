import Link from "next/link";

import type { CourseSummary } from "@newfan/contracts";

import { AppIcon, type AppIconName } from "@/app/components/ui/Icon";
import styles from "./Courses.module.css";

const LEVEL_LABEL: Record<CourseSummary["level"], string> = {
  beginner: "入門",
  intermediate: "中級",
  advanced: "実践"
};

export function courseThumbIcon(course: Pick<CourseSummary, "category" | "tags">): AppIconName {
  const haystack = `${course.category} ${course.tags.join(" ")}`.toLowerCase();
  if (haystack.includes("rag") || haystack.includes("llm")) return "bot";
  if (haystack.includes("api") || haystack.includes("fastapi")) return "fileCode2";
  if (haystack.includes("sql") || haystack.includes("データ")) return "barChart3";
  if (haystack.includes("ocr") || haystack.includes("文書")) return "fileSearch";
  return "sparkles";
}

function formatHours(minutes: number): string {
  const hours = minutes / 60;
  if (hours >= 1) {
    return `${hours % 1 === 0 ? hours : hours.toFixed(1)}時間`;
  }
  return `${minutes}分`;
}

export function CourseCard({ course }: { course: CourseSummary }) {
  return (
    <Link href={`/courses/${course.slug}`} className={styles.card} aria-label={course.title}>
      <div className={styles.cardThumb}>
        <AppIcon name={courseThumbIcon(course)} size={32} />
        {course.isBestseller ? (
          <span className={`${styles.cardBadge} ${styles.badgeBestseller}`}>ベストセラー</span>
        ) : course.isTopRated ? (
          <span className={`${styles.cardBadge} ${styles.badgeTopRated}`}>最高評価</span>
        ) : null}
      </div>
      <div className={styles.cardBody}>
        <p className={styles.cardTitle}>{course.title}</p>
        <p className={styles.cardInstructor}>{course.instructor}</p>
        <span className={styles.handsOn}>
          <AppIcon name="fileCode2" size={12} />
          コードを書いて学ぶ
        </span>
        <div className={styles.cardRating}>
          <AppIcon name="sparkles" size={13} className={styles.star} />
          <span className={styles.ratingValue}>{course.rating.toFixed(1)}</span>
          <span className={styles.ratingCount}>({course.ratingCount.toLocaleString()})</span>
        </div>
        <div className={styles.cardMeta}>
          <span className={styles.metaItem}>
            <AppIcon name="fileCode2" size={14} />
            {course.totalExercises} 演習
          </span>
          <span className={styles.metaItem}>
            <AppIcon name="clock3" size={14} />
            {formatHours(course.estimatedMinutes)}
          </span>
          <span className={styles.levelTag}>{LEVEL_LABEL[course.level]}</span>
        </div>
      </div>
    </Link>
  );
}
