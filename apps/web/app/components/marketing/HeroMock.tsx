"use client";

import { useEffect, useState } from "react";

import { AppIcon } from "@/app/components/ui";

import styles from "./aiFieldReadyLanding.module.css";

type MockStage = 0 | 1 | 2 | 3 | 4;

const STAGE_LABELS: Array<{ label: string; sub: string }> = [
  { label: "業務課題", sub: "課題登録" },
  { label: "AIテーマ化", sub: "活用候補" },
  { label: "データ棚卸し", sub: "必要データ" },
  { label: "PoC計画", sub: "成功条件" },
  { label: "成果物", sub: "提案書生成" }
];

export function HeroMock({ reducedMotion }: { reducedMotion: boolean }) {
  const [cyclingStage, setCyclingStage] = useState<MockStage>(0);

  useEffect(() => {
    if (reducedMotion) return;
    const id = window.setInterval(() => {
      setCyclingStage((current) => ((current >= 4 ? 0 : current + 1) as MockStage));
    }, 2000);
    return () => window.clearInterval(id);
  }, [reducedMotion]);

  const stage: MockStage = reducedMotion ? 4 : cyclingStage;
  const isStageReached = (target: number) => stage >= target;
  const progressPct = ((stage + 1) / STAGE_LABELS.length) * 100;

  return (
    <div className={styles.heroMock} aria-label="業務課題がAIテーマ・PoC計画・成果物に変換される画面イメージ">
      <div className={styles.heroMockHeader}>
        <span className={styles.heroMockDots} aria-hidden>
          <i />
          <i />
          <i />
        </span>
        <p className={styles.heroMockTitle}>
          <AppIcon name="layoutDashboard" size={14} />
          AIテーマ化ダッシュボード
        </p>
        <span className={`${styles.heroMockBadge} ${stage === 4 ? styles.heroMockBadgeReady : ""}`}>
          {stage === 4 ? "提案書Ready" : "変換中..."}
        </span>
      </div>

      <div className={styles.heroMockProgress}>
        <span
          className={styles.heroMockProgressFill}
          style={{ width: `${progressPct}%`, transition: reducedMotion ? "none" : undefined }}
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
        <div className={`${styles.heroMockPane} ${styles.heroMockPaneDense} ${isStageReached(0) ? styles.heroMockPaneOn : ""}`}>
          <p className={styles.heroMockPaneLabel}>業務課題</p>
          <div className={styles.heroMockRows}>
            <div className={styles.heroMockRow}>
              <span>部門</span>
              <strong>カスタマーサポート</strong>
            </div>
            <div className={styles.heroMockRow}>
              <span>課題</span>
              <strong>問い合わせ対応に時間がかかる</strong>
            </div>
            <div className={styles.heroMockRow}>
              <span>KPI</span>
              <strong>平均初回回答 8時間</strong>
            </div>
            <div className={styles.heroMockRow}>
              <span>制約</span>
              <strong>個人情報を含む問い合わせ</strong>
            </div>
          </div>
        </div>

        <div className={`${styles.heroMockPane} ${isStageReached(1) ? styles.heroMockPaneOn : ""}`}>
          <p className={styles.heroMockPaneLabel}>AI活用テーマ候補</p>
          <div className={styles.heroMockSkillFlow}>
            <p className={styles.heroMockSkillTask}>RAG / 社内FAQ・ナレッジ検索</p>
            <p className={styles.heroMockSkillRule}>FAQ・マニュアル・問い合わせ履歴が揃っているため推奨</p>
            <ul className={styles.heroMockSkillList}>
              {[
                ["PoC候補", "問い合わせ回答支援AI"],
                ["想定成果", "回答時間削減・品質平準化"]
              ].map(([chip, detail]) => (
                <li key={chip} className={styles.heroMockSkillItem}>
                  <span className={styles.heroMockChip}>{chip}</span>
                  <span>{detail}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className={`${styles.heroMockPane} ${isStageReached(2) ? styles.heroMockPaneOn : ""}`}>
          <p className={styles.heroMockPaneLabel}>必要データ</p>
          <div className={styles.heroMockCompactMeta}>
            <span className={styles.heroMockCompactTag}>FAQ</span>
            <span className={styles.heroMockCompactTag}>製品マニュアル</span>
            <span className={styles.heroMockCompactTag}>問い合わせ履歴</span>
          </div>
          <div className={styles.heroMockRows}>
            <div className={styles.heroMockRow}>
              <span>品質</span>
              <strong>更新頻度: 月次</strong>
            </div>
            <div className={styles.heroMockRow}>
              <span>権限</span>
              <strong>CS部門 + 情シス承認</strong>
            </div>
          </div>
        </div>

        <div className={`${styles.heroMockPane} ${isStageReached(3) ? styles.heroMockPaneOn : ""}`}>
          <p className={styles.heroMockPaneLabel}>PoC成功条件</p>
          <div className={styles.heroMockRows}>
            <div className={styles.heroMockRow}>
              <span>時間削減</span>
              <strong>回答作成時間 30% 削減</strong>
            </div>
            <div className={styles.heroMockRow}>
              <span>品質</span>
              <strong>回答根拠提示率 90%</strong>
            </div>
            <div className={styles.heroMockRow}>
              <span>期間</span>
              <strong>2か月 / 対象業務限定</strong>
            </div>
          </div>
        </div>

        <div className={`${styles.heroMockPane} ${styles.heroMockPaneReport} ${isStageReached(4) ? styles.heroMockPaneOn : ""}`}>
          <div className={styles.heroMockReportHeader}>
            <span className={styles.heroMockReportEyebrow}>AI Project Proposal</span>
            <span className={styles.heroMockReportId}>PRJ-2026-0620</span>
          </div>
          <p className={styles.heroMockReportTitle}>問い合わせ回答支援AI / カスタマーサポート</p>
          <div className={styles.heroMockReportMeta}>
            <span>PoC計画書</span>
            <span>評価レポート</span>
            <span>実装ロードマップ</span>
          </div>
          <div className={styles.heroMockReportCtaRow}>
            <span className={styles.heroMockReportCta}>AIプロジェクト提案書を生成</span>
            <AppIcon name="arrowRight" size={14} />
          </div>
        </div>
      </div>
    </div>
  );
}
