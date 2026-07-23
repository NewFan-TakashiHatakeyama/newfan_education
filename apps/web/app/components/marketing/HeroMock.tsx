"use client";

import { useEffect, useState } from "react";

import { AppIcon } from "@/app/components/ui";

import styles from "./aiFieldReadyLanding.module.css";

type MockStage = 0 | 1 | 2 | 3;

const FLOW_STEPS: Array<{ label: string; detail: string }> = [
  { label: "業務課題", detail: "自社業務の課題・KPIを定義" },
  { label: "AIテーマ", detail: "適用テーマを選定" },
  { label: "PoC計画", detail: "成功条件・評価指標を設計" },
  { label: "成果物", detail: "AIプロジェクト提案書" }
];

export function HeroMock({ reducedMotion }: { reducedMotion: boolean }) {
  const [cyclingStage, setCyclingStage] = useState<MockStage>(0);

  useEffect(() => {
    if (reducedMotion) return;
    const id = window.setInterval(() => {
      setCyclingStage((current) => ((current >= 3 ? 0 : current + 1) as MockStage));
    }, 2200);
    return () => window.clearInterval(id);
  }, [reducedMotion]);

  const stage: MockStage = reducedMotion ? 3 : cyclingStage;
  const progressPct = ((stage + 1) / FLOW_STEPS.length) * 100;

  return (
    <div className={styles.heroFlow} aria-label="業務課題から成果物までの流れ">
      <div className={styles.heroFlowHeader}>
        <p className={styles.heroFlowTitle}>
          <AppIcon name="layoutDashboard" size={14} />
          課題 → 成果物
        </p>
        <span className={`${styles.heroFlowBadge} ${stage === 3 ? styles.heroFlowBadgeReady : ""}`}>
          {stage === 3 ? "Ready" : "進行中"}
        </span>
      </div>

      <div className={styles.heroFlowProgress} aria-hidden>
        <span
          className={styles.heroFlowProgressFill}
          style={{ width: `${progressPct}%`, transition: reducedMotion ? "none" : undefined }}
        />
      </div>

      <ol className={styles.heroFlowSteps}>
        {FLOW_STEPS.map((step, index) => {
          const reached = stage >= index;
          const isCurrent = stage === index;
          return (
            <li
              key={step.label}
              className={`${styles.heroFlowStep} ${reached ? styles.heroFlowStepReached : ""} ${isCurrent ? styles.heroFlowStepCurrent : ""}`}
            >
              <span className={styles.heroFlowStepIndex}>{index + 1}</span>
              <span className={styles.heroFlowStepBody}>
                <strong>{step.label}</strong>
                <small>{step.detail}</small>
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
