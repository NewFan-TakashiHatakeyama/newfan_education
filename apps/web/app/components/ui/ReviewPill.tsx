import type { EvidenceReviewType } from "@newfan/contracts";

import styles from "./ui.module.css";

const REVIEW_LABEL: Record<EvidenceReviewType, string> = {
  ai: "AIレビュー",
  mentor: "メンター評価",
  ai_and_mentor: "AI + メンター承認"
};

export function ReviewPill({
  reviewType
}: {
  reviewType: EvidenceReviewType | null | undefined;
}) {
  if (!reviewType) {
    return <span className={styles.reviewPill}>レビュー —</span>;
  }
  return <span className={styles.reviewPill}>{REVIEW_LABEL[reviewType]}</span>;
}
