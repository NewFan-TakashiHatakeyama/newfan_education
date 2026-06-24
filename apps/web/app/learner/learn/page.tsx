"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import type {
  DashboardSummary,
  EvidenceItem,
  EvidenceStrength,
  NotificationItem
} from "@newfan/contracts";

import { getDashboard, getEvidenceItems, getNotifications } from "@/lib/api";
import { getDemoAuthSession } from "@/lib/auth";

import { LearnerHero } from "@/app/components/learner/LearnerHero";
import { LearnerSection } from "@/app/components/learner/Section";
import { LearnerEmptyState } from "@/app/components/learner/EmptyState";
import { EvidenceCardSkeleton, HeroSkeleton } from "@/app/components/learner/Skeleton";
import { EvidenceCard } from "@/app/components/learner/EvidenceCard";
import { EnterpriseCurriculumTimeline } from "@/app/components/learner/EnterpriseCurriculumTimeline";
import { AppIcon, IconText } from "@/app/components/ui/Icon";
import {
  deriveReadiness,
  type ReadinessLevel
} from "@/app/components/learner/ReadinessBadge";
import { SkillChipList } from "@/app/components/learner/SkillChip";
import { StatusPill } from "@/app/components/learner/StatusPill";

import styles from "@/app/components/ui/ui.module.css";

const STRONG_LIKE: ReadonlyArray<EvidenceStrength> = [
  "strong",
  "approved",
  "improved",
  "matched"
];

const TODAY_TASK = {
  title: "業務課題整理演習 — AI活用テーマの具体化",
  estimatedMinutes: 45,
  useCase: "自部門の業務課題をAIプロジェクト候補に落とし込む前準備として、課題・KPI・制約を整理する場面",
  rubricFocus: ["業務課題の具体性", "KPI設計", "ガバナンス観点"],
  exerciseId: "ex-python-api-001"
};

export default function LearnerLearnPage() {
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [evidence, setEvidence] = useState<EvidenceItem[] | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [evidenceLoading, setEvidenceLoading] = useState(true);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [notificationsLoading, setNotificationsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getDashboard()
      .then((value) => {
        if (active) setDashboard(value);
      })
      .catch(() => {
        if (active) setDashboard(null);
      })
      .finally(() => {
        if (active) setDashboardLoading(false);
      });
    getEvidenceItems()
      .then((value) => {
        if (active) setEvidence(value.items);
      })
      .catch(() => {
        if (active) setEvidence([]);
      })
      .finally(() => {
        if (active) setEvidenceLoading(false);
      });
    getNotifications()
      .then((value) => {
        if (active) setNotifications(value.items.slice(0, 4));
      })
      .catch(() => {
        if (active) setNotifications([]);
      })
      .finally(() => {
        if (active) setNotificationsLoading(false);
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

  const counts = useMemo(() => {
    const safe = evidence ?? [];
    const strongOrApprovedCount = safe.filter((it) => {
      const s = it.strength ?? null;
      return s === "strong" || s === "approved" || s === "matched";
    }).length;
    const standardOrStrongerCount = safe.filter((it) => {
      const s = it.strength ?? null;
      return s === "standard" || STRONG_LIKE.includes(s as EvidenceStrength);
    }).length;
    return { strongOrApprovedCount, standardOrStrongerCount };
  }, [evidence]);

  const readiness: ReadinessLevel = deriveReadiness({
    completionRate: dashboard?.completionRate ?? 0,
    strongOrApprovedCount: counts.strongOrApprovedCount,
    standardOrStrongerCount: counts.standardOrStrongerCount,
    totalEvidence: evidence?.length ?? 0
  });

  const completionPercent =
    dashboard?.completionRate !== undefined
      ? Math.round(dashboard.completionRate * 100)
      : null;

  const pendingReview = (evidence ?? []).filter(
    (item) => item.status === "submitted" || item.status === "resubmit"
  );

  const recentEvidence = (evidence ?? [])
    .slice()
    .sort((a, b) => {
      const ta = a.updatedAt ? Date.parse(a.updatedAt) : 0;
      const tb = b.updatedAt ? Date.parse(b.updatedAt) : 0;
      return tb - ta;
    })
    .slice(0, 3);

  const isLoading = dashboardLoading || evidenceLoading;

  return (
    <main className={styles.page}>
      {/* スクリーンリーダー向けのページ見出し */}
      <h1 style={{ position: "absolute", left: "-9999px" }}>受講者ホーム</h1>

      {isLoading ? (
        <HeroSkeleton />
      ) : (
        <LearnerHero
          eyebrow="受講者ホーム"
          title={`おかえりなさい、${learnerName} さん`}
          lead={
            <>
              本日の演習を完了し、部門・経営の判断に使える成果物を1件増やしましょう。学習完走より、
              AIプロジェクト化に必要な成果物づくりを優先して進めます。
            </>
          }
          readiness={readiness}
          metrics={[
            {
              label: "本日の育成演習",
              value: `${TODAY_TASK.estimatedMinutes}分`,
              hint: TODAY_TASK.title
            },
            {
              label: "ロードマップ進捗",
              value: completionPercent !== null ? completionPercent : "—",
              suffix: completionPercent !== null ? "%" : undefined,
              progress: dashboard?.completionRate ?? 0,
              hint: `完了 ${dashboard?.completedItems ?? 0} / 全 ${dashboard?.totalItems ?? 0}`
            },
            {
              label: "成果物（累計）",
              value: evidence?.length ?? 0,
              suffix: "件",
              hint:
                pendingReview.length > 0
                  ? `レビュー待ち ${pendingReview.length} 件 — 承認待ちの成果物`
                  : "演習提出で成果物が追加されます"
            }
          ]}
          actions={
            <>
              <Link
                href={`/learner/exercises/${TODAY_TASK.exerciseId}`}
                className={styles.actionPrimary}
              >
                <IconText icon="bookOpen">本日の演習を開始</IconText>
              </Link>
              <Link href="/learner/evidence" className={styles.actionGhost}>
                <IconText icon="fileCheck2">成果物を確認</IconText>
              </Link>
            </>
          }
        />
      )}

      <LearnerSection
        title="12週間 Enterprise カリキュラム"
        meta="業務課題定義からAIプロジェクト提案まで、各週の成果物を順に積み上げます。"
        icon="calendarDays"
      >
        <EnterpriseCurriculumTimeline completionRate={dashboard?.completionRate ?? 0} />
      </LearnerSection>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1.4fr) minmax(0, 1fr)",
          gap: "1.2rem"
        }}
      >
        <LearnerSection
          title="本日の育成演習（AIプロジェクトに近づく実務）"
          meta="1演習30〜90分。再提出は減点ではなく、PoC判断で説明できる改善履歴として残します。"
          icon="bookOpen"
          actions={
            <Link
              href={`/learner/exercises/${TODAY_TASK.exerciseId}`}
              className={styles.actionPrimary}
            >
              <IconText icon="rocket">演習に着手</IconText>
            </Link>
          }
        >
          <div
            style={{
              display: "grid",
              gap: "0.85rem",
              gridTemplateColumns: "1fr"
            }}
          >
            <div>
              <p
                style={{
                  margin: 0,
                  fontSize: "1.05rem",
                  fontWeight: 700,
                  color: "#0f172a"
                }}
              >
                {TODAY_TASK.title}
              </p>
              <p
                style={{
                  margin: "0.3rem 0 0",
                  fontSize: 13,
                  color: "#475569",
                  lineHeight: 1.65
                }}
              >
                推定 {TODAY_TASK.estimatedMinutes} 分。業務課題とKPIを整理し、
                AIレビュー合格で成果物に加算します。
              </p>
            </div>
            <div className={styles.evidenceUseCase}>
              <span className={styles.evidenceUseCaseIcon} aria-hidden>
                <AppIcon name="briefcase" size={12} />
              </span>
              <span>
                <strong>業務での適用シーン:</strong> {TODAY_TASK.useCase}
              </span>
            </div>
            <div>
              <p className={styles.evidenceMetaLabel} style={{ margin: "0 0 0.4rem" }}>
                評価観点
              </p>
              <SkillChipList skills={TODAY_TASK.rubricFocus} />
            </div>
          </div>
        </LearnerSection>

        <LearnerSection
          title="レビュー待ち・再提出"
          meta="提出後24時間以内にAIレビューが返ります。合格・改善内容は成果物レポートに反映されます。"
          icon="clock3"
        >
          {evidence === null ? (
            <div className={styles.skeletonRow}>
              <div className={styles.skeletonBox} />
              <div className={styles.skeletonBox} />
            </div>
          ) : pendingReview.length === 0 ? (
            <LearnerEmptyState
              icon={<AppIcon name="checkCircle2" size={24} />}
              title="レビュー待ちはありません"
              message="提出済み演習はすべてレビュー済みです。次の育成演習で成果物を増やしましょう。"
              action={
                <Link
                  href={`/learner/exercises/${TODAY_TASK.exerciseId}`}
                  className={styles.actionGhost}
                >
                  <IconText icon="arrowRight">次の演習へ</IconText>
                </Link>
              }
            />
          ) : (
            <ul
              style={{
                listStyle: "none",
                margin: 0,
                padding: 0,
                display: "flex",
                flexDirection: "column",
                gap: "0.6rem"
              }}
            >
              {pendingReview.map((item) => (
                <li
                  key={item.id}
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: 16,
                    padding: "0.8rem 0.95rem",
                    background: "var(--surface)"
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.6rem",
                      justifyContent: "space-between"
                    }}
                  >
                    <strong style={{ fontSize: 13 }}>{item.title}</strong>
                    <StatusPill status={item.status} />
                  </div>
                  {item.submissionId ? (
                    <Link
                      href={`/learner/submissions/${item.submissionId}`}
                      className={styles.actionGhost}
                      style={{ marginTop: "0.5rem", fontSize: 12 }}
                    >
                      <IconText icon="notebookText">レビューを開く</IconText>
                    </Link>
                  ) : (
                    <p
                      style={{
                        margin: "0.4rem 0 0",
                        fontSize: 12,
                        color: "#5d667d"
                      }}
                    >
                      提出ID未確定
                    </p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </LearnerSection>
      </div>

      <LearnerSection
        title="直近の成果物"
        meta="部門・経営判断に使える成果物を新しい順に最大3件表示。一覧は成果物ページへ。"
        icon="fileCheck2"
        actions={
          <Link href="/learner/evidence" className={styles.actionGhost}>
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
        ) : recentEvidence.length === 0 ? (
          <LearnerEmptyState
            icon={<AppIcon name="circleDashed" size={24} />}
            title="まだ成果物がありません"
            message="演習を提出するとAIレビューと成果物レポートが自動生成されます。まず本日の演習から着手してください。"
            action={
              <Link
                href={`/learner/exercises/${TODAY_TASK.exerciseId}`}
                className={styles.actionPrimary}
              >
                <IconText icon="bookOpen">本日の演習を開く</IconText>
              </Link>
            }
          />
        ) : (
          <div className={styles.evidenceGrid}>
            {recentEvidence.map((item) => (
              <EvidenceCard key={item.id} evidence={item} />
            ))}
          </div>
        )}
      </LearnerSection>

      <LearnerSection
        title="育成・レビュー通知"
        meta="ロードマップ割当・レビュー結果・教材更新など、プログラム期間の育成に関わる通知を要約表示します。"
        icon="messageSquare"
        actions={
          <Link href="/notifications" className={styles.actionGhost}>
            <IconText icon="messageSquare">通知センターを開く</IconText>
          </Link>
        }
      >
        {notificationsLoading ? (
          <div className={styles.skeletonRow}>
            <div className={styles.skeletonBox} />
            <div className={styles.skeletonBox} />
          </div>
        ) : notifications.length === 0 ? (
          <LearnerEmptyState
            icon={<AppIcon name="circleDashed" size={24} />}
            title="新しい通知はありません"
            message="ロードマップ更新・レビュー完了・教材改訂などがここに表示されます。"
          />
        ) : (
          <ul
            style={{
              listStyle: "none",
              margin: 0,
              padding: 0,
              display: "flex",
              flexDirection: "column",
              gap: "0.6rem"
            }}
          >
            {notifications.map((item) => (
              <li
                key={item.id}
                style={{
                  border: "1px solid var(--border)",
                  borderRadius: 16,
                  padding: "0.85rem 1rem",
                  background: "var(--surface)"
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                    flexWrap: "wrap"
                  }}
                >
                  <strong style={{ fontSize: 14 }}>{item.title}</strong>
                  {item.isImportant ? (
                    <span className="status-pill pill-warm">重要</span>
                  ) : null}
                </div>
                <p
                  style={{
                    margin: "0.3rem 0 0",
                    fontSize: 12.5,
                    color: "#5d667d",
                    lineHeight: 1.55
                  }}
                >
                  {item.body}
                </p>
              </li>
            ))}
          </ul>
        )}
      </LearnerSection>
    </main>
  );
}
