"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import type {
  EvidenceItem,
  EvidenceReviewType,
  EvidenceStrength,
  LearnerSummary
} from "@newfan/contracts";

import { getEvidenceItems, getLearners } from "@/lib/api";

import { PageHero } from "@/app/components/ui/PageHero";
import { Section } from "@/app/components/ui/Section";
import { EmptyState } from "@/app/components/ui/EmptyState";
import { EvidenceCardSkeleton, HeroSkeleton } from "@/app/components/ui/Skeleton";
import { FilterChips, type FilterOption } from "@/app/components/ui/FilterChips";
import {
  EvidenceCard,
  EvidenceOwnerChip
} from "@/app/components/ui/EvidenceCard";
import {
  ReadinessBadge,
  normalizeReadiness
} from "@/app/components/ui/ReadinessBadge";
import { AppIcon, IconText } from "@/app/components/ui/Icon";

import styles from "@/app/components/ui/ui.module.css";

type StrengthFilter = "all" | "strong" | "approved" | "improved" | "weak";
type ReviewFilter = "all" | EvidenceReviewType | "none";

const STRENGTH_FILTERS: Array<FilterOption<StrengthFilter>> = [
  { value: "all", label: "すべて" },
  { value: "strong", label: "PoC判断向け" },
  { value: "approved", label: "レビュー合格" },
  { value: "improved", label: "改善履歴あり" },
  { value: "weak", label: "要改善" }
];

const REVIEW_FILTERS: Array<FilterOption<ReviewFilter>> = [
  { value: "all", label: "すべて" },
  { value: "ai", label: "AIレビュー" },
  { value: "mentor", label: "メンター評価" },
  { value: "ai_and_mentor", label: "AI+メンター承認" },
  { value: "none", label: "未レビュー" }
];

function matchStrength(item: EvidenceItem, filter: StrengthFilter): boolean {
  if (filter === "all") return true;
  const strength = item.strength ?? null;
  if (filter === "strong") return strength === "strong";
  if (filter === "approved") return strength === "approved" || strength === "matched";
  if (filter === "improved") return strength === "improved";
  if (filter === "weak") return strength === "weak" || strength === "standard" || strength === null;
  return true;
}

function matchReview(item: EvidenceItem, filter: ReviewFilter): boolean {
  if (filter === "all") return true;
  if (filter === "none") return !item.reviewType;
  return item.reviewType === filter;
}

const STRONG_LIKE: ReadonlyArray<EvidenceStrength> = [
  "strong",
  "approved",
  "improved",
  "matched"
];

export default function CompanyEvidencePage() {
  const [items, setItems] = useState<EvidenceItem[] | null>(null);
  const [learners, setLearners] = useState<LearnerSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [learnerFilter, setLearnerFilter] = useState<string>("all");
  const [teamFilter, setTeamFilter] = useState<string>("all");
  const [strengthFilter, setStrengthFilter] = useState<StrengthFilter>("all");
  const [reviewFilter, setReviewFilter] = useState<ReviewFilter>("all");

  useEffect(() => {
    let active = true;
    Promise.allSettled([getEvidenceItems(), getLearners()]).then((results) => {
      if (!active) return;
      const [e, l] = results;
      if (e.status === "fulfilled") {
        setItems(e.value.items);
        setError(null);
      } else {
        setItems([]);
        setError(e.reason instanceof Error ? e.reason.message : "成果物の取得に失敗しました。");
      }
      if (l.status === "fulfilled") setLearners(l.value.items);
      else setLearners([]);
    });
    return () => {
      active = false;
    };
  }, []);

  const learnerById = useMemo(() => {
    const map = new Map<string, LearnerSummary>();
    learners.forEach((l) => map.set(l.id, l));
    return map;
  }, [learners]);

  const learnerOptions: Array<FilterOption<string>> = useMemo(() => {
    const counts = new Map<string, number>();
    (items ?? []).forEach((it) => {
      counts.set(it.learnerId, (counts.get(it.learnerId) ?? 0) + 1);
    });
    return [
      { value: "all", label: "すべて", count: items?.length ?? 0 },
      ...Array.from(counts.entries())
        .sort((a, b) => b[1] - a[1])
        .map(([id, count]) => ({
          value: id,
          label: learnerById.get(id)?.name ?? id,
          count
        }))
    ];
  }, [items, learnerById]);

  const teamOptions: Array<FilterOption<string>> = useMemo(() => {
    const counts = new Map<string, number>();
    (items ?? []).forEach((it) => {
      const team = learnerById.get(it.learnerId)?.teamName ?? "—";
      counts.set(team, (counts.get(team) ?? 0) + 1);
    });
    return [
      { value: "all", label: "すべて", count: items?.length ?? 0 },
      ...Array.from(counts.entries())
        .sort((a, b) => b[1] - a[1])
        .map(([team, count]) => ({ value: team, label: team, count }))
    ];
  }, [items, learnerById]);

  const filtered = useMemo(() => {
    return (items ?? []).filter((it) => {
      if (learnerFilter !== "all" && it.learnerId !== learnerFilter) return false;
      if (teamFilter !== "all") {
        const team = learnerById.get(it.learnerId)?.teamName ?? "—";
        if (team !== teamFilter) return false;
      }
      if (!matchStrength(it, strengthFilter)) return false;
      if (!matchReview(it, reviewFilter)) return false;
      return true;
    });
  }, [items, learnerFilter, teamFilter, strengthFilter, reviewFilter, learnerById]);

  const stats = useMemo(() => {
    const safe = items ?? [];
    const strong = safe.filter((e) =>
      STRONG_LIKE.includes((e.strength ?? "weak") as EvidenceStrength)
    ).length;
    const approved = safe.filter((e) => e.status === "approved" || e.status === "passed").length;
    const learnerSet = new Set(safe.map((e) => e.learnerId));
    return { total: safe.length, strong, approved, learners: learnerSet.size };
  }, [items]);

  const isLoading = items === null;

  return (
    <main className={styles.page}>
      {isLoading ? (
        <HeroSkeleton />
      ) : (
        <PageHero
          theme="company"
          ariaLabel="企業成果物一覧"
          eyebrow="成果物一覧"
          title="受講者の成果物をAIプロジェクト判断に活用"
          lead={
            <>
              受講者の演習提出物とレビュー履歴を一画面で横断確認。受講者・チーム・成果物強度・レビュー種別で絞り込み、
              PoC判断・部門提案・育成計画に使える成果物を素早く特定します。
            </>
          }
          metrics={[
            { label: "成果物（累計）", value: stats.total, suffix: "件" },
            { label: "PoC判断向け", value: stats.strong, suffix: "件", hint: "プロジェクト判断に使える成果物" },
            { label: "レビュー合格", value: stats.approved, suffix: "件" },
            { label: "対象受講者", value: stats.learners, suffix: "名" }
          ]}
          actions={
            <>
              <Link href="/company/reports" className={styles.actionPrimary}>
                <IconText icon="barChart3">AIプロジェクト候補を生成</IconText>
              </Link>
              <Link href="/company/learners" className={styles.actionGhost}>
                <IconText icon="users">受講者一覧へ</IconText>
              </Link>
            </>
          }
        />
      )}

      {error ? (
        <div className={styles.section} role="alert">
          <p className="muted" style={{ margin: 0 }}>
            {error} 必要な権限を持つアカウントでサインインしてください。
          </p>
        </div>
      ) : null}

      <Section title="成果物を絞り込む" meta="受講者 / チーム / 成果物強度 / レビュー種別の組み合わせで、プロジェクト判断に使える成果物だけを抽出できます。" theme="company" icon="funnel">
        <div style={{ display: "grid", gap: "0.7rem" }}>
          <FilterChips
            label="受講者"
            options={learnerOptions}
            selected={learnerFilter}
            onChange={setLearnerFilter}
          />
          <FilterChips label="チーム" options={teamOptions} selected={teamFilter} onChange={setTeamFilter} />
          <FilterChips
            label="成果物強度"
            options={STRENGTH_FILTERS}
            selected={strengthFilter}
            onChange={setStrengthFilter}
          />
          <FilterChips
            label="レビュー種別"
            options={REVIEW_FILTERS}
            selected={reviewFilter}
            onChange={setReviewFilter}
          />
        </div>
      </Section>

      <Section
        title={`成果物一覧 (${filtered.length} 件)`}
        meta="受講者名・所属・実務準備度バッジ付き。PoC判断・部門提案にそのまま使えるかを確認できます。"
        theme="company"
        icon="fileCheck2"
      >
        {isLoading ? (
          <div className={styles.evidenceGrid}>
            <EvidenceCardSkeleton />
            <EvidenceCardSkeleton />
            <EvidenceCardSkeleton />
          </div>
        ) : filtered.length === 0 ? (
          (items?.length ?? 0) === 0 ? (
            <EmptyState
              icon={<AppIcon name="circleDashed" size={24} />}
              title="まだ成果物がありません"
              message="演習の提出とAIレビューが進むと、AIプロジェクト判断に使える成果物が蓄積されます。"
            />
          ) : (
            <EmptyState
              icon={<AppIcon name="funnel" size={24} />}
              title="絞り込み条件に一致する成果物はありません"
              message="フィルタを緩めるか、別の受講者・チームを選んでPoC判断向けの成果物を探してください。"
              action={
                <button
                  type="button"
                  className={styles.actionGhost}
                  onClick={() => {
                    setLearnerFilter("all");
                    setTeamFilter("all");
                    setStrengthFilter("all");
                    setReviewFilter("all");
                  }}
                >
                  フィルタをリセット
                </button>
              }
            />
          )
        ) : (
          <div className={styles.evidenceGrid}>
            {filtered.map((item) => {
              const owner = learnerById.get(item.learnerId);
              return (
                <EvidenceCard
                  key={item.id}
                  evidence={item}
                  useCaseLabel="プロジェクト判断での活用シーン:"
                  rubricLabel="PoC判断・部門提案で確認する観点"
                  ownerSlot={
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        gap: "0.5rem",
                        flexWrap: "wrap"
                      }}
                    >
                      <EvidenceOwnerChip
                        learnerName={owner?.name ?? item.learnerId}
                        teamName={owner?.teamName}
                      />
                      {owner ? (
                        <ReadinessBadge level={normalizeReadiness(owner.readiness)} />
                      ) : null}
                    </div>
                  }
                />
              );
            })}
          </div>
        )}
      </Section>
    </main>
  );
}
