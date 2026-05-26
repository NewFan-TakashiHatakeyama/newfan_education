import type { ExecutionStatus } from "./ExecutionStatusBadge";

type SubmissionStatus = "idle" | "submitting" | "submitted" | "failed";

type TestResultPanelProps = {
  executionStatus: ExecutionStatus;
  submissionStatus: SubmissionStatus;
  attempts: number;
};

function resolveCaseLabel(status: ExecutionStatus) {
  if (status === "success") {
    return "PASS";
  }
  if (status === "running") {
    return "RUNNING";
  }
  if (status === "error" || status === "timeout" || status === "package_restricted") {
    return "FAIL";
  }
  return "NOT RUN";
}

export function TestResultPanel({
  executionStatus,
  submissionStatus,
  attempts
}: TestResultPanelProps) {
  const caseLabel = resolveCaseLabel(executionStatus);

  return (
    <section>
      <h2>TestResultPanel</h2>
      <ul className="card-list">
        <li>case_1 (2, 3) - {caseLabel}</li>
        <li>case_2 (10, -2) - {caseLabel}</li>
      </ul>
      <p className="muted">
        提出試行回数: {attempts} / 提出状態:{" "}
        {submissionStatus === "idle"
          ? "未提出"
          : submissionStatus === "submitting"
            ? "提出処理中"
            : submissionStatus === "submitted"
              ? "提出済み"
              : "提出失敗"}
      </p>
    </section>
  );
}
