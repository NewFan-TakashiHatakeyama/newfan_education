/** Display labels only. Stored ledger column keys and role IDs remain unchanged. */
const LABELS: Record<string, string> = {
  "Owner PersonID": "責任者のユーザーID",
  "確認者PersonID": "確認者のユーザーID",
  "正本確認者PersonID": "独立確認者のユーザーID",
  "正本確認日時": "独立確認の日時",
  "正本URI": "根拠資料のリンク",
  "証拠URI": "証拠のリンク",
  "Task ID": "タスクID",
  "GateRun ID": "承認記録ID",
  "実Owner": "責任者",
  "前提版": "前提条件の版"
};

export function ledgerLabel(key: string) { return LABELS[key] ?? key; }
