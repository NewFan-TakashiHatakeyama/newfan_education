"use client";

import { AppIcon } from "@/app/components/ui";

import styles from "./aiFieldReadyLanding.module.css";
import { LP_TRUST_SECTION } from "./lpContent";

export function TrustSection() {
  return (
    <div className={styles.trustWrap}>
      <div className={styles.trustIntro}>
        <p className={styles.trustEyebrow}>Why Field-Ready</p>
        <p>{LP_TRUST_SECTION.body}</p>
      </div>
      <ul className={styles.trustList}>
        {LP_TRUST_SECTION.pillars.map((pillar) => (
          <li key={pillar} className={styles.trustListItem}>
            <span className={styles.trustListIcon}>
              <AppIcon name="checkCircle2" size={14} />
            </span>
            <span>{pillar}</span>
          </li>
        ))}
      </ul>
      <p className={styles.trustNote}>{LP_TRUST_SECTION.note}</p>
    </div>
  );
}
