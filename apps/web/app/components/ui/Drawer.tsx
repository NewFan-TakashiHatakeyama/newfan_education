"use client";

import { useEffect, type ReactNode } from "react";

import styles from "./ui.module.css";

export function Drawer({
  open,
  title,
  onClose,
  children
}: {
  open: boolean;
  title: ReactNode;
  onClose: () => void;
  children: ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", handler);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className={styles.drawerBackdrop}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={typeof title === "string" ? title : undefined}
    >
      <aside
        className={styles.drawerPanel}
        onClick={(event) => event.stopPropagation()}
      >
        <div className={styles.drawerHeader}>
          <h2 className={styles.drawerTitle}>{title}</h2>
          <button
            type="button"
            className={styles.drawerClose}
            onClick={onClose}
            aria-label="閉じる"
          >
            ✕
          </button>
        </div>
        {children}
      </aside>
    </div>
  );
}
