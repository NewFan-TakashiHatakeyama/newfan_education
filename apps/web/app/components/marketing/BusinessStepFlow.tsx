"use client";

import { useEffect, useRef, useState } from "react";

import styles from "@/app/components/ui/ui.module.css";

export type BusinessStep = {
  index: string;
  title: string;
  body: string;
};

type BusinessStepFlowProps = {
  steps: BusinessStep[];
};

function StepCard({
  step,
  visible,
  delayMs
}: {
  step: BusinessStep;
  visible: boolean;
  delayMs: number;
}) {
  return (
    <li
      className={`${styles.stepCard} ${visible ? styles.stepCardVisible : ""}`}
      data-step={step.index}
      style={{ animationDelay: `${delayMs}ms` }}
    >
      <span className={styles.stepCardIndex}>
        <span className={styles.stepCardIndexNum}>{step.index}</span>
        STEP
      </span>
      <h3 className={styles.stepCardTitle}>{step.title}</h3>
      <p className={styles.stepCardBody}>{step.body}</p>
    </li>
  );
}

export function BusinessStepFlow({ steps }: BusinessStepFlowProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = containerRef.current;
    if (!node) return;

    if (typeof IntersectionObserver === "undefined") {
      const frame = requestAnimationFrame(() => setVisible(true));
      return () => cancelAnimationFrame(frame);
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  const rowOne = steps.slice(0, 3);
  const rowTwo = steps.slice(3, 6);

  return (
    <div
      ref={containerRef}
      className={`${styles.stepFlowContainer} ${visible ? styles.stepFlowVisible : ""}`}
    >
      <ol className={styles.stepFlowRow} aria-label="業務フロー 1〜3">
        {rowOne.map((step, i) => (
          <StepCard key={step.index} step={step} visible={visible} delayMs={80 + i * 90} />
        ))}
      </ol>

      <ol className={styles.stepFlowRow} aria-label="業務フロー 4〜6">
        {rowTwo.map((step, i) => (
          <StepCard key={step.index} step={step} visible={visible} delayMs={350 + i * 90} />
        ))}
      </ol>
    </div>
  );
}
