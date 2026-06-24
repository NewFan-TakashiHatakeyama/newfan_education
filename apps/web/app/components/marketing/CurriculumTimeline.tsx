"use client";

import { useEffect, useRef, useState } from "react";

import { AppIcon } from "@/app/components/ui";

import { trackLpEvent } from "@/lib/lp-analytics";

import styles from "./aiFieldReadyLanding.module.css";
import { LP_CURRICULUM_TIMELINE } from "./lpContent";

export function CurriculumTimeline({ reducedMotion }: { reducedMotion: boolean }) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [scrollProgress, setScrollProgress] = useState(reducedMotion ? 1 : 0);
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (reducedMotion) return;
    const node = ref.current;
    if (!node) return;

    const update = () => {
      const rect = node.getBoundingClientRect();
      const viewport = window.innerHeight || 1;
      const total = rect.height + viewport * 0.4;
      const passed = viewport - rect.top;
      const ratio = Math.min(1, Math.max(0, passed / total));
      setScrollProgress(ratio);
      const index = Math.min(
        LP_CURRICULUM_TIMELINE.phases.length - 1,
        Math.floor(ratio * LP_CURRICULUM_TIMELINE.phases.length)
      );
      setActiveIndex(index);
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
  const activePhase = LP_CURRICULUM_TIMELINE.phases[activeIndex];

  return (
    <div ref={ref} className={styles.curriculumTimeline}>
      <div className={styles.curriculumTimelineScroll} role="list" aria-label="12週間カリキュラム">
        {LP_CURRICULUM_TIMELINE.phases.map((phase, index) => {
          const reached = progress >= (index + 0.3) / LP_CURRICULUM_TIMELINE.phases.length;
          const isActive = activeIndex === index;
          return (
            <button
              key={phase.week}
              type="button"
              role="listitem"
              className={`${styles.curriculumPhaseCard} ${reached ? styles.curriculumPhaseReached : ""} ${isActive ? styles.curriculumPhaseActive : ""}`}
              onClick={() => {
                setActiveIndex(index);
                trackLpEvent("curriculum_week_opened", { week: phase.week });
              }}
            >
              <span className={styles.curriculumPhaseWeek}>{phase.week}</span>
              <strong>{phase.label}</strong>
              <small>{phase.deliverable}</small>
            </button>
          );
        })}
      </div>

      <article className={styles.curriculumPhaseDetail} aria-live="polite">
        <p className={styles.curriculumPhaseDetailEyebrow}>
          <AppIcon name="bookOpen" size={14} />
          {activePhase.week} — {activePhase.label}
        </p>
        <p>{activePhase.body}</p>
        <div className={styles.curriculumDeliverable}>
          <span>成果物</span>
          <strong>{activePhase.deliverable}</strong>
        </div>
      </article>
    </div>
  );
}
