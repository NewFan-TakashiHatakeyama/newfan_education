"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import type { EvidenceItem, EvidenceStatus, EvidenceStrength } from "@newfan/contracts";

import { getEvidenceItems, getDashboard, getSkillsGap } from "@/lib/api";
import { getDemoAuthSession } from "@/lib/auth";

import { LearnerHero } from "@/app/components/learner/LearnerHero";
import { LearnerSection } from "@/app/components/learner/Section";
import { FilterChips, type FilterOption } from "@/app/components/learner/FilterChips";
import { EvidenceCard } from "@/app/components/learner/EvidenceCard";
import { LearnerEmptyState } from "@/app/components/learner/EmptyState";
import { EvidenceCardSkeleton, HeroSkeleton } from "@/app/components/learner/Skeleton";
import { deriveReadiness, type ReadinessLevel } from "@/app/components/learner/ReadinessBadge";
import { AppIcon, IconText } from "@/app/components/ui/Icon";

import pageStyles from "@/app/components/ui/ui.module.css";

type SkillFilter = "all" | string;
type StrengthFilter = "all" | "strong-only" | "approved" | "improved" | "weak";
type StatusFilter = "all" | "passed" | "submitted" | "completed";

const STRENGTH_FILTERS: Array<FilterOption<StrengthFilter>> = [
  { value: "all", label: "すべて" },
  { value: "strong-only", label: "PoC判断向け" },
  { value: "approved", label: "レビュー合格" },
  { value: "improved", label: "改善履歴あり" },
  { value: "weak", label: "要改善" }
];

const STATUS_FILTERS: Array<FilterOption<StatusFilter>> = [
  { value: "all", label: "すべての状態" },
  { value: "passed", label: "合格" },
  { value: "submitted", label: "レビュー待ち" },
  { value: "completed", label: "教材完了" }
];

const STRONG_LIKE: ReadonlyArray<EvidenceStrength> = [
  "strong",
  "approved",
  "improved",
  "matched"
];

function matchStrength(item: EvidenceItem, filter: StrengthFilter): boolean {
  if (filter === "all") return true;
  const strength = item.strength ?? null;
  if (filter === "strong-only") {
    return strength === "strong";
  }
  if (filter === "approved") {
    return strength === "approved" || strength === "matched";
  }
  if (filter === "improved") {
    return strength === "improved";
  }
  if (filter === "weak") {
    return strength === "weak" || strength === "standard" || strength === null;
  }
  return true;
}

function matchStatus(item: EvidenceItem, filter: StatusFilter): boolean {
  if (filter === "all") return true;
  const status = item.status ?? null;
  if (filter === "passed") {
    return status === "passed" || status === "approved";
  }
  if (filter === "submitted") {
    return status === "submitted" || status === "resubmit";
  }
  if (filter === "completed") {
    return status === "completed";
  }
  return true;
}

function matchSkill(item: EvidenceItem, filter: SkillFilter): boolean {
  if (filter === "all") return true;
  return item.skillTags.some((tag) => tag === filter);
}

export default function LearnerEvidencePage() {
  const [items, setItems] = useState<EvidenceItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [completionRate, setCompletionRate] = useState<number | null>(null);
  const [targetSkillsCount, setTargetSkillsCount] = useState<number | null>(null);
  const [targetRole, setTargetRole] = useState<string>("AI/DX 推進");

  const [skillFilter, setSkillFilter] = useState<SkillFilter>("all");
  const [strengthFilter, setStrengthFilter] = useState<StrengthFilter>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  useEffect(() => {
    let active = true;
    getEvidenceItems()
      .then((result) => {
        if (active) {
          setItems(result.items);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setItems([]);
          setError(err instanceof Error ? err.message : "成果物の読み込みに失敗しました。");
        }
      });
    getDashboard()
      .then((value) => {
        if (active) setCompletionRate(value.completionRate);
      })
      .catch(() => {
        if (active) setCompletionRate(null);
      });
    getSkillsGap()
      .then((summary) => {
        if (active) {
          setTargetSkillsCount(summary.items.length);
          if (summary.targetRole) {
            setTargetRole(summary.targetRole);
          }
        }
      })
      .catch(() => {
        if (active) setTargetSkillsCount(null);
      });
    return () => {
      active = false;
    };
  }, []);

  const learnerName = useMemo(() => {
    if (typeof window === "undefined") return "受講者";
    const session = getDemoAuthSession();
    return session.displayName || session.userId || "受講者";
  }, []);

  const isLoading = items === null;

  const counts = useMemo(() => {
    const safe = items ?? [];
    const strongCount = safe.filter((it) =>
      STRONG_LIKE.includes((it.strength ?? "weak") as EvidenceStrength)
    ).length;
    const approvedCount = safe.filter(
      (it) => it.status === "approved" || it.status === "passed"
    ).length;
    const standardOrStrongerCount = safe.filter((it) => {
      const s = it.strength ?? null;
      return s === "standard" || STRONG_LIKE.includes(s as EvidenceStrength);
    }).length;
    const strongOrApprovedCount = safe.filter((it) => {
      const s = it.strength ?? null;
      return s === "strong" || s === "approved" || s === "matched";
    }).length;
    return { strongCount, approvedCount, standardOrStrongerCount, strongOrApprovedCount };
  }, [items]);

  const skillOptions: Array<FilterOption<SkillFilter>> = useMemo(() => {
    const skills = new Map<string, number>();
    (items ?? []).forEach((item) => {
      item.skillTags.forEach((tag) => {
        skills.set(tag, (skills.get(tag) ?? 0) + 1);
      });
    });
    const list: Array<FilterOption<SkillFilter>> = [
      { value: "all", label: "すべて", count: items?.length ?? 0 }
    ];
    Array.from(skills.entries())
      .sort((a, b) => b[1] - a[1])
      .forEach(([tag, count]) => list.push({ value: tag, label: tag, count }));
    return list;
  }, [items]);

  const filtered = useMemo(() => {
    return (items ?? []).filter(
      (item) =>
        matchSkill(item, skillFilter) &&
        matchStrength(item, strengthFilter) &&
        matchStatus(item, statusFilter)
    );
  }, [items, skillFilter, strengthFilter, statusFilter]);

  const readiness: ReadinessLevel = deriveReadiness({
    completionRate: completionRate ?? 0,
    strongOrApprovedCount: counts.strongOrApprovedCount,
    standardOrStrongerCount: counts.standardOrStrongerCount,
    totalEvidence: items?.length ?? 0
  });

  const completionPercent = completionRate !== null ? Math.round(completionRate * 100) : null;

  return (
    <main className={pageStyles.page}>
      {isLoading ? (
        <HeroSkeleton />
      ) : (
        <LearnerHero
          eyebrow="成果物"
          title={`${learnerName} さんの成果物`}
          lead={
            <>
              部門・経営の判断に使える提出物と評価履歴を一覧しています。AIレビュー／メンター承認／AIプロジェクト適合の状況を
              確認し、足りないスキルや改善の経緯も見える化します。
            </>
          }
          readiness={readiness}
          metrics={[
            {
              label: "育成ロール",
              value: targetRole,
              hint:
                targetSkillsCount !== null
                  ? `AIプロジェクトに必要なスキル ${targetSkillsCount} 項目`
                  : "ロードマップに紐づくスキルを評価中"
            },
            {
              label: "ロードマップ進捗",
              value: completionPercent !== null ? completionPercent : "—",
              suffix: completionPercent !== null ? "%" : undefined,
              progress: completionRate ?? 0,
              hint:
                completionRate === null
                  ? "ダッシュボードの取得に失敗しました"
                  : "育成演習の完了と提出で成果物を増やしていきます"
            },
            {
              label: "成果物（累計）",
              value: items?.length ?? 0,
              suffix: "件",
              hint: `PoC判断向け ${counts.strongCount} 件 / レビュー合格 ${counts.approvedCount} 件`
            }
          ]}
          actions={
            <>
              <Link href="/learner/learn" className={pageStyles.actionPrimary}>
                <IconText icon="layoutDashboard">受講者ホームへ</IconText>
              </Link>
              <Link href="/learner/exercises/ex-python-api-001" className={pageStyles.actionGhost}>
                <IconText icon="bookOpen">本日の演習を開始</IconText>
              </Link>
            </>
          }
        />
      )}

      {error ? (
        <div className={pageStyles.section} role="alert">
          <p className="muted" style={{ margin: 0 }}>
            成果物の読み込み中にエラーが発生しました: {error}
            <br />
            空状態またはサンプルとして以下の内容を表示しています。
          </p>
        </div>
      ) : null}

      <LearnerSection
        title="成果物を絞り込む"
        meta="スキル／成果物強度／状態の組み合わせで、PoC判断・部門提案に使える成果物だけを抽出できます。"
        icon="funnel"
      >
        <div style={{ display: "grid", gap: "0.7rem" }}>
          <FilterChips
            label="スキル別"
            options={skillOptions}
            selected={skillFilter}
            onChange={setSkillFilter}
          />
          <FilterChips
            label="成果物強度"
            options={STRENGTH_FILTERS}
            selected={strengthFilter}
            onChange={setStrengthFilter}
          />
          <FilterChips
            label="状態"
            options={STATUS_FILTERS}
            selected={statusFilter}
            onChange={setStatusFilter}
          />
        </div>
      </LearnerSection>

      <LearnerSection
        title={`成果物一覧 (${filtered.length} 件)`}
        meta="育成責任者・部門リーダーにそのまま共有できる形式か、PoC判断で説明できる内容かを確認できます。"
        icon="fileCheck2"
      >
        {isLoading ? (
          <div className={pageStyles.evidenceGrid}>
            <EvidenceCardSkeleton />
            <EvidenceCardSkeleton />
            <EvidenceCardSkeleton />
          </div>
        ) : filtered.length === 0 ? (
          (items?.length ?? 0) === 0 ? (
            <LearnerEmptyState
              icon={<AppIcon name="circleDashed" size={24} />}
              title="まだ成果物がありません"
              message="育成演習を提出するとAIレビューと成果物レポートが自動生成されます。まず本日の演習から着手してください。"
              action={
                <Link href="/learner/learn" className={pageStyles.actionPrimary}>
                  <IconText icon="layoutDashboard">受講者ホームへ</IconText>
                </Link>
              }
            />
          ) : (
            <LearnerEmptyState
              icon={<AppIcon name="funnel" size={24} />}
              title="絞り込み条件に一致する成果物はありません"
              message="フィルタを緩めるか、別のスキルタグを選んでPoC判断向けの成果物を探してください。"
              action={
                <button
                  type="button"
                  className={pageStyles.actionGhost}
                  onClick={() => {
                    setSkillFilter("all");
                    setStrengthFilter("all");
                    setStatusFilter("all");
                  }}
                >
                  フィルタをリセット
                </button>
              }
            />
          )
        ) : (
          <div className={pageStyles.evidenceGrid}>
            {filtered.map((item) => (
              <EvidenceCard
                key={item.id}
                evidence={item}
                useCaseLabel="業務での適用シーン:"
                rubricLabel="評価観点"
              />
            ))}
          </div>
        )}
      </LearnerSection>
    </main>
  );
}
