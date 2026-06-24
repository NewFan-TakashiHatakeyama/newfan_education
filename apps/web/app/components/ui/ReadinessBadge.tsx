import styles from "./ui.module.css";

export type ReadinessLevel = "Ready" | "Almost" | "Need Training" | "Not Started";

const READINESS_CLASS: Record<ReadinessLevel, string> = {
  Ready: styles.readinessReady,
  Almost: styles.readinessAlmost,
  "Need Training": styles.readinessNeed,
  "Not Started": styles.readinessNone
};

const READINESS_LABEL: Record<ReadinessLevel, string> = {
  Ready: "実務準備度: Ready",
  Almost: "実務準備度: Almost",
  "Need Training": "実務準備度: Need Training",
  "Not Started": "実務準備度: Not Started"
};

export function ReadinessBadge({ level }: { level: ReadinessLevel }) {
  return (
    <span className={`${styles.readinessBadge} ${READINESS_CLASS[level]}`}>
      <span className={styles.readinessDot} aria-hidden />
      {READINESS_LABEL[level]}
    </span>
  );
}

/**
 * Derive readiness level from completion rate and evidence/strength counts.
 * - Ready: completion ≥ 75% AND at least one approved/strong evidence
 * - Almost: completion ≥ 50% AND any standard-or-stronger evidence
 * - Need Training: completion < 50% OR only weak evidence
 * - Not Started: no evidence at all
 */
export function deriveReadiness({
  completionRate,
  strongOrApprovedCount,
  standardOrStrongerCount,
  totalEvidence
}: {
  completionRate: number;
  strongOrApprovedCount: number;
  standardOrStrongerCount: number;
  totalEvidence: number;
}): ReadinessLevel {
  if (totalEvidence === 0) {
    return "Not Started";
  }
  if (completionRate >= 0.75 && strongOrApprovedCount >= 1) {
    return "Ready";
  }
  if (completionRate >= 0.5 && standardOrStrongerCount >= 1) {
    return "Almost";
  }
  return "Need Training";
}

/**
 * Map a server-provided readiness string (e.g. "Ready", "Almost", "Need Training")
 * to the canonical ReadinessLevel. Falls back to "Not Started".
 */
export function normalizeReadiness(value: string | null | undefined): ReadinessLevel {
  if (!value) return "Not Started";
  const normalized = value.trim();
  if (normalized === "Ready") return "Ready";
  if (normalized === "Almost") return "Almost";
  if (normalized === "Need Training") return "Need Training";
  if (normalized === "Not Started") return "Not Started";
  return "Not Started";
}
