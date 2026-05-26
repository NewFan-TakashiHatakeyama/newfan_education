import { ExecutionStatusBadge, type ExecutionStatus } from "./ExecutionStatusBadge";

type ExerciseHeaderProps = {
  title: string;
  estimatedMinutes: number;
  executionStatus: ExecutionStatus;
  savedAtText: string;
  onSubmit: () => void;
  canSubmit: boolean;
  submitLabel: string;
  submissionStatusText: string;
};

export function ExerciseHeader({
  title,
  estimatedMinutes,
  executionStatus,
  savedAtText,
  onSubmit,
  canSubmit,
  submitLabel,
  submissionStatusText
}: ExerciseHeaderProps) {
  return (
    <section>
      <div className="exercise-header">
        <div>
          <h1 style={{ marginBottom: 6 }}>{title}</h1>
          <p className="muted">
            所要時間: {estimatedMinutes}分 / 保存状態: {savedAtText} / 提出状態: {submissionStatusText}
          </p>
        </div>
        <div className="inline-actions">
          <ExecutionStatusBadge status={executionStatus} />
          <button type="button" onClick={onSubmit} disabled={!canSubmit}>
            {submitLabel}
          </button>
        </div>
      </div>
    </section>
  );
}
