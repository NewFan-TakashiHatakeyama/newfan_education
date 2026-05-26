export function SkillGapCard({
  skill,
  current,
  target,
  evidenceCount
}: {
  skill: string;
  current: number;
  target: number;
  evidenceCount: number;
}) {
  const gap = Math.max(0, target - current);

  return (
    <li>
      <strong>{skill}</strong>
      <p className="muted">
        現在: {current} / 目標: {target} / 差分: {gap} / 証跡数: {evidenceCount}
      </p>
    </li>
  );
}
