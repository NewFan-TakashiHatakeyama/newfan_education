"use client";

import Image from "next/image";
import Link from "next/link";
import type { CurriculumVersion } from "@newfan/contracts";
import styles from "./LearningTemplate.module.css";

const PARTNER_LOGOS = [
  "/images/companies/airbnb.svg",
  "/images/companies/google.svg",
  "/images/companies/microsoft.svg",
  "/images/companies/hubspot.svg",
  "/images/companies/fedex.svg",
  "/images/companies/walmart.svg"
];

type LearningCardItem = {
  id: string;
  title: string;
  curriculumSlug: string;
  versionLabel: string;
  difficultyLabel: string;
  estimatedLabel: string;
  lessonSlug: string;
};

export function toLearningCards(items: CurriculumVersion[]): LearningCardItem[] {
  return items.map((item) => {
    const fallbackLesson =
      item.curriculumSlug === "python-basic" ? "variables-v1" : "lesson";
    return {
      id: item.id,
      title: item.title,
      curriculumSlug: item.curriculumSlug,
      versionLabel: `v${item.version}`,
      difficultyLabel:
        item.difficulty !== undefined ? `難易度 ${item.difficulty}` : "難易度 未設定",
      estimatedLabel:
        item.estimatedMinutes !== undefined
          ? `${item.estimatedMinutes}分`
          : "所要時間 未設定",
      lessonSlug: fallbackLesson
    };
  });
}

export function LearningHero() {
  return (
    <section className={styles.hero}>
      <div className={styles.heroGrid}>
        <div>
          <span className={styles.heroBadge}>Template style learning</span>
          <h1 className={styles.heroTitle}>Learn Engineering from Top Experts</h1>
          <p className={styles.heroLead}>
            テンプレートのヒーロー構成を学習カリキュラム向けに転用し、検索導線と学習の価値訴求を集約しています。
          </p>
          <div className={styles.searchWrap}>
            <input
              className={styles.searchInput}
              placeholder="Search engineering courses..."
              aria-label="学習カリキュラム検索"
            />
            <button className={styles.searchButton} type="button">
              Search
            </button>
          </div>
          <ul className={styles.heroPoints}>
            <li>Flexible Schedules</li>
            <li>Guided Learning Paths</li>
            <li>Peer Support Community</li>
          </ul>
        </div>
        <div className={styles.heroImageWrap}>
          <Image
            src="/images/banner/mahila.webp"
            width={1000}
            height={805}
            className={styles.heroImage}
            alt="Learning visual"
            priority
          />
        </div>
      </div>
    </section>
  );
}

export function LearningPartnerStrip() {
  return (
    <section className={styles.sectionCard}>
      <div className={styles.sectionHeader}>
        <h2 className={styles.sectionTitle}>Trusted by companies of all sizes</h2>
        <p className={styles.muted}>Template Companies section adaptation</p>
      </div>
      <div className={styles.partnerRow}>
        {PARTNER_LOGOS.map((src) => (
          <div className={styles.partnerCard} key={src}>
            <Image src={src} alt={src} width={116} height={36} />
          </div>
        ))}
      </div>
    </section>
  );
}

export function LearningCurriculumCards({ items }: { items: LearningCardItem[] }) {
  return (
    <section className={styles.sectionCard}>
      <div className={styles.sectionHeader}>
        <h2 className={styles.sectionTitle}>Popular courses</h2>
        <Link href="/learn" className={styles.cardAction}>
          Browse All Courses &gt;
        </Link>
      </div>
      <div className={styles.curriculumGrid}>
        {items.map((item) => (
          <article key={item.id} className={styles.curriculumCard}>
            <div className={styles.pillRow}>
              <span className={styles.pill}>{item.versionLabel}</span>
              <span className={styles.pill}>{item.difficultyLabel}</span>
              <span className={styles.pill}>{item.estimatedLabel}</span>
            </div>
            <h3 className={styles.cardTitle}>{item.title}</h3>
            <p className={styles.cardMeta}>{item.curriculumSlug}</p>
            <Link
              href={`/learn/${item.curriculumSlug}/${item.lessonSlug}`}
              className={styles.cardAction}
            >
              Start learning
            </Link>
          </article>
        ))}
      </div>
    </section>
  );
}

export function LearningEmptyState({ message }: { message: string }) {
  return (
    <section className={styles.sectionCard}>
      <h2 className={styles.sectionTitle}>Learning content is unavailable</h2>
      <p className={styles.muted}>{message}</p>
    </section>
  );
}

