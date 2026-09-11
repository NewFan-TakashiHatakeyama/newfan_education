import type { ReactNode } from "react";
import styles from "./ui.module.css";

export function Disclosure({ title = "詳しく見る", children, open }: { title?: string; children: ReactNode; open?: boolean }) {
  return <details className={styles.disclosure} open={open}><summary>{title}</summary><div>{children}</div></details>;
}
