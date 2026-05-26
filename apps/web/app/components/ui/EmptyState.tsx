import type { ReactNode } from "react";

import styles from "./ui.module.css";

export function EmptyState({
  icon = "✶",
  title,
  message,
  action
}: {
  icon?: ReactNode;
  title: string;
  message: string;
  action?: ReactNode;
}) {
  return (
    <div className={styles.emptyState}>
      <span className={styles.emptyIcon} aria-hidden>
        {icon}
      </span>
      <h3 className={styles.emptyTitle}>{title}</h3>
      <p className={styles.emptyLead}>{message}</p>
      {action ? (
        <div className={styles.actionRow} style={{ justifyContent: "center" }}>
          {action}
        </div>
      ) : null}
    </div>
  );
}
