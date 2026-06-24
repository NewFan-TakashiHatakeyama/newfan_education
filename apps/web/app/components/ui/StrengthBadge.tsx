import type { EvidenceStrength } from "@newfan/contracts";

import styles from "./ui.module.css";

type StrengthLike = EvidenceStrength | null | undefined;

const STRENGTH_LABEL: Record<EvidenceStrength, string> = {
  weak: "要改善",
  standard: "標準成果物",
  strong: "PoC判断向け",
  improved: "改善履歴あり",
  approved: "レビュー合格",
  matched: "AIプロジェクト適合"
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
