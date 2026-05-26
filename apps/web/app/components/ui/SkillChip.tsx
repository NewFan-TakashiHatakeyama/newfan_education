import styles from "./ui.module.css";

export type SkillChipTone = "default" | "strong" | "gap";

const TONE_CLASS: Record<SkillChipTone, string> = {
  default: "",
  strong: styles.skillChipStrong,
  gap: styles.skillChipGap
};

export function SkillChip({ label, tone = "default" }: { label: string; tone?: SkillChipTone }) {
  return <span className={`${styles.skillChip} ${TONE_CLASS[tone]}`}>#{label}</span>;
}

export function SkillChipList({
  skills,
  tone = "default"
}: {
  skills: string[];
  tone?: SkillChipTone;
}) {
  if (skills.length === 0) {
    return null;
  }
  return (
    <div className={styles.skillChips}>
      {skills.map((skill) => (
        <SkillChip key={`${tone}-${skill}`} label={skill} tone={tone} />
      ))}
    </div>
  );
}
