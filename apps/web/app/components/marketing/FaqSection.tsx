"use client";

import { useState } from "react";

import { trackLpEvent } from "@/lib/lp-analytics";

import styles from "./aiFieldReadyLanding.module.css";
import { LP_FAQS } from "./lpContent";

export function FaqSection() {
  const [openMap, setOpenMap] = useState<Record<number, boolean>>(() =>
    LP_FAQS.reduce<Record<number, boolean>>((acc, faq, index) => {
      acc[index] = Boolean(faq.defaultOpen);
      return acc;
    }, {})
  );

  return (
    <div className={styles.faqList}>
      {LP_FAQS.map((faq, index) => {
        const isOpen = openMap[index];
        return (
          <details
            key={faq.q}
            className={styles.faqItem}
            open={isOpen}
            onToggle={(event) => {
              const target = event.currentTarget;
              if (target.open === isOpen) {
                return;
              }
              setOpenMap((prev) => ({ ...prev, [index]: target.open }));
              if (target.open) {
                trackLpEvent("faq_opened", { question: faq.q });
              }
            }}
          >
            <summary>
              <span>{faq.q}</span>
              <span className={styles.faqMarker} aria-hidden />
            </summary>
            <p>{faq.a}</p>
          </details>
        );
      })}
    </div>
  );
}
