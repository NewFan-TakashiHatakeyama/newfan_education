import type { EvidenceItem } from "@newfan/contracts";
import type { ReactNode } from "react";

import { AppIcon } from "./Icon";
import styles from "./ui.module.css";
import { SkillChipList } from "./SkillChip";
import { StrengthBadge } from "./StrengthBadge";
import { StatusPill } from "./StatusPill";
import { ReviewPill } from "./ReviewPill";

function formatDate(iso?: string | null): string {
  if (!iso) {
    return "—";
  }
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) {
      return "—";
    }
    return new Intl.DateTimeFormat("ja-JP", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit"
    }).format(d);
  } catch {
    return "—";
  }
}

function accentClass(strength?: string | null): string {
  switch (strength) {
    case "strong":
      return styles.evidenceCardAccentStrong;
    case "approved":
      return styles.evidenceCardAccentApproved;
    case "improved":
      return styles.evidenceCardAccentImproved;
    case "weak":
      return styles.evidenceCardAccentWeak;
    default:
      return "";
  }
}

export function EvidenceCard({
  evidence,
  ownerSlot,
  useCaseLabel = "現場での使いどころ:",
  rubricLabel = "評価ルーブリック"
}: {
  evidence: EvidenceItem;
  ownerSlot?: ReactNode;
  useCaseLabel?: string;
  rubricLabel?: string;
}) {
  const accent = accentClass(evidence.strength);
  return (
    <article className={styles.evidenceCard} aria-label={evidence.title}>
      <span className={`${styles.evidenceCardAccent} ${accent}`} aria-hidden />
      {ownerSlot ? <div>{ownerSlot}</div> : null}
      <div className={styles.evidenceCardTopRow}>
        <h3 className={styles.evidenceTitle}>{evidence.title}</h3>
        <StrengthBadge strength={evidence.strength} />
      </div>

      <p className={styles.evidenceSummary}>{evidence.summary}</p>

      {evidence.useCase ? (
        <p className={styles.evidenceUseCase}>
          <span className={styles.evidenceUseCaseIcon} aria-hidden>
            <AppIcon name="briefcase" size={12} />
          </span>
          <span>
            <strong>{useCaseLabel}</strong> {evidence.useCase}
          </span>
        </p>
      ) : null}

      <SkillChipList skills={evidence.skillTags} />

      {evidence.rubricSummary ? (
        <p className={styles.evidenceRubric}>
          <span className={styles.evidenceMetaLabel}>{rubricLabel}</span>{" "}
          {evidence.rubricSummary}
        </p>
      ) : null}

      <div className={styles.evidenceMeta}>
        <span className={styles.evidenceMetaItem}>
          <AppIcon name="calendarDays" className={styles.iconMuted} size={12} />
          <span className={styles.evidenceMetaLabel}>提出</span>{" "}
          {formatDate(evidence.submittedAt)}
        </span>
        {evidence.score !== null && evidence.score !== undefined ? (
          <span className={styles.evidenceMetaItem}>
            <AppIcon name="chart" className={styles.iconMuted} size={12} />
            <span className={styles.evidenceMetaLabel}>スコア</span> {evidence.score}
          </span>
        ) : null}
        <span className={styles.evidenceMetaItem}>
          <AppIcon name="clock3" className={styles.iconMuted} size={12} />
          <span className={styles.evidenceMetaLabel}>更新</span>{" "}
          {formatDate(evidence.updatedAt)}
        </span>
      </div>

      <div className={styles.evidenceCardFooter}>
        <StatusPill status={evidence.status} />
        <ReviewPill reviewType={evidence.reviewType} />
      </div>
    </article>
  );
}

export function EvidenceOwnerChip({
  learnerName,
  teamName
}: {
  learnerName: string;
  teamName?: string | null;
}) {
  return (
    <span className={styles.evidenceCardOwner}>
      <AppIcon name="userRound" size={12} />
      <strong>{learnerName}</strong>
      {teamName ? <span style={{ color: "#94a3b8" }}>· {teamName}</span> : null}
    </span>
  );
}
