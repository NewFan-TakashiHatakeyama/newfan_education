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
  { value: "strong", label: "案件面談向け" },
  { value: "approved", label: "営業証跡向け" },
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
        setError(e.reason instanceof Error ? e.reason.message : "実務証跡の取得に失敗しました。");
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
          ariaLabel="企業証跡一覧"
          eyebrow="証跡一覧"
          title="待機人材の実務証跡を営業・配属判断に活用"
          lead={
            <>
              待機人材の育成演習提出物と評価履歴を一画面で横断確認。待機人材・チーム・証跡強度・レビュー種別で絞り込み、
              案件面談・営業提案・配属判断に使える実務証跡を素早く特定します。
            </>
          }
          metrics={[
            { label: "実務証跡（累計）", value: stats.total, suffix: "件" },
            { label: "案件面談向け", value: stats.strong, suffix: "件", hint: "営業・配属に使える証跡" },
            { label: "レビュー合格", value: stats.approved, suffix: "件" },
            { label: "対象待機人材", value: stats.learners, suffix: "名" }
          ]}
          actions={
            <>
              <Link href="/company/reports" className={styles.actionPrimary}>
                <IconText icon="barChart3">営業サマリーを生成</IconText>
              </Link>
              <Link href="/company/learners" className={styles.actionGhost}>
                <IconText icon="users">待機人材一覧へ</IconText>
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

      <Section title="実務証跡を絞り込む" meta="待機人材 / チーム / 証跡強度 / レビュー種別の組み合わせで、営業・配属判断に使える証跡だけを抽出できます。" theme="company" icon="funnel">
        <div style={{ display: "grid", gap: "0.7rem" }}>
          <FilterChips
            label="待機人材"
            options={learnerOptions}
            selected={learnerFilter}
            onChange={setLearnerFilter}
          />
          <FilterChips label="チーム" options={teamOptions} selected={teamFilter} onChange={setTeamFilter} />
          <FilterChips
            label="証跡強度"
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
        title={`実務証跡一覧 (${filtered.length} 件)`}
        meta="待機人材名・所属・配属準備度バッジ付き。案件面談・営業説明にそのまま使えるかを確認できます。"
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
              title="まだ実務証跡がありません"
              message="育成演習の提出とAIレビューが進むと、営業提案・配属判断に使える実務証跡が蓄積されます。"
            />
          ) : (
            <EmptyState
              icon={<AppIcon name="funnel" size={24} />}
              title="絞り込み条件に一致する実務証跡はありません"
              message="フィルタを緩めるか、別の待機人材・チームを選んで案件面談向けの証跡を探してください。"
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
                  useCaseLabel="営業・配属での活用シーン:"
                  rubricLabel="案件面談・配属で確認する観点"
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
