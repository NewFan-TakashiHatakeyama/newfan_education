"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import styles from "./ventures.module.css";

/** 案件配下の画面を横断するタブ。台帳は数が多いので概要ページから辿る。 */
export function VentureNav({ ventureId }: { ventureId: string }) {
  const pathname = usePathname();
  const base = `/ventures/${ventureId}`;
  const links = [
    { href: base, label: "概要" },
    { href: `${base}/tasks`, label: "工程タスク" },
    { href: `${base}/gates`, label: "ゲート承認" },
    { href: `${base}/skills`, label: "スキル充足" }
  ];

  return (
    <nav className={styles.nav} aria-label="案件メニュー">
      <Link href="/ventures" className={styles.navLink}>
        ← 案件一覧
      </Link>
      {links.map((link) => {
        const active =
          link.href === base ? pathname === base : pathname.startsWith(link.href);
        return (
          <Link
            key={link.href}
            href={link.href}
            className={`${styles.navLink} ${active ? styles.navLinkActive : ""}`}
            aria-current={active ? "page" : undefined}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}

const APPLICABILITY_CLASS: Record<string, string> = {
  適用: styles.pillApplied,
  対象外: styles.pillExcluded,
  未判定: styles.pillUndecided
};

const STATUS_CLASS: Record<string, string> = {
  完了: styles.pillDone,
  進行中: styles.pillProgress,
  保留: styles.pillBlocked,
  未着手: styles.pillNeutral
};

export function ApplicabilityPill({ value }: { value: string }) {
  return (
    <span className={`${styles.pill} ${APPLICABILITY_CLASS[value] ?? styles.pillNeutral}`}>
      {value}
    </span>
  );
}

export function TaskStatusPill({ value }: { value: string }) {
  return (
    <span className={`${styles.pill} ${STATUS_CLASS[value] ?? styles.pillNeutral}`}>{value}</span>
  );
}

const DECISION_CLASS: Record<string, string> = {
  承認: styles.pillDone,
  廃止完了承認: styles.pillDone,
  Scale: styles.pillDone,
  Continue: styles.pillDone,
  条件付承認: styles.pillUndecided,
  差戻し: styles.pillBlocked,
  否決: styles.pillBlocked,
  Stop: styles.pillBlocked,
  Shrink: styles.pillBlocked,
  Pivot: styles.pillProgress,
  未審査: styles.pillNeutral
};

export function GateDecisionPill({ value }: { value: string }) {
  return (
    <span className={`${styles.pill} ${DECISION_CLASS[value] ?? styles.pillNeutral}`}>{value}</span>
  );
}
