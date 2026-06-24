/**
 * Lightweight LP tracking utility.
 *
 * - Emits `console.log` in development for visibility.
 * - Dispatches a `CustomEvent("lp-analytics", { detail })` on `window`
 *   so future analytics adapters (GA4 / Plausible / 内製計測) can hook in
 *   without bundling an SDK.
 */

export type LpAnalyticsEventName =
  | "hero_primary_cta_clicked"
  | "curriculum_download_clicked"
  | "sample_deliverable_clicked"
  | "program_demo_tab_changed"
  | "role_track_opened"
  | "curriculum_week_opened"
  | "stakeholder_tab_changed"
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
