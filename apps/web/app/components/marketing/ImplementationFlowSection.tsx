"use client";

import { AppIcon } from "@/app/components/ui";

import styles from "./aiFieldReadyLanding.module.css";
import { LP_IMPLEMENTATION_FLOW } from "./lpContent";

export function ImplementationFlowSection() {
  return (
    <ol className={styles.implementationFlow}>
      {LP_IMPLEMENTATION_FLOW.map((step) => (
        <li key={step.step} className={styles.implementationFlowItem}>
          <span className={styles.implementationFlowStep}>{step.step}</span>
          <div>
            <h3>{step.title}</h3>
            <p>{step.body}</p>
            <span className={styles.implementationFlowPeriod}>
              <AppIcon name="clock3" size={12} />
              {step.period}
            </span>
          </div>
        </li>
      ))}
    </ol>
  );
}
