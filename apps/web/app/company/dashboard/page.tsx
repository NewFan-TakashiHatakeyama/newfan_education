"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import type {
  B2BCompany,
  EvidenceItem,
  EvidenceStrength,
  LearnerSummary,
  RoleTemplate
} from "@newfan/contracts";

import {
  getCurrentCompany,
  getEvidenceItems,
  getLearners,
  getRequirements,
  getRoleTemplates
} from "@/lib/api";

import { PageHero } from "@/app/components/ui/PageHero";
import { Section } from "@/app/components/ui/Section";
import { EmptyState } from "@/app/components/ui/EmptyState";
import { EvidenceCard, EvidenceOwnerChip } from "@/app/components/ui/EvidenceCard";
import { EvidenceCardSkeleton, HeroSkeleton, SkeletonRow } from "@/app/components/ui/Skeleton";
import { AppIcon, IconText } from "@/app/components/ui/Icon";

import styles from "@/app/components/ui/ui.module.css";

const STRONG_LIKE: ReadonlyArray<EvidenceStrength> = [
  "strong",
  "approved",
  "improved",
  "matched"
];

export default function CompanyDashboardPage() {
  const [company, setCompany] = useState<B2BCompany | null>(null);
  const [learners, setLearners] = useState<LearnerSummary[] | null>(null);
  const [evidence, setEvidence] = useState<EvidenceItem[] | null>(null);
  const [requirementCount, setRequirementCount] = useState<number | null>(null);
  const [templates, setTemplates] = useState<RoleTemplate[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.allSettled([
      getCurrentCompany(),
      getLearners(),
      getEvidenceItems(),
      getRequirements(),
      getRoleTemplates()
    ]).then((results) => {
      if (!active) return;
      const [c, l, e, r, t] = results;
      if (c.status === "fulfilled") setCompany(c.value);
      if (l.status === "fulfilled") setLearners(l.value.items);
      else setLearners([]);
      if (e.status === "fulfilled") setEvidence(e.value.items);
      else setEvidence([]);
      if (r.status === "fulfilled") setRequirementCount(r.value.items.length);
      else setRequirementCount(0);
      if (t.status === "fulfilled") setTemplates(t.value.items);
      else setTemplates([]);
      const rejected = results.filter((res) => res.status === "rejected");
      if (rejected.length > 0 && learners === null) {
        setError(
          "一部のデータを取得できませんでした。必要な権限を持つアカウントでサインインして再読み込みしてください。"
        );
      }
    });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const isLoading = learners === null || evidence === null;

  const stats = useMemo(() => {
    const safeLearners = learners ?? [];
    const safeEvidence = evidence ?? [];
    const totalLearners = safeLearners.length;
    const avgCompletion =
      totalLearners === 0
        ? 0
        : Math.round(
            safeLearners.reduce(
              (sum, l) => sum + (l.roadmapCompletionRate ?? 0),
              0
            ) / totalLearners
          );
    const pendingReview = safeLearners.reduce(
      (sum, l) => sum + (l.pendingSubmissionCount ?? 0),
      0
    );
    const readyCount = safeLearners.filter((l) => l.readiness === "Ready").length;
    const almostCount = safeLearners.filter((l) => l.readiness === "Almost").length;
    const proposable = readyCount + almostCount;
    const recentEvidence = safeEvidence
      .slice()
      .sort((a, b) => {
        const ta = a.updatedAt ? Date.parse(a.updatedAt) : 0;
        const tb = b.updatedAt ? Date.parse(b.updatedAt) : 0;
        return tb - ta;
      })
      .slice(0, 3);
    const strongEvidenceCount = safeEvidence.filter((e) =>
      STRONG_LIKE.includes((e.strength ?? "weak") as EvidenceStrength)
    ).length;
    return {
      totalLearners,
      avgCompletion,
      pendingReview,
      readyCount,
      almostCount,
      proposable,
      recentEvidence,
      strongEvidenceCount
    };
  }, [learners, evidence]);

  const roleAttainment = useMemo(() => {
    const safeLearners = learners ?? [];
    const safeTemplates = templates ?? [];
    if (safeTemplates.length === 0) {
      const roles = new Map<string, { total: number; sum: number }>();
      safeLearners.forEach((l) => {
        const k = l.targetRole || "未設定";
        const cur = roles.get(k) ?? { total: 0, sum: 0 };
        cur.total += 1;
        cur.sum += l.roadmapCompletionRate ?? 0;
        roles.set(k, cur);
      });
      return Array.from(roles.entries()).map(([name, { total, sum }]) => ({
        name,
        attainment: total === 0 ? 0 : Math.round(sum / total)
      }));
    }
    return safeTemplates.map((tpl) => {
      const matched = safeLearners.filter((l) => l.targetRole === tpl.name);
      const attainment =
        matched.length === 0
          ? 0
          : Math.round(
              matched.reduce((sum, l) => sum + (l.roadmapCompletionRate ?? 0), 0) /
                matched.length
            );
      return { name: tpl.name, attainment };
    });
  }, [learners, templates]);

  const learnerNameById = useMemo(() => {
    const map = new Map<string, { name: string; team: string }>();
    (learners ?? []).forEach((l) => {
      map.set(l.id, { name: l.name, team: l.teamName });
    });
    return map;
  }, [learners]);

  return (
    <main className={styles.page}>
      {isLoading ? (
        <HeroSkeleton />
      ) : (
        <PageHero
          theme="company"
          ariaLabel="企業ダッシュボード"
          eyebrow="企業ダッシュボード"
          title={company ? `${company.name} のAI人材育成・成果物状況` : "企業ダッシュボード"}
          lead={
            <>
              受講者のロードマップ進捗・成果物の蓄積・レビュー待ち・AIテーマ診断・PoC候補化を一画面で把握します。
              部門別の業務課題登録や育成優先度の設定から始められます。
            </>
          }
          metrics={[
            {
              label: "契約プラン",
              value: company?.plan ?? "—",
              hint: company ? `契約ステータス: ${company.status}` : "未取得"
            },
            {
              label: "受講者",
              value: stats.totalLearners,
              suffix: "名",
              hint: `PoC候補可 ${stats.readyCount} / 要補強 ${stats.almostCount}`
            },
            {
              label: "ロードマップ平均進捗",
              value: stats.avgCompletion,
              suffix: "%",
              progress: stats.avgCompletion / 100,
              hint: "個人別の進捗は受講者一覧で確認"
            }
          ]}
          actions={
            <>
              <Link href="/company/learners" className={styles.actionPrimary}>
                <IconText icon="users">受講者を一覧確認</IconText>
              </Link>
              <Link href="/company/roadmaps" className={styles.actionGhost}>
                <IconText icon="map">ロードマップを割り当て</IconText>
              </Link>
              <Link href="/company/requirements" className={styles.actionGhost}>
                <IconText icon="clipboardList">業務課題を登録</IconText>
              </Link>
              <Link href="/company/reports" className={styles.actionGhost}>
                <IconText icon="barChart3">AIプロジェクト候補を生成</IconText>
              </Link>
            </>
          }
        />
      )}

      {error ? (
        <div className={styles.section} role="alert">
          <p className="muted" style={{ margin: 0 }}>
            {error}{" "}
            <Link href="/auth/sign-in" style={{ marginLeft: 4 }}>
              サインインを開く
            </Link>
          </p>
        </div>
      ) : null}

      <Section
        title="育成・プロジェクト推進の主要指標"
        meta="受講者の育成状況とAIプロジェクト判断の材料を数値で把握。PoC推進候補 = PoC着手可 + メンター伴走。"
        theme="company"
        icon="chart"
      >
        <div className={styles.kpiGrid}>
          <KpiCard label="受講者" value={stats.totalLearners} suffix="名" hint="育成対象として登録済み" />
          <KpiCard
            label="ロードマップ平均進捗"
            value={stats.avgCompletion}
            suffix="%"
            hint="個人別の進捗は受講者一覧へ"
          />
          <KpiCard
            label="レビュー待ち"
            value={stats.pendingReview}
            suffix="件"
            hint="メンター承認待ちの育成演習提出"
          />
          <KpiCard
            label="PoC推進候補"
            value={stats.proposable}
            suffix="名"
            hint={`PoC着手可 ${stats.readyCount} / メンター伴走 ${stats.almostCount}`}
          />
          <KpiCard
            label="成果物（蓄積）"
            value={evidence?.length ?? 0}
            suffix="件"
            hint={`レビュー合格の強い成果物 ${stats.strongEvidenceCount} 件`}
          />
          <KpiCard
            label="業務課題"
            value={requirementCount ?? 0}
            suffix="件"
            hint="登録するとAIテーマ適合度の評価が可能"
          />
        </div>
      </Section>

      <Section
        title="AI/DXロール別 育成到達度"
        meta="目標ロールごとのロードマップ完了率。業務課題とのギャップ把握に使います。"
        theme="company"
        icon="target"
      >
        {roleAttainment.length === 0 ? (
          <EmptyState
            icon={<AppIcon name="circleDashed" size={24} />}
            title="ロール別の育成到達度はまだ表示できません"
            message="受講者を登録しロードマップを割り当てると、目標ロール別の到達度が表示されます。"
            action={
              <Link href="/company/roadmaps" className={styles.actionPrimary}>
                <IconText icon="map">ロードマップを割り当て</IconText>
              </Link>
            }
          />
        ) : (
          <div className={styles.roleBarList}>
            {roleAttainment.map((row) => (
              <div key={row.name} className={styles.roleBarRow}>
                <span className={styles.roleBarName}>{row.name}</span>
                <div
                  className={styles.roleBarTrack}
                  role="progressbar"
                  aria-valuenow={row.attainment}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`${row.name} の育成到達度`}
                >
                  <div
                    className={styles.roleBarFill}
                    style={{ width: `${Math.max(2, row.attainment)}%` }}
                  />
                </div>
                <span className={styles.roleBarValue}>{row.attainment}%</span>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section
        title="直近の成果物"
        meta="AIプロジェクト判断に使える成果物を最新3件表示。一覧は『成果物一覧』ページから確認できます。"
        theme="company"
        icon="fileCheck2"
        actions={
          <Link href="/company/evidence" className={styles.actionGhost}>
            <IconText icon="listFilter">成果物一覧へ</IconText>
          </Link>
        }
      >
        {evidence === null ? (
          <div className={styles.evidenceGrid}>
            <EvidenceCardSkeleton />
            <EvidenceCardSkeleton />
            <EvidenceCardSkeleton />
          </div>
        ) : stats.recentEvidence.length === 0 ? (
          <EmptyState
            icon={<AppIcon name="circleDashed" size={24} />}
            title="まだ成果物がありません"
            message="演習の提出とAIレビューが進むと、AIプロジェクト判断に使える成果物が蓄積されます。"
          />
        ) : (
          <div className={styles.evidenceGrid}>
            {stats.recentEvidence.map((item) => {
              const owner = learnerNameById.get(item.learnerId);
              return (
                <EvidenceCard
                  key={item.id}
                  evidence={item}
                  ownerSlot={
                    owner ? (
                      <EvidenceOwnerChip learnerName={owner.name} teamName={owner.team} />
                    ) : (
                      <EvidenceOwnerChip learnerName={item.learnerId} />
                    )
                  }
                />
              );
            })}
          </div>
        )}
      </Section>

      <Section
        title="次のアクション"
        meta="育成優先度の設定から、AIプロジェクト候補の選定まで。"
        theme="company"
        icon="rocket"
      >
        {learners === null ? (
          <SkeletonRow widths={["60%", "40%"]} />
        ) : (
          <div className={styles.actionRow}>
            <Link href="/company/learners" className={styles.actionPrimary}>
              <IconText icon="users">受講者を招待 / 管理</IconText>
            </Link>
            <Link href="/company/roadmaps" className={styles.actionGhost}>
              <IconText icon="map">ロードマップを割り当て</IconText>
            </Link>
            <Link href="/company/requirements" className={styles.actionGhost}>
              <IconText icon="clipboardList">業務課題を登録</IconText>
            </Link>
            <Link href="/company/reports" className={styles.actionGhost}>
              <IconText icon="barChart3">AIプロジェクト候補を生成</IconText>
            </Link>
          </div>
        )}
      </Section>
    </main>
  );
}

function KpiCard({
  label,
  value,
  suffix,
  hint
}: {
  label: string;
  value: number | string;
  suffix?: string;
  hint?: string;
}) {
  return (
    <div className={`${styles.kpiTile} ${styles.kpiTileAccent}`}>
      <p className={styles.kpiLabel}>{label}</p>
      <p className={styles.kpiValue}>
        {value}
        {suffix ? <span className={styles.kpiValueSuffix}>{suffix}</span> : null}
      </p>
      {hint ? <p className={styles.kpiHint}>{hint}</p> : null}
    </div>
  );
}
