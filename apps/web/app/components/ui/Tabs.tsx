"use client";

import styles from "./ui.module.css";

export type TabOption<T extends string> = {
  value: T;
  label: string;
  count?: number;
};

export function Tabs<T extends string>({
  options,
  selected,
  onChange,
  ariaLabel = "tabs"
}: {
  options: Array<TabOption<T>>;
  selected: T;
  onChange: (value: T) => void;
  ariaLabel?: string;
}) {
  return (
    <div className={styles.tabs} role="tablist" aria-label={ariaLabel}>
      {options.map((option) => {
        const active = option.value === selected;
        return (
          <button
            key={option.value}
            role="tab"
            aria-selected={active}
            type="button"
            className={`${styles.tab} ${active ? styles.tabActive : ""}`}
            onClick={() => onChange(option.value)}
          >
            {option.label}
            {option.count !== undefined ? ` (${option.count})` : ""}
          </button>
        );
      })}
    </div>
  );
}
