"use client";

import { useEffect, useRef } from "react";

import { AppIcon } from "@/app/components/ui";

import { trackLpEvent } from "@/lib/lp-analytics";

import styles from "./aiFieldReadyLanding.module.css";
import { LP_DELIVERABLES_SECTION } from "./lpContent";

export function DeliverablesPreview() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const preview = LP_DELIVERABLES_SECTION.preview;

  useEffect(() => {
    const node = containerRef.current;
    if (!node || typeof IntersectionObserver === "undefined") return;
    let fired = false;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!fired && entry.isIntersecting) {
            fired = true;
            trackLpEvent("sample_deliverable_clicked", { source: "view" });
            observer.disconnect();
            break;
          }
        }
      },
      { threshold: 0.35 }
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={containerRef} className={styles.deliverablesLayout}>
      <ul className={styles.deliverablesList}>
        {LP_DELIVERABLES_SECTION.items.map((item) => (
          <li key={item.name}>
            <strong>{item.name}</strong>
            <span>{item.use}</span>
          </li>
        ))}
      </ul>

      <article className={styles.deliverablesProposalCard} aria-label="AIプロジェクト提案書プレビュー">
        <header>
          <p className={styles.deliverablesProposalEyebrow}>{preview.title}</p>
          <h3>{preview.theme}</h3>
        </header>
        <dl className={styles.deliverablesProposalFields}>
          <div>
            <dt>対象部門</dt>
            <dd>{preview.department}</dd>
          </div>
          <div>
            <dt>課題</dt>
            <dd>{preview.issue}</dd>
          </div>
          <div>
            <dt>AI活用方式</dt>
            <dd>{preview.approach}</dd>
          </div>
          <div>
            <dt>PoC成功条件</dt>
            <dd>{preview.successCriteria}</dd>
          </div>
          <div>
            <dt>必要データ</dt>
            <dd>{preview.data}</dd>
          </div>
          <div>
            <dt>主なリスク</dt>
            <dd>{preview.risks}</dd>
          </div>
          <div>
            <dt>次アクション</dt>
            <dd>{preview.nextAction}</dd>
          </div>
        </dl>
        <footer className={styles.deliverablesProposalFooter}>
          <AppIcon name="fileCheck2" size={14} />
          <span>経営・部門向け意思決定資料として出力</span>
        </footer>
      </article>
    </div>
  );
}
