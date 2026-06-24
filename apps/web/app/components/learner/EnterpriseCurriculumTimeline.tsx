import Link from "next/link";

import {
  ENTERPRISE_COMMON_MODULES,
  ENTERPRISE_CURRICULUM_WEEKS,
  enterpriseLessonHref
} from "@/lib/enterpriseCurriculum";
import { IconText } from "@/app/components/ui/Icon";

import styles from "@/app/components/ui/ui.module.css";

export function EnterpriseCurriculumTimeline({
  completionRate = 0
}: {
  completionRate?: number;
}) {
  const completedWeeks = Math.min(
    ENTERPRISE_CURRICULUM_WEEKS.length,
    Math.floor(completionRate * ENTERPRISE_CURRICULUM_WEEKS.length)
  );

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <ol
        className={styles.timeline}
        style={{ listStyle: "none", padding: "0 0 0 1.5rem", margin: 0 }}
        aria-label="12週間カリキュラム"
      >
        {ENTERPRISE_CURRICULUM_WEEKS.map((entry, index) => {
          const status =
            index < completedWeeks
              ? "done"
              : index === completedWeeks
                ? "current"
                : "pending";
          const dotClass =
            status === "done"
              ? styles.timelineDotDone
              : status === "pending"
                ? styles.timelineDotPending
                : "";

          return (
            <li key={entry.curriculumSlug} className={styles.timelineItem}>
              <span
                className={`${styles.timelineDot} ${dotClass}`}
                aria-hidden
              />
              <div className={styles.timelineHeader}>
                <span className={styles.evidenceMetaLabel}>
                  Week {entry.week} · {entry.phase}
                </span>
                <h3 className={styles.timelineTitle}>{entry.title}</h3>
                <span
                  className={`${styles.statusPill} ${
                    status === "done"
                      ? styles.statusPassed
                      : status === "current"
                        ? styles.statusSubmitted
                        : styles.statusUnknown
                  }`}
                >
                  {status === "done"
                    ? "完了"
                    : status === "current"
                      ? "進行中"
                      : "未開始"}
                </span>
                {entry.estimatedMinutes ? (
                  <span className={styles.timelineMeta}>
                    推定 {entry.estimatedMinutes} 分
                  </span>
                ) : null}
              </div>
              <p className={styles.timelineBody}>
                成果物: <strong>{entry.deliverable}</strong>
              </p>
              <Link
                href={enterpriseLessonHref(entry.curriculumSlug)}
                className={styles.actionGhost}
                style={{ marginTop: "0.55rem", fontSize: 12, display: "inline-flex" }}
              >
                <IconText icon="bookOpen">教材を開く</IconText>
              </Link>
            </li>
          );
        })}
      </ol>

      {ENTERPRISE_COMMON_MODULES.length > 0 ? (
        <div
          style={{
            border: "1px solid var(--border)",
            borderRadius: 16,
            padding: "0.95rem 1.1rem",
            background: "var(--surface)"
          }}
        >
          <p
            style={{
              margin: "0 0 0.65rem",
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "#64748b"
            }}
          >
            共通モジュール
          </p>
          {ENTERPRISE_COMMON_MODULES.map((mod) => (
            <div
              key={mod.curriculumSlug}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "0.75rem",
                flexWrap: "wrap"
              }}
            >
              <div>
                <strong style={{ fontSize: 14, color: "#0f172a" }}>
                  {mod.moduleCode}. {mod.title}
                </strong>
                <p style={{ margin: "0.25rem 0 0", fontSize: 12.5, color: "#475569" }}>
                  成果物: {mod.deliverable}
                  {mod.estimatedMinutes ? ` · 推定 ${mod.estimatedMinutes} 分` : ""}
                </p>
              </div>
              <Link
                href={enterpriseLessonHref(mod.curriculumSlug)}
                className={styles.actionGhost}
                style={{ fontSize: 12 }}
              >
                <IconText icon="shieldCheck">学習する</IconText>
              </Link>
            </div>
          ))}
        </div>
      ) : null}

      <p className="muted" style={{ margin: 0, fontSize: 12.5, lineHeight: 1.6 }}>
        各週の教材完了と演習提出で成果物が蓄積され、Week 12 の AIプロジェクト提案書につながります。
      </p>
    </div>
  );
}
