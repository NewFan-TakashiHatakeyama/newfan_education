import type { ReactNode } from "react";

import { AppIcon, type AppIconName, resolveIconByText } from "./Icon";
import styles from "./ui.module.css";
import { ReadinessBadge, type ReadinessLevel } from "./ReadinessBadge";

export type PageHeroTheme = "default" | "company" | "mentor" | "marketing";

export type PageHeroMetric = {
  label: string;
  value: ReactNode;
  suffix?: string;
  hint?: ReactNode;
  progress?: number;
  icon?: AppIconName;
};

const HERO_THEME: Record<PageHeroTheme, string> = {
  default: "",
  company: styles.heroCompany,
  mentor: styles.heroMentor,
  marketing: styles.heroMarketing
};

const HERO_EYEBROW_THEME: Record<PageHeroTheme, string> = {
  default: "",
  company: styles.heroEyebrowCompany,
  mentor: styles.heroEyebrowMentor,
  marketing: styles.heroEyebrowMarketing
};

const HERO_TITLE_THEME: Record<PageHeroTheme, string> = {
  default: "",
  company: "",
  mentor: "",
  marketing: styles.heroTitleMarketing
};

const HERO_PROGRESS_THEME: Record<PageHeroTheme, string> = {
  default: "",
  company: styles.progressFillCompany,
  mentor: styles.progressFillMentor,
  marketing: ""
};

export function PageHero({
  eyebrow,
  title,
  lead,
  readiness,
  metrics,
  actions,
  theme = "default",
  ariaLabel = "ページステータス",
  extra
}: {
  eyebrow: string;
  title: string;
  lead: ReactNode;
  readiness?: ReadinessLevel;
  metrics?: PageHeroMetric[];
  actions?: ReactNode;
  theme?: PageHeroTheme;
  ariaLabel?: string;
  extra?: ReactNode;
}) {
  return (
    <section className={`${styles.hero} ${HERO_THEME[theme]}`} aria-label={ariaLabel}>
      <div className={styles.heroTopRow}>
        <span className={`${styles.heroEyebrow} ${HERO_EYEBROW_THEME[theme]}`}>{eyebrow}</span>
        {readiness ? <ReadinessBadge level={readiness} /> : null}
      </div>
      <h1 className={`${styles.heroTitle} ${HERO_TITLE_THEME[theme]}`}>{title}</h1>
      <p className={styles.heroLead}>{lead}</p>
      {actions ? <div className={styles.actionRow}>{actions}</div> : null}
      {metrics && metrics.length > 0 ? (
        <div className={styles.heroMetrics}>
          {metrics.map((metric) => (
            <div key={metric.label} className={styles.metric}>
              <p className={styles.metricLabel}>
                <AppIcon
                  name={metric.icon ?? resolveIconByText(metric.label)}
                  className={styles.metricIcon}
                  size={13}
                />
                {metric.label}
              </p>
              <div className={styles.metricValue}>
                <span>{metric.value}</span>
                {metric.suffix ? <span className={styles.metricSuffix}>{metric.suffix}</span> : null}
              </div>
              {metric.progress !== undefined ? (
                <div
                  className={styles.progressTrack}
                  role="progressbar"
                  aria-valuenow={Math.round(metric.progress * 100)}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <div
                    className={`${styles.progressFill} ${HERO_PROGRESS_THEME[theme]}`}
                    style={{ width: `${Math.min(100, Math.max(0, metric.progress * 100))}%` }}
                  />
                </div>
              ) : null}
              {metric.hint ? <p className={styles.metricFoot}>{metric.hint}</p> : null}
            </div>
          ))}
        </div>
      ) : null}
      {extra}
    </section>
  );
}
