import type { EvidenceStatus } from "@newfan/contracts";

import styles from "./ui.module.css";

type StatusLike = EvidenceStatus | null | undefined;

const STATUS_LABEL: Record<EvidenceStatus, string> = {
  completed: "教材完了",
  submitted: "提出済み",
  passed: "合格",
  resubmit: "再提出依頼",
  approved: "メンター承認"
};

const STATUS_CLASS: Record<EvidenceStatus, string> = {
  completed: styles.statusCompleted,
  submitted: styles.statusSubmitted,
  passed: styles.statusPassed,
  resubmit: styles.statusResubmit,
  approved: styles.statusApproved
};

export function StatusPill({ status }: { status: StatusLike }) {
  if (!status) {
    return <span className={`${styles.statusPill} ${styles.statusUnknown}`}>状態 —</span>;
  }
  return (
    <span className={`${styles.statusPill} ${STATUS_CLASS[status]}`}>
      {STATUS_LABEL[status]}
    </span>
  );
}
