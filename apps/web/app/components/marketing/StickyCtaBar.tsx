"use client";

import Link from "next/link";

import { trackLpEvent } from "@/lib/lp-analytics";

import styles from "./aiFieldReadyLanding.module.css";

/** モバイル下部の最小固定CTA。デスクトップはヘッダー/最終CTAに任せ、重複表示を避ける。 */
export function StickyCtaBar() {
  return (
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
  );
}
