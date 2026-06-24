import styles from "./aiFieldReadyLanding.module.css";
import { LP_USE_CASES } from "./lpContent";

export function UseCasesSection() {
  return (
    <div className={styles.useCaseGrid}>
      {LP_USE_CASES.cases.map((item) => (
        <article key={item.industry} className={styles.useCaseCard}>
          <h3>{item.industry}</h3>
          <div>
            <span className={styles.useCaseLabel}>AIテーマ例</span>
            <p>{item.theme}</p>
          </div>
          <div>
            <span className={styles.useCaseLabel}>成果物例</span>
            <p>{item.deliverable}</p>
          </div>
        </article>
      ))}
    </div>
  );
}
