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
            tabIndex={active ? 0 : -1}
            type="button"
            className={`${styles.tab} ${active ? styles.tabActive : ""}`}
            onClick={() => onChange(option.value)}
            onKeyDown={event => {
              const index = options.findIndex(item => item.value === option.value);
              const next = event.key === "ArrowRight" ? (index + 1) % options.length
                : event.key === "ArrowLeft" ? (index - 1 + options.length) % options.length
                  : event.key === "Home" ? 0 : event.key === "End" ? options.length - 1 : -1;
              if (next < 0) return;
              event.preventDefault(); onChange(options[next].value);
              (event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>('[role="tab"]')[next])?.focus();
            }}
          >
            {option.label}
            {option.count !== undefined ? ` (${option.count})` : ""}
          </button>
        );
      })}
    </div>
  );
}
