"use client";

import { useEffect, useRef } from "react";

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
      <div className={styles.deliverablesSidebar}>
        <p className={styles.deliverablesSidebarLabel}>研修で残す成果物</p>
        <ul className={styles.deliverablesList}>
          {LP_DELIVERABLES_SECTION.items.map((item) => (
            <li key={item.name}>
              <strong>{item.name}</strong>
              <span>{item.use}</span>
            </li>
          ))}
        </ul>
      </div>

      <article className={styles.deliverablesProposalCard} aria-label="問い合わせ回答支援AIの提案書サンプル">
        <header className={styles.deliverablesProposalHeader}>
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
            <dt>次アクション</dt>
            <dd>{preview.nextAction}</dd>
          </div>
        </dl>

        <div className={styles.deliverablesCompare}>
          <div>
            <span className={styles.deliverablesCompareLabel}>{preview.asIs.label}</span>
            <strong>{preview.asIs.kpi}</strong>
            <p>{preview.asIs.process}</p>
          </div>
          <div>
            <span className={styles.deliverablesCompareLabel}>{preview.toBe.label}</span>
            <strong>{preview.toBe.kpi}</strong>
            <p>{preview.toBe.process}</p>
          </div>
        </div>

        <div className={styles.deliverablesMetaBlock}>
          <p className={styles.deliverablesMetaTitle}>利用データ</p>
          <ul className={styles.deliverablesChipList}>
            {preview.dataSources.map((source) => (
              <li key={source}>{source}</li>
            ))}
          </ul>
        </div>

        <div className={styles.deliverablesMetaRow}>
          <div className={styles.deliverablesMetaBlock}>
            <p className={styles.deliverablesMetaTitle}>対象外</p>
            <ul className={styles.deliverablesChipList}>
              {preview.outOfScope.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className={styles.deliverablesMetaBlock}>
            <p className={styles.deliverablesMetaTitle}>ガードレール</p>
            <ul className={styles.deliverablesChipList}>
              {preview.guardrails.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className={styles.deliverablesDraftList} aria-label="回答ドラフト例">
          <p className={styles.deliverablesMetaTitle}>回答ドラフト例</p>
          {preview.sampleDrafts.map((sample) => (
            <div key={sample.inquiry} className={styles.deliverablesDraft}>
              <div className={styles.deliverablesDraftMeta}>
                <span className={styles.deliverablesDraftCategory}>{sample.category}</span>
                <span
                  className={
                    sample.disposition === "エスカレーション"
                      ? styles.deliverablesDraftDispositionWarn
                      : styles.deliverablesDraftDispositionOk
                  }
                >
                  {sample.disposition}
                </span>
              </div>
              <p className={styles.deliverablesDraftInquiry}>
                <span>問い合わせ</span>
                {sample.inquiry}
              </p>
              <p className={styles.deliverablesDraftBody}>{sample.draft}</p>
              <ul className={styles.deliverablesDraftSources}>
                {sample.sources.map((source) => (
                  <li key={source}>{source}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </article>
    </div>
  );
}
