import type { VentureLedgerEntry } from "@newfan/contracts";
import styles from "./ventures.module.css";

/** Missing classifications stay visible even before the first evaluation row exists. */
export function EvaluationCoverage({ entries }: { entries: VentureLedgerEntry[] }) {
  const groups = new Map<string, VentureLedgerEntry[]>();
  for (const row of entries) {
    const key = ["Release ID", "ManifestHash", "集合版／正本ID"].map(k => row.values[k] || "未設定").join(" / ");
    groups.set(key, [...(groups.get(key) ?? []), row]);
  }
  if (!groups.size) groups.set("公開対象・集合版未設定", []);
  return <section aria-label="18評価分類の充足状況">
    <h3>公開対象・集合版ごとの18評価分類</h3>
    {[...groups].map(([target, rows]) => <details key={target} open>
      <summary>{target}</summary>
      <div className={styles.toolbar}>{Array.from({ length: 18 }, (_, i) => {
        const type = `E${String(i + 1).padStart(2, "0")}`;
        const matching = rows.filter(r => r.derived["EvalType（参照）"] === type);
        const complete = matching.length === 1 && matching[0].derived["充足フラグ"] === "1";
        const state = !matching.length ? "未判定" : matching.length > 1 ? "重複・確認要" : complete ? "充足" : "未充足";
        return <span key={type} className={`${styles.pill} ${complete ? styles.pillDone : styles.pillProgress}`}>{type}：{state}</span>;
      })}</div>
    </details>)}
  </section>;
}
