"use client";

import { useEffect, useState } from "react";

import { AppIcon } from "@/app/components/ui";

import styles from "./aiFieldReadyLanding.module.css";

type MockStage = 0 | 1 | 2 | 3 | 4 | 5;

const STAGE_LABELS: Array<{ label: string; sub: string }> = [
  { label: "案件要件入力", sub: "顧客の必須 / 歓迎要件を登録" },
  { label: "スキル分解", sub: "要件をタスク・スキル単位へ" },
  { label: "ロードマップ生成", sub: "受講者ごとに 3 か月計画" },
  { label: "演習提出", sub: "AI / SQL / レポート課題を提出" },
  { label: "レビュー", sub: "AI 一次評価 + メンター承認" },
  { label: "実務証跡レポート", sub: "営業提案サマリー出力" }
];

export function HeroMock({ reducedMotion }: { reducedMotion: boolean }) {
  const [cyclingStage, setCyclingStage] = useState<MockStage>(0);

  useEffect(() => {
    if (reducedMotion) {
      return;
    }
    const id = window.setInterval(() => {
      setCyclingStage((current) => ((current >= 5 ? 0 : current + 1) as MockStage));
    }, 1800);
    return () => window.clearInterval(id);
  }, [reducedMotion]);

  const stage: MockStage = reducedMotion ? 5 : cyclingStage;
  const isStageReached = (target: number) => stage >= target;
  const progressPct = ((stage + 1) / STAGE_LABELS.length) * 100;

  return (
    <div className={styles.heroMock} aria-label="案件要件から実務証跡レポートが生成されるまでの SaaS 画面イメージ">
      <div className={styles.heroMockHeader}>
        <span className={styles.heroMockDots} aria-hidden>
          <i />
          <i />
          <i />
        </span>
        <p className={styles.heroMockTitle}>
          <AppIcon name="layoutDashboard" size={14} />
          実務証跡レポート — Workspace
        </p>
        <span className={`${styles.heroMockBadge} ${stage === 5 ? styles.heroMockBadgeReady : ""}`}>
          {stage === 5 ? "Ready" : "Building..."}
        </span>
      </div>

      <div className={styles.heroMockProgress}>
        <span
          className={styles.heroMockProgressFill}
          style={{
            width: `${progressPct}%`,
            transition: reducedMotion ? "none" : undefined
          }}
        />
      </div>
      <ol className={styles.heroMockSteps}>
        {STAGE_LABELS.map((step, index) => {
          const reached = isStageReached(index);
          const isCurrent = stage === index;
          return (
            <li
              key={step.label}
              className={`${styles.heroMockStep} ${reached ? styles.heroMockStepReached : ""} ${isCurrent ? styles.heroMockStepCurrent : ""}`}
            >
              <span className={styles.heroMockStepIndex}>{index + 1}</span>
              <span className={styles.heroMockStepBody}>
                <strong>{step.label}</strong>
                <small>{step.sub}</small>
              </span>
            </li>
          );
        })}
      </ol>

      <div className={styles.heroMockBody}>
        <div className={`${styles.heroMockPane} ${isStageReached(0) ? styles.heroMockPaneOn : ""}`}>
          <p className={styles.heroMockPaneLabel}>案件A: 生成AI業務改善支援</p>
          <div className={styles.heroMockRows}>
            <div className={styles.heroMockRow}>
              <span>必須</span>
              <strong>Python / SQL / プロンプト設計</strong>
            </div>
            <div className={styles.heroMockRow}>
              <span>歓迎</span>
              <strong>RAG 評価 / OCR 検証 / PMO 補助</strong>
            </div>
            <div className={styles.heroMockRow}>
              <span>期間</span>
              <strong>3 か月以内に 2 名アサイン</strong>
            </div>
          </div>
        </div>

        <div className={`${styles.heroMockPane} ${isStageReached(1) ? styles.heroMockPaneOn : ""}`}>
          <p className={styles.heroMockPaneLabel}>スキル分解</p>
          <div className={styles.heroMockChips}>
            {["前処理", "可視化", "改善提案", "プロンプト設計", "RAG 評価"].map((chip, index) => (
              <span
                key={chip}
                className={styles.heroMockChip}
                style={reducedMotion ? undefined : { animationDelay: `${index * 80}ms` }}
              >
                {chip}
              </span>
            ))}
          </div>
        </div>

        <div className={`${styles.heroMockPane} ${isStageReached(2) ? styles.heroMockPaneOn : ""}`}>
          <p className={styles.heroMockPaneLabel}>3 か月ロードマップ（K.Y.）</p>
          <div className={styles.heroMockTimeline}>
            <span data-month="M1">業務分解 + プロンプト</span>
            <span data-month="M2">データ抽出 + 改善提案</span>
            <span data-month="M3">提案資料化 + 面談</span>
          </div>
        </div>

        <div className={`${styles.heroMockPane} ${isStageReached(3) ? styles.heroMockPaneOn : ""}`}>
          <p className={styles.heroMockPaneLabel}>演習提出</p>
          <div className={styles.heroMockSubmission}>
            <span className={styles.heroMockSubmissionTag}>
              <AppIcon name="fileCode2" size={12} />
              ex-202604-rag.ipynb
            </span>
            <span className={`${styles.heroMockStatus} ${styles.heroMockStatusInfo}`}>再提出 2</span>
          </div>
        </div>

        <div className={`${styles.heroMockPane} ${isStageReached(4) ? styles.heroMockPaneOn : ""}`}>
          <p className={styles.heroMockPaneLabel}>レビュー</p>
          <div className={styles.heroMockReview}>
            <div>
              <span>AIレビュー</span>
              <strong>正確性 82 / 再現性 78 / 報告力 85</strong>
            </div>
            <span className={`${styles.heroMockStatus} ${styles.heroMockStatusOk}`}>
              <AppIcon name="shieldCheck" size={12} />
              メンター承認
            </span>
          </div>
        </div>

        <div className={`${styles.heroMockPane} ${styles.heroMockPaneReport} ${isStageReached(5) ? styles.heroMockPaneOn : ""}`}>
          <div className={styles.heroMockReportHeader}>
            <span className={styles.heroMockReportEyebrow}>Evidence Report</span>
            <span className={styles.heroMockReportId}>EV-2026-0512</span>
          </div>
          <p className={styles.heroMockReportTitle}>K.Y. / データ分析補助 / 案件適合度 84%</p>
          <div className={styles.heroMockReportMeta}>
            <span>提案可能タスク: 3 件</span>
            <span>評価: B+</span>
            <span>改善: 3 件</span>
          </div>
          <div className={styles.heroMockReportCtaRow}>
            <span className={styles.heroMockReportCta}>営業提案サマリーへ出力</span>
            <AppIcon name="arrowRight" size={14} />
          </div>
        </div>
      </div>
    </div>
  );
}
