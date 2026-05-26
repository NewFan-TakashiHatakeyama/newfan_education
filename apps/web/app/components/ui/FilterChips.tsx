"use client";

import { AppIcon, type AppIconName, resolveIconByText } from "./Icon";
import styles from "./ui.module.css";

export type FilterOption<T extends string> = {
  value: T;
  label: string;
  count?: number;
};

export function FilterChips<T extends string>({
  label,
  options,
  selected,
  onChange,
  icon
}: {
  label: string;
  options: Array<FilterOption<T>>;
  selected: T;
  onChange: (value: T) => void;
  icon?: AppIconName;
}) {
  const resolvedIcon = icon ?? resolveIconByText(label);

  return (
    <div className={styles.filterRow} role="group" aria-label={label}>
      <span className={styles.filterGroupLabel}>
        <span className={styles.chipLabel}>
          <AppIcon name={resolvedIcon} className={styles.iconInline} size={12} />
          {label}
        </span>
      </span>
      {options.map((option) => {
        const isActive = option.value === selected;
        return (
          <button
            key={option.value}
            type="button"
            className={`${styles.chip} ${isActive ? styles.chipActive : ""}`}
            onClick={() => onChange(option.value)}
            aria-pressed={isActive}
          >
            {option.label}
            {option.count !== undefined ? (
              <span className={styles.chipCount}>{option.count}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
