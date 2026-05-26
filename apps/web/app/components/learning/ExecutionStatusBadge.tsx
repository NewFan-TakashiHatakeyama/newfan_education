export type ExecutionStatus =
  | "idle"
  | "running"
  | "success"
  | "error"
  | "timeout"
  | "package_restricted";

const LABEL_MAP: Record<ExecutionStatus, string> = {
  idle: "未実行",
  running: "実行中",
  success: "成功",
  error: "失敗",
  timeout: "タイムアウト",
  package_restricted: "パッケージ制限"
};

export function ExecutionStatusBadge({ status }: { status: ExecutionStatus }) {
  return <span className={`exec-badge exec-${status}`}>{LABEL_MAP[status]}</span>;
}
