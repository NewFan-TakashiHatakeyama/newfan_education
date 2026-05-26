type SubmissionStatus = "idle" | "submitting" | "submitted" | "failed";

type SubmitModalProps = {
  open: boolean;
  submissionStatus: SubmissionStatus;
  message: string;
  isSubmitting: boolean;
  onClose: () => void;
  onConfirm: () => void;
};

export function SubmitModal({
  open,
  submissionStatus,
  message,
  isSubmitting,
  onClose,
  onConfirm
}: SubmitModalProps) {
  if (!open) {
    return null;
  }

  const confirmLabel =
    submissionStatus === "failed" ? "再提出する" : isSubmitting ? "提出中..." : "提出する";

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="提出確認">
      <div className="modal-card">
        <h3>SubmitModal</h3>
        <p>{message}</p>
        <p className="muted">提出後は学習イベント記録と成果物候補作成を行います（デモ）。</p>
        <div className="inline-actions">
          <button type="button" className="ghost-button" onClick={onClose} disabled={isSubmitting}>
            閉じる
          </button>
          <button type="button" onClick={onConfirm} disabled={isSubmitting}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
