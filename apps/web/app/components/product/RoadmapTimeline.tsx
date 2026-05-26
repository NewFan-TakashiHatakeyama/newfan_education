import type { Roadmap } from "@newfan/contracts";

export function RoadmapTimeline({ roadmap }: { roadmap: Roadmap | null }) {
  if (!roadmap || roadmap.items.length === 0) {
    return null;
  }

  return (
    <div>
      {roadmap.items.map((item, index) => (
        <div className="timeline-item" key={item.id}>
          <strong>
            Week {index + 1} / Step {index + 1}: {item.title}
          </strong>
          <p className="muted">
            所要時間 {item.estimatedMinutes}分 / 到達スキル {item.prerequisiteSkillTags.join(", ")}
          </p>
          <span className="status-pill">未着手</span>
        </div>
      ))}
    </div>
  );
}
