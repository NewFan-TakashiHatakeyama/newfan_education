import styles from "./aiFieldReadyLanding.module.css";
import { LP_REVIEW_SYSTEM } from "./lpContent";

export function ReviewSystemSection() {
  return (
    <div className={styles.reviewSystem}>
      <div className={styles.reviewSystemGrid}>
        {LP_REVIEW_SYSTEM.reviews.map((review) => (
          <article key={review.type} className={styles.reviewSystemCard}>
            <h3>{review.type}</h3>
            <p>{review.body}</p>
          </article>
        ))}
      </div>

      <div className={styles.reviewRubric}>
        <h3>評価ルーブリック例</h3>
        <table className={styles.reviewRubricTable}>
          <thead>
            <tr>
              <th>評価軸</th>
              <th>評価内容</th>
            </tr>
          </thead>
          <tbody>
            {LP_REVIEW_SYSTEM.rubric.map((row) => (
              <tr key={row.axis}>
                <td>{row.axis}</td>
                <td>{row.body}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
