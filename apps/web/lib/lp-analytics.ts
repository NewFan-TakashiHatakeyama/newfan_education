/**
 * Lightweight LP tracking utility.
 *
 * - Emits `console.log` in development for visibility.
 * - Dispatches a `CustomEvent("lp-analytics", { detail })` on `window`
 *   so future analytics adapters (GA4 / Plausible / 内製計測) can hook in
 *   without bundling an SDK.
 *
 * 設計意図: SaaS LP の改善サイクルにおいて、主要 CTA / セクション露出 /
 * タブ切替を再現性高く追跡できることを最低限の責務とする。
 */

export type LpAnalyticsEventName =
  | "hero_demo_cta_clicked"
  | "sample_report_cta_clicked"
  | "diagnosis_cta_clicked"
  | "product_demo_tab_changed"
  | "evidence_report_viewed"
  | "pricing_plan_clicked"
  | "faq_opened"
  | "final_cta_clicked"
  | "sticky_cta_clicked";

export type LpAnalyticsPayload = {
  event: LpAnalyticsEventName;
  meta?: Record<string, string | number | boolean | null | undefined>;
  timestamp: string;
};

const LP_EVENT_NAME = "lp-analytics";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

function isDev(): boolean {
  if (typeof process === "undefined") {
    return false;
  }
  return process.env?.NODE_ENV !== "production";
}

export function trackLpEvent(
  event: LpAnalyticsEventName,
  meta?: LpAnalyticsPayload["meta"]
): void {
  const payload: LpAnalyticsPayload = {
    event,
    meta,
    timestamp: new Date().toISOString()
  };

  if (isDev() && typeof console !== "undefined") {
    console.info("[lp-analytics]", event, meta ?? {});
  }

  if (!isBrowser()) {
    return;
  }

  try {
    const customEvent = new CustomEvent<LpAnalyticsPayload>(LP_EVENT_NAME, {
      detail: payload
    });
    window.dispatchEvent(customEvent);
  } catch {
    // 環境によっては CustomEvent 構築に失敗するため握り潰す。
  }
}
