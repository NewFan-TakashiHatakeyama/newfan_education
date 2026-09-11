"use client";

import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import styles from "./ui.module.css";

export type DrawerProps = {
  open: boolean; title: ReactNode; onClose: () => void; children: ReactNode;
  dirty?: boolean; busy?: boolean; footer?: ReactNode; variant?: "drawer" | "modal";
};

export function Drawer({ open, title, onClose, children, dirty = false, busy = false, footer, variant = "drawer" }: DrawerProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const [discard, setDiscard] = useState(false);
  useEffect(() => {
    const dialog = ref.current;
    if (!open || !dialog) return;
    const trigger = document.activeElement as HTMLElement | null;
    const previousOverflow = document.body.style.overflow;
    dialog.showModal();
    document.body.style.overflow = "hidden";
    return () => {
      dialog.close();
      document.body.style.overflow = previousOverflow;
      if (trigger?.isConnected) trigger.focus();
    };
  }, [open]);
  useEffect(() => {
    if (!open || !dirty) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [open, dirty]);
  const close = () => {
    if (busy) return;
    if (dirty) setDiscard(true);
    else { setDiscard(false); onClose(); }
  };
  if (!open) return null;
  return createPortal(
    <dialog ref={ref} className={`${styles.overlay} ${variant === "modal" ? styles.modal : styles.sidePanel}`}
      aria-labelledby={titleId} onCancel={event => { event.preventDefault(); close(); }}
      onKeyDown={event => {
        if (event.key !== "Tab") return;
        const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), a[href], summary, [tabindex="0"]')).filter(element => element.getClientRects().length > 0);
        const first = controls[0], last = controls[controls.length - 1];
        if (!first) { event.preventDefault(); return; }
        if (event.shiftKey && (document.activeElement === first || document.activeElement === event.currentTarget)) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }}
      onClick={event => { if (event.target === event.currentTarget) {
        const bounds = event.currentTarget.getBoundingClientRect();
        if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) close();
      } }}>
      <div className={styles.overlayLayout}>
        <header className={styles.drawerHeader}>
          <h2 id={titleId} className={styles.drawerTitle}>{title}</h2>
          <button type="button" className={styles.drawerClose} disabled={busy} onClick={close} aria-label="閉じる">×</button>
        </header>
        {discard ? <div className={styles.discardPrompt} role="alert">
          <strong>変更を破棄しますか？</strong><p>保存していない内容は失われます。</p>
          <div className={styles.actionRow}>
            <button type="button" autoFocus onClick={() => setDiscard(false)}>編集を続ける</button>
            <button type="button" className="danger-button" onClick={() => { setDiscard(false); onClose(); }}>変更を破棄して閉じる</button>
          </div>
        </div> : <>
          <div className={styles.overlayBody}>{children}</div>
          {footer && <footer className={styles.overlayFooter}>{footer}</footer>}
        </>}
      </div>
    </dialog>, document.body
  );
}

export function Modal(props: Omit<DrawerProps, "variant">) {
  return <Drawer {...props} variant="modal" />;
}
