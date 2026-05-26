import type { EvidenceStrength } from "@newfan/contracts";

import styles from "./ui.module.css";

type StrengthLike = EvidenceStrength | null | undefined;

const STRENGTH_LABEL: Record<EvidenceStrength, string> = {
  weak: "弱い証跡",
  standard: "標準証跡",
  strong: "強い証跡",
  improved: "改善履歴付き",
  approved: "営業利用可",
  matched: "案件適合"
};

const STRENGTH_CLASS: Record<EvidenceStrength, string> = {
  weak: styles.strengthWeak,
  standard: styles.strengthStandard,
  strong: styles.strengthStrong,
  improved: styles.strengthImproved,
  approved: styles.strengthApproved,
  matched: styles.strengthMatched
};

export function StrengthBadge({ strength }: { strength: StrengthLike }) {
  if (!strength) {
    return (
      <span className={`${styles.strengthBadge} ${styles.strengthWeak}`}>強度 —</span>
    );
  }
  return (
    <span className={`${styles.strengthBadge} ${STRENGTH_CLASS[strength]}`}>
      {STRENGTH_LABEL[strength]}
    </span>
  );
}

export function getStrengthLabel(strength: StrengthLike): string {
  if (!strength) {
    return "—";
  }
  return STRENGTH_LABEL[strength];
}
