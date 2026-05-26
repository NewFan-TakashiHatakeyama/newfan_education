"use client";

import { useEffect, useRef } from "react";

import { AppIcon } from "@/app/components/ui";

import { trackLpEvent } from "@/lib/lp-analytics";

import styles from "./aiFieldReadyLanding.module.css";
import { LP_EVIDENCE_REPORT_SECTION } from "./lpContent";

export function EvidenceReportPreview() {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const node = containerRef.current;
    if (!node || typeof IntersectionObserver === "undefined") {
      return;
    }
    let fired = false;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!fired && entry.isIntersecting) {
            fired = true;
            trackLpEvent("evidence_report_viewed");
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

  const report = LP_EVIDENCE_REPORT_SECTION.report;

  return (
    <div ref={containerRef} className={styles.evidenceLayout}>
      <article className={styles.evidenceReportCard} aria-label="実務証跡レポート プレビュー">
        <header className={styles.evidenceReportHead}>
          <div>
            <p className={styles.evidenceReportEyebrow}>{LP_EVIDENCE_REPORT_SECTION.eyebrow}</p>
            <h3>K.Y. / データ分析補助</h3>
            <p className={styles.evidenceReportMeta}>
              {report.learner} ／ {report.role}
            </p>
          </div>
          <div className={styles.evidenceReportGradeWrap}>
            <span className={styles.evidenceReportIdLabel}>証跡ID</span>
            <span className={styles.evidenceReportId}>{report.id}</span>
            <span className={styles.evidenceReportGrade}>
              <span>総合評価</span>
              <strong>{report.grade}</strong>
            </span>
          </div>
        </header>

        <section className={styles.evidenceReportFit}>
          <div>
            <p>案件適合度（必須）</p>
            <div className={styles.evidenceReportBar}>
              <span style={{ width: `${report.fitRequired}%` }} />
            </div>
            <strong>{report.fitRequired}%</strong>
          </div>
          <div>
            <p>案件適合度（歓迎）</p>
            <div className={styles.evidenceReportBar}>
              <span style={{ width: `${report.fitWelcome}%` }} />
            </div>
            <strong>{report.fitWelcome}%</strong>
          </div>
          <div>
            <p>総合適合度</p>
            <div className={styles.evidenceReportBar}>
              <span style={{ width: `${report.fitOverall}%` }} />
            </div>
            <strong>{report.fitOverall}%</strong>
          </div>
        </section>

        <section className={styles.evidenceReportSection}>
          <h4>
            <AppIcon name="target" size={14} />
            提案可能タスク
          </h4>
          <ul>
            {report.proposableTasks.map((task) => (
              <li key={task}>{task}</li>
            ))}
          </ul>
        </section>

        <section className={styles.evidenceReportSection}>
          <h4>
            <AppIcon name="fileCheck2" size={14} />
            提出物
          </h4>
          <ul>
            {report.deliverables.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>

        <section className={styles.evidenceReportSection}>
          <h4>
            <AppIcon name="gauge" size={14} />
            評価（ルーブリック）
          </h4>
          <div className={styles.evidenceReportRubric}>
            <div>
              <span>正確性</span>
              <span className={styles.evidenceReportBar}>
                <span style={{ width: `${report.rubric.accuracy}%` }} />
              </span>
              <strong>{report.rubric.accuracy}</strong>
            </div>
            <div>
              <span>再現性</span>
              <span className={styles.evidenceReportBar}>
                <span style={{ width: `${report.rubric.repeatability}%` }} />
              </span>
              <strong>{report.rubric.repeatability}</strong>
            </div>
            <div>
              <span>報告力</span>
              <span className={styles.evidenceReportBar}>
                <span style={{ width: `${report.rubric.reporting}%` }} />
              </span>
              <strong>{report.rubric.reporting}</strong>
            </div>
          </div>
        </section>

        <section className={styles.evidenceReportSection}>
          <h4>
            <AppIcon name="calendarDays" size={14} />
            改善履歴
          </h4>
          <ol className={styles.evidenceReportTimeline}>
            {report.improvements.map((entry) => (
              <li key={`${entry.date}-${entry.note}`}>
                <span>{entry.date}</span>
                <p>{entry.note}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className={`${styles.evidenceReportSection} ${styles.evidenceReportSalesSummary}`}>
          <h4>
            <AppIcon name="barChart3" size={14} />
            営業提案サマリー
          </h4>
          <p>{report.salesSummary}</p>
        </section>
      </article>

      <aside className={styles.evidenceUses} aria-label="証跡レポートの活用方法">
        {LP_EVIDENCE_REPORT_SECTION.uses.map((use) => (
          <article key={use.audience} className={styles.evidenceUseCard}>
            <h4>{use.audience}</h4>
            <ul>
              {use.bullets.map((bullet) => (
                <li key={bullet}>{bullet}</li>
              ))}
            </ul>
          </article>
        ))}
      </aside>
    </div>
  );
}
