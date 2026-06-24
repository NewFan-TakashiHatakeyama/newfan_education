"use client";

import { useEffect, useRef, useState } from "react";

import { AppIcon } from "@/app/components/ui";

import { trackLpEvent } from "@/lib/lp-analytics";

import styles from "./aiFieldReadyLanding.module.css";
import { LP_STAKEHOLDER_TABS } from "./lpContent";

export function StakeholderValueTabs({ reducedMotion }: { reducedMotion: boolean }) {
  const [active, setActive] = useState(LP_STAKEHOLDER_TABS[0].id);
  const tabListRef = useRef<HTMLDivElement | null>(null);
  const [indicator, setIndicator] = useState({ left: 0, width: 0 });

  const activeTab = LP_STAKEHOLDER_TABS.find((tab) => tab.id === active) ?? LP_STAKEHOLDER_TABS[0];

  useEffect(() => {
    const root = tabListRef.current;
    if (!root) return;
    const button = root.querySelector<HTMLButtonElement>(`button[data-stakeholder-id="${active}"]`);
    if (!button) return;
    const rootRect = root.getBoundingClientRect();
    const buttonRect = button.getBoundingClientRect();
    setIndicator({ left: buttonRect.left - rootRect.left, width: buttonRect.width });
  }, [active]);

  return (
    <div className={styles.stakeholderTabs}>
      <div ref={tabListRef} className={styles.tabList} role="tablist" aria-label="部門別導入価値">
        {LP_STAKEHOLDER_TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={active === tab.id}
            data-stakeholder-id={tab.id}
            className={`${styles.tabButton} ${active === tab.id ? styles.tabButtonActive : ""}`}
            onClick={() => {
              setActive(tab.id);
              trackLpEvent("stakeholder_tab_changed", { tab: tab.id });
            }}
          >
            {tab.label}
          </button>
        ))}
        <span
          className={styles.tabIndicator}
          style={{
            width: indicator.width,
            transform: `translateX(${indicator.left}px)`,
            transition: reducedMotion ? "none" : undefined
          }}
          aria-hidden
        />
      </div>

      <article
        key={activeTab.id}
        role="tabpanel"
        className={`${styles.stakeholderPanel} ${reducedMotion ? styles.tabPanelStatic : styles.tabPanelAnimated}`}
      >
        <span className={styles.valueIconBadge}>
          <AppIcon name={activeTab.icon} size={18} />
        </span>
        <p className={styles.valueStakeholder}>{activeTab.audience}</p>
        <h3>{activeTab.benefit}</h3>
        <p>{activeTab.detail}</p>
      </article>
    </div>
  );
}
