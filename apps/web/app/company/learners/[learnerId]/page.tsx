"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import type { EvidenceItem, LearnerSummary } from "@newfan/contracts";

import { getEvidenceItems, getLearnerDetail } from "@/lib/api";

import { PageHero } from "@/app/components/ui/PageHero";
import { Section } from "@/app/components/ui/Section";
import { EmptyState } from "@/app/components/ui/EmptyState";
import { HeroSkeleton, SkeletonRow } from "@/app/components/ui/Skeleton";
import { Tabs, type TabOption } from "@/app/components/ui/Tabs";
import { EvidenceCard } from "@/app/components/ui/EvidenceCard";
import { SkillChip, SkillChipList } from "@/app/components/ui/SkillChip";
import { normalizeReadiness } from "@/app/components/ui/ReadinessBadge";

import styles from "@/app/components/ui/ui.module.css";

type TabKey =
  | "overview"
  | "roadmap"
  | "submissions"
  | "review"
  | "evidence"
  | "fit"
  | "history";

const TABS: Array<TabOption<TabKey>> = [
  { value: "overview", label: "概要" },
  { value: "roadmap", label: "ロードマップ" },
  { value: "submissions", label: "提出物" },
  { value: "review", label: "レビュー" },
  { value: "evidence", label: "証跡" },
  { value: "fit", label: "案件適合" },
  { value: "history", label: "履歴" }
];

export default function CompanyLearnerDetailPage() {
  const params = useParams<{ learnerId: string }>();
  const [detail, setDetail] = useState<LearnerSummary | null>(null);
  const [evidence, setEvidence] = useState<EvidenceItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");

  useEffect(() => {
    if (!params.learnerId) return;
    let active = true;
    Promise.allSettled([getLearnerDetail(params.learnerId), getEvidenceItems()]).then(
      (results) => {
        if (!active) return;
        const [d, e] = results;
        if (d.status === "fulfilled") {
          setDetail(d.value);
          setError(null);
        } else {
          setError(d.reason instanceof Error ? d.reason.message : "受講者詳細の取得に失敗しました。");
        }
        if (e.status === "fulfilled") {
          setEvidence(e.value.items);
        } else {
          setEvidence([]);
        }
      }
    );
    return () => {
      active = false;
    };
  }, [params.learnerId]);

  const learnerEvidence = useMemo(() => {
    if (!detail) return [] as EvidenceItem[];
    return (evidence ?? []).filter((e) => e.learnerId === detail.id);
  }, [detail, evidence]);

  if (error && !detail) {
    return (
      <main className={styles.page}>
        <EmptyState
          icon="!"
          title="受講者詳細を取得できませんでした"
          message={`${error} 必要な権限を持つアカウントでサインインしてください。`}
          action={
            <Link href="/auth/sign-in" className={styles.actionPrimary}>
              サインインを開く
            </Link>
          }
        />
      </main>
    );
  }

  if (!detail) {
    return (
      <main className={styles.page}>
        <HeroSkeleton />
        <SkeletonRow widths={["60%", "40%", "70%"]} />
      </main>
    );
  }

  const readiness = normalizeReadiness(detail.readiness);
  const completion = (detail.roadmapCompletionRate ?? 0) / 100;
  const strongCount = learnerEvidence.filter((e) =>
    ["strong", "approved", "improved", "matched"].includes((e.strength ?? "weak") as string)
  ).length;

  return (
    <main className={styles.page}>
      <PageHero
        theme="company"
        ariaLabel="受講者詳細"
        eyebrow="受講者詳細"
        title={detail.name}
        lead={
          <>
            {detail.teamName} / 目標ロール:{" "}
            <strong>{detail.targetRole}</strong> · タブ切替で進捗・提出・レビュー・証跡・案件適合・履歴を確認できます。
          </>
        }
        readiness={readiness}
        metrics={[
          {
            label: "ロードマップ進捗",
            value: detail.roadmapCompletionRate ?? 0,
            suffix: "%",
            progress: completion,
            hint: "個別タスクは『ロードマップ』タブへ"
          },
          {
            label: "レビュー待ち",
            value: detail.pendingSubmissionCount ?? 0,
            suffix: "件",
            hint: "メンター承認待ちの提出"
          },
          {
            label: "累計証跡",
            value: learnerEvidence.length,
            suffix: "件",
            hint: `強い証跡 ${strongCount} 件`
          }
        ]}
        actions={
          <>
            <Link href="/company/learners" className={styles.actionGhost}>
              ← 一覧に戻る
            </Link>
            <Link href="/company/roadmaps" className={styles.actionGhost}>
              ロードマップを再割当
            </Link>
            <Link href="/company/reports" className={styles.actionPrimary}>
              営業サマリーを生成
            </Link>
          </>
        }
      />

      <section className={styles.section}>
        <Tabs options={TABS} selected={activeTab} onChange={setActiveTab} ariaLabel="受講者詳細タブ" />

        {activeTab === "overview" ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "0.85rem" }}>
            <div className={`${styles.kpiTile} ${styles.kpiTileAccent}`}>
              <p className={styles.kpiLabel}>目標ロール</p>
              <p style={{ margin: "0.2rem 0", fontSize: "1.1rem", fontWeight: 700, color: "#0f172a" }}>
                {detail.targetRole}
              </p>
              <p className={styles.kpiHint}>
                配属準備度: <strong>{readiness}</strong>
              </p>
            </div>
            <div className={styles.kpiTile}>
              <p className={styles.kpiLabel}>強み</p>
              <div style={{ marginTop: "0.4rem" }}>
                {(detail.strongSkills ?? []).length === 0 ? (
                  <p className="muted" style={{ margin: 0 }}>—</p>
                ) : (
                  <SkillChipList skills={detail.strongSkills ?? []} tone="strong" />
                )}
              </div>
            </div>
            <div className={styles.kpiTile}>
              <p className={styles.kpiLabel}>不足スキル</p>
              <div style={{ marginTop: "0.4rem" }}>
                {(detail.gapSkills ?? []).length === 0 ? (
                  <p className="muted" style={{ margin: 0 }}>—</p>
                ) : (
                  <SkillChipList skills={detail.gapSkills ?? []} tone="gap" />
                )}
              </div>
            </div>
          </div>
        ) : null}

        {activeTab === "roadmap" ? (
          <EmptyState
            icon="◆"
            title="ロードマップタブ"
            message="個別ロードマップ詳細はロードマップ管理画面から再割当できます。Phase 別タイムラインは受講者画面 (/learner/roadmaps/[id]) と同じトーンで提示予定。"
            action={
              <Link href="/company/roadmaps" className={styles.actionPrimary}>
                ロードマップ割当へ
              </Link>
            }
          />
        ) : null}

        {activeTab === "submissions" ? (
          <EmptyState
            icon="◌"
            title="提出物タブ"
            message="メンターレビュー画面に統合されています。提出物・実行結果はメンターレビューから確認してください。"
            action={
              <Link href="/mentor/reviews" className={styles.actionGhost}>
                メンターレビューへ
              </Link>
            }
          />
        ) : null}

        {activeTab === "review" ? (
          <EmptyState
            icon="●"
            title="レビュータブ"
            message={`AI / メンター評価の総覧は、提出単位のレビュー画面で確認できます。レビュー待ち: ${detail.pendingSubmissionCount ?? 0} 件。`}
            action={
              <Link href="/mentor/reviews" className={styles.actionPrimary}>
                メンターレビューを開く
              </Link>
            }
          />
        ) : null}

        {activeTab === "evidence" ? (
          learnerEvidence.length === 0 ? (
            <EmptyState
              icon="✶"
              title="この受講者の証跡はまだありません"
              message="課題提出と AI レビューが進むと証跡が積み上がります。"
            />
          ) : (
            <div className={styles.evidenceGrid}>
              {learnerEvidence.map((e) => (
                <EvidenceCard key={e.id} evidence={e} />
              ))}
            </div>
          )
        ) : null}

        {activeTab === "fit" ? (
          <EmptyState
            icon="◆"
            title="案件適合タブ"
            message="登録済み案件要件との適合度評価は、案件要件画面から個別に実行してください。"
            action={
              <Link href="/company/requirements" className={styles.actionPrimary}>
                案件要件画面へ
              </Link>
            }
          />
        ) : null}

        {activeTab === "history" ? (
          <div style={{ display: "grid", gap: "0.5rem" }}>
            <p className={styles.fieldHelp} style={{ margin: 0 }}>
              主要イベントの履歴 (最新順)。レビュー結果・再提出・割当変更を確認できます。
            </p>
            {learnerEvidence.length === 0 ? (
              <EmptyState
                icon="◌"
                title="履歴はまだありません"
                message="提出・レビュー・割当が行われると、ここに時系列で記録されます。"
              />
            ) : (
              <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "0.5rem" }}>
                {learnerEvidence.slice(0, 6).map((e) => (
                  <li
                    key={e.id}
                    style={{
                      border: "1px solid var(--border)",
                      borderRadius: 14,
                      padding: "0.7rem 0.9rem",
                      background: "var(--surface)",
                      display: "flex",
                      gap: "0.7rem",
                      alignItems: "center",
                      flexWrap: "wrap"
                    }}
                  >
                    <span className={styles.evidenceMetaLabel}>
                      {e.updatedAt ? new Date(e.updatedAt).toISOString().slice(0, 10) : "—"}
                    </span>
                    <strong style={{ fontSize: 13 }}>{e.title}</strong>
                    <SkillChip label={e.strength ?? "—"} />
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : null}
      </section>
    </main>
  );
}
