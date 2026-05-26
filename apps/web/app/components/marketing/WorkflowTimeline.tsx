"use client";

import { useEffect, useRef, useState } from "react";

import { AppIcon } from "@/app/components/ui";

import styles from "./aiFieldReadyLanding.module.css";
import { LP_WORKFLOW } from "./lpContent";

export function WorkflowTimeline({ reducedMotion }: { reducedMotion: boolean }) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    if (reducedMotion) {
      return;
    }
    const node = ref.current;
    if (!node) {
      return;
    }

    const update = () => {
      const rect = node.getBoundingClientRect();
      const viewport = window.innerHeight || 1;
      const total = rect.height + viewport * 0.4;
      const passed = viewport - rect.top;
      const ratio = Math.min(1, Math.max(0, passed / total));
      setScrollProgress(ratio);
    };

    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [reducedMotion]);

  const progress = reducedMotion ? 1 : scrollProgress;

  return (
    <div ref={ref} className={styles.workflowTimelineWrap}>
      <div className={styles.workflowTimelineTrackWrap} aria-hidden>
        <div className={styles.workflowTimelineTrack}>
          <div
            className={styles.workflowTimelineFill}
            style={{ width: `${progress * 100}%` }}
          />
        </div>
      </div>
      <ol className={styles.workflowTimelineList}>
        {LP_WORKFLOW.map((step, index) => {
          const stepProgress = (index + 0.4) / LP_WORKFLOW.length;
          const reached = progress >= stepProgress || reducedMotion;
          return (
            <li
              key={step.id}
              className={`${styles.workflowTimelineItem} ${reached ? styles.workflowTimelineItemReached : ""}`}
            >
              <span className={styles.workflowTimelineNode}>
                <AppIcon name={step.icon} size={14} />
              </span>
              <div className={styles.workflowTimelineBody}>
                <p className={styles.workflowTimelineLabel}>STEP {index + 1}</p>
                <h3>{step.title}</h3>
                <p>{step.body}</p>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
