"use client";

import Link from "next/link";

import { AppIcon } from "@/app/components/ui";

import { trackLpEvent } from "@/lib/lp-analytics";

import styles from "./aiFieldReadyLanding.module.css";

export function StickyCtaBar() {
  return (
    <>
      <aside className={styles.stickyDesktop} aria-label="固定アクション">
        <p className={styles.stickyHeading}>商談化のための最短ルート</p>
        <Link
          href="/business/sign-up"
          className={styles.stickyPrimary}
          onClick={() => trackLpEvent("sticky_cta_clicked", { cta: "diagnosis" })}
        >
          <AppIcon name="rocket" size={14} />
          待機人材10名の育成診断を相談する
        </Link>
        <Link
          href="#sample-report"
          className={styles.stickyGhost}
          onClick={() => trackLpEvent("sticky_cta_clicked", { cta: "sample_report" })}
        >
          サンプル証跡レポートを見る
        </Link>
        <Link
          href="#demo"
          className={styles.stickyGhost}
          onClick={() => trackLpEvent("sticky_cta_clicked", { cta: "demo" })}
        >
          無料デモを見る
        </Link>
      </aside>

      <div className={styles.stickyMobile} aria-label="モバイル用 固定 CTA">
        <Link
          href="#sample-report"
          className={styles.stickyMobileGhost}
          onClick={() => trackLpEvent("sticky_cta_clicked", { cta: "sample_report" })}
        >
          サンプル証跡レポート
        </Link>
        <Link
          href="#demo"
          className={styles.stickyMobilePrimary}
          onClick={() => trackLpEvent("sticky_cta_clicked", { cta: "demo" })}
        >
          無料デモを見る
        </Link>
      </div>
    </>
  );
}
