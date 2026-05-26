import type { ReactNode } from "react";

export function EmptyState({
  title,
  message,
  action
}: {
  title: string;
  message: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state" role="status" aria-live="polite">
      <h3>{title}</h3>
      <p className="muted">{message}</p>
      {action ? <div className="inline-actions">{action}</div> : null}
    </div>
  );
}
