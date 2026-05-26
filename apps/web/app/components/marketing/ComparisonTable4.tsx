"use client";

import styles from "./aiFieldReadyLanding.module.css";
import { LP_COMPARISON } from "./lpContent";

export function ComparisonTable4() {
  const highlightIndex = LP_COMPARISON.columns.length - 1;

  return (
    <div className={styles.comparisonScroll}>
      <table className={styles.comparisonTable}>
        <thead>
          <tr>
            <th scope="col">比較軸</th>
            {LP_COMPARISON.columns.map((col, index) => (
              <th
                key={col}
                scope="col"
                className={index === highlightIndex ? styles.comparisonHeadHighlight : ""}
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {LP_COMPARISON.rows.map((row) => (
            <tr key={row.label}>
              <th scope="row">{row.label}</th>
              {row.values.map((value, index) => (
                <td
                  key={`${row.label}-${index}`}
                  className={index === highlightIndex ? styles.comparisonCellHighlight : ""}
                >
                  {value}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
