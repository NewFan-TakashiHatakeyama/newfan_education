import styles from "./ui.module.css";

export function EvidenceCardSkeleton() {
  return (
    <div className={styles.evidenceCard} aria-hidden="true">
      <span className={`${styles.evidenceCardAccent} ${styles.evidenceCardAccentWeak}`} />
      <div className={styles.skeletonRow}>
        <div className={styles.skeletonBox} style={{ width: "55%", height: 18 }} />
        <div className={styles.skeletonBox} style={{ width: "90%" }} />
        <div className={styles.skeletonBox} style={{ width: "78%" }} />
        <div className={styles.skeletonBox} style={{ width: "45%" }} />
      </div>
    </div>
  );
}

export function HeroSkeleton() {
  return <div className={styles.skeletonBoxTall} aria-hidden="true" />;
}

export function SkeletonRow({ widths = ["55%", "90%", "70%"] }: { widths?: string[] }) {
  return (
    <div className={styles.skeletonRow} aria-hidden="true">
      {widths.map((w, i) => (
        <div key={i} className={styles.skeletonBox} style={{ width: w }} />
      ))}
    </div>
  );
}
