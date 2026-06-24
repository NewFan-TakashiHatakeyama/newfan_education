"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import type { LearnerSummary, Submission } from "@newfan/contracts";

import { getLearners, getSubmissions } from "@/lib/api";

import { PageHero } from "@/app/components/ui/PageHero";
import { Section } from "@/app/components/ui/Section";
import { EmptyState } from "@/app/components/ui/EmptyState";
import { SkeletonRow } from "@/app/components/ui/Skeleton";
import { FilterChips, type FilterOption } from "@/app/components/ui/FilterChips";
import { StatusPill } from "@/app/components/ui/StatusPill";
import { SkillChip } from "@/app/components/ui/SkillChip";
import { AppIcon, IconText } from "@/app/components/ui/Icon";

import styles from "@/app/components/ui/ui.module.css";

type StatusFilter = "all" | "submitted" | "needs_resubmit" | "reviewed";

const STATUS_FILTERS: Array<FilterOption<StatusFilter>> = [
  { value: "all", label: "すべて" },
  { value: "submitted", label: "レビュー待ち" },
  { value: "needs_resubmit", label: "差戻し" },
  { value: "reviewed", label: "AI評価済" }
];

function statusToBadge(status: string) {
  if (status === "reviewed") return "passed" as const;
  if (status === "needs_resubmit") return "resubmit" as const;
  if (status === "approved") return "approved" as const;
  return "submitted" as const;
}

function timeAgo(iso: string | null | undefined): string {
  if (!iso) return "—";
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return "—";
  const diffMs = Date.now() - t;
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;
  if (diffMs < minute) return "たった今";
  if (diffMs < hour) return `${Math.round(diffMs / minute)}分前`;
  if (diffMs < day) return `${Math.round(diffMs / hour)}時間前`;
  if (diffMs < 30 * day) return `${Math.round(diffMs / day)}日前`;
  return iso.slice(0, 10);
}

export default function MentorReviewsPage() {
  const [submissions, setSubmissions] = useState<Submission[] | null>(null);
  const [learners, setLearners] = useState<LearnerSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  useEffect(() => {
    let active = true;
    Promise.allSettled([getSubmissions(), getLearners()]).then((results) => {
      if (!active) return;
      const [s, l] = results;
      if (s.status === "fulfilled") {
        setSubmissions(s.value.items);
        setError(null);
      } else {
        setSubmissions([]);
        setError(
          s.reason instanceof Error
            ? s.reason.message
            : "育成演習提出の取得に失敗しました。mentor / admin ロールでサインインしてください。"
        );
      }
      if (l.status === "fulfilled") setLearners(l.value.items);
    });
    return () => {
      active = false;
    };
  }, []);

  const learnerName = useMemo(() => {
    const map = new Map<string, LearnerSummary>();
    learners.forEach((l) => map.set(l.id, l));
    return map;
  }, [learners]);

  const filtered = useMemo(() => {
    return (submissions ?? []).filter((s) => {
      if (statusFilter === "all") return true;
      return s.status === statusFilter;
    });
  }, [submissions, statusFilter]);

  const stats = useMemo(() => {
    const safe = submissions ?? [];
    return {
      total: safe.length,
      pending: safe.filter((s) => s.status === "submitted").length,
      resubmit: safe.filter((s) => s.status === "needs_resubmit").length,
      reviewed: safe.filter((s) => s.status === "reviewed").length
    };
  }, [submissions]);

  const isLoading = submissions === null;

  return (
    <main className={styles.page}>
      <PageHero
        theme="mentor"
        ariaLabel="メンターレビュー"
        eyebrow="レビュー待ち"
        title="受講者の育成演習を承認し、成果物を育てる"
        lead={
          <>
            受講者の育成演習提出を確認し、AI 評価・ルーブリックスコアをもとに承認 / 差戻し / 要面談を判断します。
            メンター承認後にPoC判断・部門提案に活用でき、成果物品質の向上と教育担当の負荷軽減につながります。
          </>
        }
        metrics={[
          { label: "育成演習提出", value: stats.total, suffix: "件", hint: "レビューキュー総数" },
          { label: "レビュー待ち", value: stats.pending, suffix: "件", hint: "メンター承認待ち" },
          { label: "差戻し", value: stats.resubmit, suffix: "件", hint: "再提出依頼中" },
          { label: "AI評価済", value: stats.reviewed, suffix: "件", hint: "承認判断待ち" }
        ]}
        actions={
          <Link href="/company/dashboard" className={styles.actionGhost}>
            <IconText icon="layoutDashboard">企業ダッシュボードへ</IconText>
          </Link>
        }
      />

      {error ? (
        <div className={styles.section} role="alert">
          <p className="muted" style={{ margin: 0 }}>
            {error}
          </p>
        </div>
      ) : null}

      <Section title="絞り込み" meta="ステータスでレビューキューを切り替え。" theme="mentor" icon="funnel">
        <FilterChips
          label="ステータス"
          options={STATUS_FILTERS}
          selected={statusFilter}
          onChange={setStatusFilter}
        />
      </Section>

      <Section
        title={`レビューキュー (${filtered.length} 件)`}
        meta="提出日 / 受講者 / 育成演習 / AI 評価サマリーを一覧表示。"
        theme="mentor"
        icon="clipboardCheck"
      >
        {isLoading ? (
          <SkeletonRow widths={["80%", "65%", "70%"]} />
        ) : filtered.length === 0 ? (
          (submissions?.length ?? 0) === 0 ? (
            <EmptyState
              icon={<AppIcon name="circleDashed" size={24} />}
              title="レビュー待ちはありません"
              message="受講者の新しい育成演習提出があると、ここに表示されます。"
            />
          ) : (
            <EmptyState
              icon={<AppIcon name="funnel" size={24} />}
              title="該当する育成演習提出はありません"
              message="フィルタを変えるか『すべて』に戻してください。"
              action={
                <button
                  type="button"
                  className={styles.actionGhost}
                  onClick={() => setStatusFilter("all")}
                >
                  すべて表示
                </button>
              }
            />
          )
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
              gap: "0.95rem"
            }}
          >
            {filtered.map((s) => {
              const learner = learnerName.get(s.learnerId);
              return (
                <article
                  key={s.id}
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: 22,
                    background:
                      "linear-gradient(180deg, #ffffff 0%, #ecfeff 100%)",
                    padding: "1.05rem 1.2rem",
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.55rem",
                    boxShadow: "0 14px 30px -22px rgba(13, 148, 136, 0.35)"
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      gap: "0.5rem"
                    }}
                  >
                    <div>
                      <p style={{ margin: 0, fontSize: 11, color: "#0f766e", letterSpacing: "0.12em", textTransform: "uppercase", fontWeight: 700 }}>
                        {s.exerciseId}
                      </p>
                      <strong style={{ fontSize: 15, color: "#0f172a" }}>
                        {learner ? `${learner.name} さん` : s.learnerId}
                      </strong>
                    </div>
                    <StatusPill status={statusToBadge(s.status)} />
                  </div>

                  <p
                    style={{
                      margin: 0,
                      fontSize: 12.5,
                      color: "#334466",
                      lineHeight: 1.6
                    }}
                  >
                    提出日: {timeAgo(s.createdAt)}
                    {learner ? (
                      <>
                        {" · "}
                        所属: {learner.teamName} · 目標ロール: {learner.targetRole}
                      </>
                    ) : null}
                  </p>

                  <div
                    style={{
                      background: "#f0fdfa",
                      border: "1px solid #99f6e4",
                      borderRadius: 12,
                      padding: "0.55rem 0.75rem",
                      fontSize: 12,
                      color: "#134e4a",
                      lineHeight: 1.6
                    }}
                  >
                    <strong>推奨アクション:</strong>{" "}
                    {s.status === "submitted"
                      ? "AI 評価とルーブリックを確認 → 承認 / 差戻し / 要面談を判断"
                      : s.status === "needs_resubmit"
                      ? "差戻し理由を明示。改善履歴として成果物に残ります"
                      : "AI 評価済。PoC判断向け成果物にするにはメンター承認を実施"}
                  </div>

                  <div className={styles.actionRow}>
                    <Link
                      href={`/mentor/reviews/${s.id}`}
                      className={styles.actionPrimary}
                      style={{ fontSize: 12 }}
                    >
                      <IconText icon="checkCircle2">レビューする</IconText>
                    </Link>
                    <SkillChip label={s.id} />
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </Section>
    </main>
  );
}
