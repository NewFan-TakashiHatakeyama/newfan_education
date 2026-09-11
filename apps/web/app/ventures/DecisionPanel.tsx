import Link from "next/link";
import type { VentureSummary, VentureDecisionRow } from "@newfan/contracts";
import { Section } from "@/app/components/ui/Section";
import styles from "./ventures.module.css";

export function DecisionPanel({ ventureId, decisions }: { ventureId: string; decisions: VentureSummary["decisions"] }) {
  const groups: [string, string, VentureDecisionRow[], string[]][] = [
    ["次の判断・未解決仮説", "hypothesis", decisions?.hypotheses ?? [], ["具体仮説/対象者", "残る不確実性", "次の実験", "再判断日", "反証・停止条件", "追加投資上限（円）"]],
    ["利用者価値・採算・停止閾値", "kpi", decisions?.kpis ?? [], ["対象/分母・窓", "目標/停止閾値", "最新実測", "実Owner", "確認日"]],
    ["条件の期限・再審査", "condition", decisions?.conditions ?? [], ["条件・制約", "Owner PersonID", "期限", "状態"]],
    ["資金計画", "cash_plan", decisions?.cashPlans ?? [], ["期首現金", "期間入金", "期間支出", "最低確保現金"]],
    ["運用・反復の期限", "task_run", decisions?.runs ?? [], ["Task ID", "開始トリガー", "予定期限", "次回期限", "Owner PersonID", "状態"]]
  ];
  return <Section title="次の事業判断" meta="未入力・未計測は未確定として表示します。停止・再審査は正本で実施してください。" theme="company">
    <p>リスク前提：{decisions?.riskState || "未確認"}</p>
    {decisions?.nextActions?.slice(0, 5).map(action => <p key={`${action.ledgerKey}/${action.rowId}`} className={action.overdue ? styles.error : undefined}>
      <Link href={`/ventures/${ventureId}/ledgers/${action.ledgerKey}`}>{action.rowId}：{action.action}</Link>
      {" — "}{action.overdue ? "期限超過・再審査要：" : "期限："}{action.dueDate || "未設定"} / 責任者：{action.owner}
    </p>)}
    {groups.map(([title, key, rows, columns]) => <div key={key}>
      <h3><Link href={`/ventures/${ventureId}/ledgers/${key}`}>{title}</Link></h3>
      {!rows.length ? <p>未入力：判断に必要な記録を作成してください。</p> : rows.map(row => <details key={row.id}>
        <summary>{row.id} — {row.values["再判断日"] || row.values["期限"] || row.values["次回期限"] || "期限未設定"} / {Object.values(row.checks).join("・")}</summary>
        <dl className={styles.detailList}>{columns.map(col => <div key={col}><dt>{col}</dt><dd>{row.values[col] || "未入力・未確定"}</dd></div>)}
          {Object.entries(row.checks).map(([col, val]) => <div key={col}><dt>{col}</dt><dd>{val || "未計測"}</dd></div>)}
        </dl>
      </details>)}
    </div>)}
  </Section>;
}
