"use client";

import { useEffect, useMemo, useState } from "react";

import type {
  CourseCategory,
  CourseSort,
  CourseSummary
} from "@newfan/contracts";

import { getCourseCategories, getCourseTrending, getCourses } from "@/lib/api";
import { LearnerHero } from "@/app/components/learner/LearnerHero";
import { AppIcon } from "@/app/components/ui/Icon";

import { CourseCard } from "./CourseCard";
import styles from "./Courses.module.css";
import uiStyles from "@/app/components/ui/ui.module.css";

const SORT_OPTIONS: { value: CourseSort; label: string }[] = [
  { value: "popular", label: "人気順" },
  { value: "newest", label: "新着順" },
  { value: "rating", label: "評価順" }
];

export function CourseCatalog() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [sort, setSort] = useState<CourseSort>("popular");

  const [courses, setCourses] = useState<CourseSummary[] | null>(null);
  const [categories, setCategories] = useState<CourseCategory[]>([]);
  const [trending, setTrending] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Debounce the free-text query so we don't fetch on every keystroke.
  useEffect(() => {
    const handle = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(handle);
  }, [query]);

  useEffect(() => {
    let active = true;
    Promise.all([getCourseCategories(), getCourseTrending()])
      .then(([categoryResult, trendingResult]) => {
        if (!active) return;
        setCategories(categoryResult.items);
        setTrending(trendingResult.items);
      })
      .catch(() => {
        if (active) {
          setCategories([]);
          setTrending([]);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    getCourses({
      q: debouncedQuery || undefined,
      category: category ?? undefined,
      sort
    })
      .then((result) => {
        if (!active) return;
        setCourses(result.items);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setCourses([]);
        setError(err instanceof Error ? err.message : "コースの取得に失敗しました。");
      });
    return () => {
      active = false;
    };
  }, [debouncedQuery, category, sort]);

  const resultLabel = useMemo(() => {
    if (courses === null) return "読み込み中…";
    return `${courses.length} 件のコース`;
  }, [courses]);

  return (
    <main className={uiStyles.page}>
      <LearnerHero
        eyebrow="コースを探す"
        title="AI講座カタログ"
        lead={
          <>
            動画ではなく、各レッスンで実際にコードを書いて学ぶハンズオン型の講座です。
            目的に合うコースを選び、演習を提出して実務スキルを積み上げましょう。
          </>
        }
      />

      <div className={styles.catalog}>
        <div className={styles.searchBar}>
          <AppIcon name="search" size={18} />
          <input
            className={styles.searchInput}
            placeholder="AI講座をキーワードで検索（例: RAG, FastAPI, SQL）"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            aria-label="コース検索"
          />
        </div>

        {trending.length > 0 ? (
          <div className={styles.trendingRow}>
            <span className={styles.trendingLabel}>
              <AppIcon name="rocket" size={14} />
              急上昇
            </span>
            {trending.map((term) => (
              <button
                key={term}
                type="button"
                className={styles.chip}
                onClick={() => setQuery(term)}
              >
                {term}
              </button>
            ))}
          </div>
        ) : null}

        <div className={styles.chipRow}>
          <button
            type="button"
            className={`${styles.chip} ${category === null ? styles.chipActive : ""}`}
            onClick={() => setCategory(null)}
          >
            すべて
          </button>
          {categories.map((item) => (
            <button
              key={item.category}
              type="button"
              className={`${styles.chip} ${category === item.category ? styles.chipActive : ""}`}
              onClick={() => setCategory(item.category)}
            >
              {item.category}（{item.courseCount}）
            </button>
          ))}
        </div>

        <div className={styles.toolbar}>
          <span className={styles.resultCount}>{resultLabel}</span>
          <select
            className={styles.sortSelect}
            value={sort}
            onChange={(event) => setSort(event.target.value as CourseSort)}
            aria-label="並び替え"
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {error ? (
          <div className={styles.emptyState} role="alert">
            {error}
          </div>
        ) : courses === null ? (
          <div className={styles.grid}>
            <div className={styles.skeletonCard} />
            <div className={styles.skeletonCard} />
            <div className={styles.skeletonCard} />
          </div>
        ) : courses.length === 0 ? (
          <div className={styles.emptyState}>
            <p style={{ margin: 0, fontWeight: 600 }}>該当するコースが見つかりませんでした。</p>
            <p style={{ margin: "0.4rem 0 0", fontSize: "0.85rem" }}>
              キーワードやカテゴリの条件を変えてお試しください。
            </p>
          </div>
        ) : (
          <div className={styles.grid}>
            {courses.map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
