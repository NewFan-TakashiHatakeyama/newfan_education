"use client";

import Link from "next/link";

import { AppIcon } from "@/app/components/ui";

import { trackLpEvent } from "@/lib/lp-analytics";

import styles from "./aiFieldReadyLanding.module.css";
import { LP_CTA } from "./lpContent";

export function StickyCtaBar() {
  return (
    <>
      <aside className={styles.stickyDesktop} aria-label="固定アクション">
        <p className={styles.stickyHeading}>AI人材育成の第一歩</p>
        <Link
          href="/business/sign-up"
          className={styles.stickyPrimary}
          onClick={() => trackLpEvent("sticky_cta_clicked", { cta: "diagnosis" })}
        >
          <AppIcon name="rocket" size={14} />
          {LP_CTA.primary}
        </Link>
        <Link
          href="#curriculum-download"
          className={styles.stickyGhost}
          onClick={() => trackLpEvent("sticky_cta_clicked", { cta: "curriculum" })}
        >
          {LP_CTA.secondary}
        </Link>
        <Link
          href="#sample-deliverables"
          className={styles.stickyGhost}
          onClick={() => trackLpEvent("sticky_cta_clicked", { cta: "sample" })}
        >
          {LP_CTA.tertiary}
        </Link>
      </aside>

      <div className={styles.stickyMobile} aria-label="モバイル用 固定 CTA">
        <Link
          href="#curriculum-download"
          className={styles.stickyMobileGhost}
          onClick={() => trackLpEvent("sticky_cta_clicked", { cta: "curriculum" })}
        >
          資料を見る
        </Link>
        <Link
          href="/business/sign-up"
          className={styles.stickyMobilePrimary}
          onClick={() => trackLpEvent("sticky_cta_clicked", { cta: "diagnosis" })}
        >
          診断を相談
        </Link>
      </div>
    </>
  );
}
