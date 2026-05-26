import type { ReactNode } from "react";

import { AppIcon, type AppIconName, resolveIconByText } from "./Icon";
import styles from "./ui.module.css";

export type SectionTheme = "default" | "company" | "mentor";

export function Section({
  title,
  meta,
  actions,
  children,
  theme = "default",
  contentClassName,
  icon
}: {
  title: ReactNode;
  meta?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  theme?: SectionTheme;
  contentClassName?: string;
  icon?: AppIconName;
}) {
  const resolvedIcon =
    icon ?? (typeof title === "string" ? resolveIconByText(title) : null);
  const titleIconTheme =
    theme === "company"
      ? styles.titleIconCompany
      : theme === "mentor"
        ? styles.titleIconMentor
        : styles.titleIcon;

  return (
    <section className={styles.section}>
      <div className={styles.sectionHeader}>
        <div>
          <h2 className={styles.sectionTitle}>
            {resolvedIcon ? (
              <AppIcon name={resolvedIcon} className={`${styles.iconInline} ${titleIconTheme}`} />
            ) : null}
            {title}
          </h2>
          {meta ? <p className={styles.sectionMeta}>{meta}</p> : null}
        </div>
        {actions ? <div className={styles.actionRow}>{actions}</div> : null}
      </div>
      <div className={contentClassName}>{children}</div>
    </section>
  );
}
