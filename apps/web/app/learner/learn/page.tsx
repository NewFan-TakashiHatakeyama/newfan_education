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
  title: "Python API演習 — 業務TODO API",
  estimatedMinutes: 45,
  useCase: "案件参画前の説明として、業務システム向けの簡易バックエンドAPIを実装する場面",
  rubricFocus: ["API設計", "入出力検証", "テスト分割"],
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
              本日の演習を完了し、営業・配属の説明に使える実務証跡を1件増やしましょう。学習完走より、
              案件面談で問われる成果物づくりを優先して進めます。
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
              label: "実務証跡（累計）",
              value: evidence?.length ?? 0,
              suffix: "件",
              hint:
                pendingReview.length > 0
                  ? `レビュー待ち ${pendingReview.length} 件 — 営業証跡の材料`
                  : "演習提出で実務証跡が追加されます"
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
                <IconText icon="fileCheck2">実務証跡を確認</IconText>
              </Link>
            </>
          }
        />
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1.4fr) minmax(0, 1fr)",
          gap: "1.2rem"
        }}
      >
        <LearnerSection
          title="本日の育成演習（案件に近づく実務）"
          meta="1演習30〜90分。再提出は減点ではなく、案件面談で説明できる改善履歴として残します。"
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
                推定 {TODAY_TASK.estimatedMinutes} 分。FastAPI で TODO の作成・取得・更新エンドポイントを実装し、
                AIレビュー合格で実務証跡に加算します。
              </p>
            </div>
            <div className={styles.evidenceUseCase}>
              <span className={styles.evidenceUseCaseIcon} aria-hidden>
                <AppIcon name="briefcase" size={12} />
              </span>
              <span>
                <strong>案件での想定シーン:</strong> {TODAY_TASK.useCase}
              </span>
            </div>
            <div>
              <p className={styles.evidenceMetaLabel} style={{ margin: "0 0 0.4rem" }}>
                案件面談・配属で問われる観点
              </p>
              <SkillChipList skills={TODAY_TASK.rubricFocus} />
            </div>
          </div>
        </LearnerSection>

        <LearnerSection
          title="レビュー待ち・再提出"
          meta="提出後24時間以内にAIレビューが返ります。合格・改善内容は営業証跡に反映されます。"
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
              message="提出済み演習はすべてレビュー済みです。次の育成演習で実務証跡を増やしましょう。"
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
        title="直近の実務証跡"
        meta="営業・配属判断に使える証跡を新しい順に最大3件表示。一覧は実務証跡ページへ。"
        icon="fileCheck2"
        actions={
          <Link href="/learner/evidence" className={styles.actionGhost}>
            <IconText icon="listFilter">実務証跡一覧へ</IconText>
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
            title="まだ実務証跡がありません"
            message="演習を提出するとAIレビューと実務証跡レポートが自動生成されます。まず本日の演習から着手してください。"
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
        meta="ロードマップ割当・レビュー結果・教材更新など、待機期間の育成に関わる通知を要約表示します。"
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
