"use client";

import { AppIcon } from "@/app/components/ui";

import styles from "./aiFieldReadyLanding.module.css";
import { LP_SCENARIO } from "./lpContent";

export function ScenarioTimeline() {
  return (
    <div className={styles.scenarioGrid}>
      {LP_SCENARIO.months.map((month, index) => (
        <article key={month.label} className={styles.scenarioCard}>
          <header className={styles.scenarioCardHead}>
            <span className={styles.scenarioPhase}>{month.label}</span>
            <span className={styles.scenarioIndex}>STEP {index + 1} / {LP_SCENARIO.months.length}</span>
          </header>
          <h3>{month.title}</h3>
          <div className={styles.scenarioBlock}>
            <p className={styles.scenarioBlockLabel}>
              <AppIcon name="clipboardCheck" size={14} />
              実施内容
            </p>
            <ul>
              {month.activities.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className={styles.scenarioBlock}>
            <p className={styles.scenarioBlockLabel}>
              <AppIcon name="fileCheck2" size={14} />
              成果物
            </p>
            <ul className={styles.scenarioDeliverables}>
              {month.deliverables.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </article>
      ))}
    </div>
  );
}
