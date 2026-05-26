import { ExecutionStatusBadge, type ExecutionStatus } from "./ExecutionStatusBadge";

type RunConsoleProps = {
  status: ExecutionStatus;
  stdout: string;
  stderr: string;
  elapsedMs: number | null;
};

export function RunConsole({ status, stdout, stderr, elapsedMs }: RunConsoleProps) {
  return (
    <section>
      <div className="exercise-console-header">
        <h2>RunConsole</h2>
        <div className="inline-actions">
          <ExecutionStatusBadge status={status} />
          <span className="muted">実行時間: {elapsedMs ?? "-"} ms</span>
        </div>
      </div>
      <div className="console-grid">
        <div>
          <h3>stdout</h3>
          <pre className="console-pane">{stdout || "(empty)"}</pre>
        </div>
        <div>
          <h3>stderr</h3>
          <pre className="console-pane error-pane">{stderr || "(empty)"}</pre>
        </div>
      </div>
    </section>
  );
}
