"""Application rules supplementing the read-only workbook definitions.

The workbook's reserved rows are not application capacity limits. Record identity,
verification and risk revisions belong to the application, not to worksheet cells.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

RISK_FIELDS = ("riskTier", "riskTierRationale", "conditions", "industry",
               "serviceCountries", "processingCountries", "offeringType", "summary")
VERIFICATION_FIELDS = ("正本確認者PersonID", "正本確認日時", "前提版")
PROTECTED_LEDGERS = {"eval_plan", "eval_run", "gate_run", "required_eval"}
CANCELLATION_FIELDS = {"無効化・取消理由", "取消／置換Run ID", "取消理由"}
EVENT_COLUMNS = {
    "release": {"承認日", "公開日時", "緊急権限行使日時", "事後審査期限"},
    "incident": {"検知日時", "受付日時", "復旧日時"},
    "eval_run": {"日時", "承認日"},
}


def risk_fingerprint(venture: dict) -> str:
    data = {key: venture.get(key) for key in RISK_FIELDS}
    data["riskLedgerRevision"] = (venture.get("governance") or {}).get("riskLedgerRevision", 0)
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def extend_master(raw: dict) -> dict:
    """Extend a fresh JSON load; leave the workbook and extracted baseline intact."""
    for ledger in raw["ledgers"]:
        ledger["workbook_row_limit"] = ledger.get("row_limit")
        ledger["row_limit"] = None
        key = ledger["key"]
        columns = ledger["input_columns"]
        rules = ledger.setdefault("column_rules", {})
        additions: list[str] = []
        if key == "eval_plan":
            additions += ["EvalType", "対象外理由"]
            rules["EvalType"] = {"type": "select", "options": [f"E{i:02}" for i in range(1, 19)]}
        if key in PROTECTED_LEDGERS:
            additions += list(VERIFICATION_FIELDS) + ["取消理由"]
        if key == "gate_run":
            additions += ["仮説ID", "対象期間", "取消／置換Run ID", "集合版／正本ID"]
        if key == "hypothesis":
            additions += ["対象範囲/版", "対象期間", "追加投資実績（円）", "投資実績根拠URI"]
            rules["追加投資実績（円）"] = {"type": "number", "min": 0, "options": []}
        if key == "assignment":
            additions += ["支援方法", "支援者PersonID", "支援証拠URI"]
        if key in ("unit_economics", "cash_plan", "effect"):
            additions += ["測定区分", "対象外理由"]
            rules["測定区分"] = {"type": "select", "options": ["未計測", "実測", "対象外"]}
        for column in additions:
            if column not in columns:
                columns.append(column)
        for column in EVENT_COLUMNS.get(key, set()):
            rules[column] = {"type": "datetime", "options": []}
    return raw


def record_is_final(key: str, values: dict) -> bool:
    if key in PROTECTED_LEDGERS and values.get("正本確認日時"):
        return True
    if key == "eval_plan":
        return values.get("状態") in ("承認", "対象外承認")
    if key == "eval_run":
        return values.get("人の合否") in ("合格", "不合格")
    if key == "gate_run":
        return values.get("判断結果", "") not in ("", "未審査")
    return key == "required_eval" and bool(values.get("正本確認日時"))


def task_checks(rows: list[dict], members: list[dict], basis, gate_runs: dict | None = None) -> dict[str, dict]:
    """Compute completion from evidence, accountable people and the dependency graph."""
    from infrastructure.venture_rules import parse_date
    by_id = {r["taskId"]: r for r in rows}
    active = {(m["userId"], m["roleId"]) for m in members}
    result: dict[str, dict] = {}
    visiting: set[str] = set()

    def check(task_id: str) -> dict:
        if task_id in result:
            return result[task_id]
        if task_id in visiting:
            return {"completionValid": False, "completionCheck": "循環依存"}
        row = by_id.get(task_id)
        if not row:
            return {"completionValid": False, "completionCheck": "依存ID不正"}
        visiting.add(task_id)
        verdict = "完了記録・前提充足"
        start, end = parse_date(row.get("actualStart")), parse_date(row.get("actualEnd"))
        if row["applicability"] == "対象外":
            verdict = "除外記録済" if all(row.get(k) for k in (
                "applicabilityReason", "applicabilityDecidedBy", "applicabilityDecidedAt")) else "除外承認不足"
        elif row["applicability"] != "適用":
            verdict = "適用未判定"
        elif not row.get("applicabilityDecidedBy"):
            verdict = "適用承認不足"
        elif row["status"] != "完了":
            verdict = "未完了"
        elif not all(row.get(k) for k in ("assigneeUserId", "evidenceUri", "completionApprovedBy", "completionApprovedAt")) or not start or not end:
            verdict = "完了証拠不足"
        elif start > end or end > basis:
            verdict = "実績日不正"
        elif row["roleId"] not in row.get("execRoleIds", []) or (row["assigneeUserId"], row["roleId"]) not in active:
            verdict = "実施ロール未割当"
        elif (row["completionApprovedBy"], row["approverRoleId"]) not in active:
            verdict = "承認ロール未割当"
        elif row["approverRoleId"] == "R19" and row["completionApprovedBy"] == row["assigneeUserId"]:
            verdict = "独立承認不足"
        elif row.get("dependencyCheck") not in ("標準依存", "記法OK", "依存なし"):
            verdict = row.get("dependencyCheck") or "依存確認不足"
        else:
            approved = row.get("completionApprovedAt", "")[:10]
            applied = row.get("applicabilityDecidedAt", "")[:10]
            if (parse_date(approved) and parse_date(approved) > basis) or (parse_date(applied) and parse_date(applied) > basis):
                verdict = "実績・承認日不正"
            elif approved < row["actualEnd"] or applied > row["actualStart"]:
                verdict = "完了・適用日逆転"
            elif task_id == "B6-01" and not any(v.get("判断結果") == "Stop" and v.get("正本確認日時") and v.get("正本決裁URI") and not any(v.get(k) for k in CANCELLATION_FIELDS) for v in (gate_runs or {}).values()):
                verdict = "Stop判断参照不足"
            elif any(check(dep)["completionCheck"] not in ("完了記録・前提充足", "除外記録済") for dep in row["dependsOn"]):
                verdict = "前提未充足"
        visiting.remove(task_id)
        result[task_id] = {"completionValid": verdict == "完了記録・前提充足", "completionCheck": verdict}
        return result[task_id]
    for task_id in by_id:
        check(task_id)
    return result


# Exact values only. Unknown/new verdicts never become success by substring.
SUCCESS_VERDICTS = {
    "計画記録あり", "対象外計画記録", "計画・構成一致", "記録あり・内容審査別",
    "必須・合格Run記録", "承認済み対象外", "日時整合", "決裁・構成一致",
    "準備記録整合・実行許可は正本", "記録あり・公開判断別", "条件整合",
    "解消確認済", "期限内・制約継続", "整合済・正本決裁要確認", "判定整合",
    "必須評価セット充足", "G0仮説記録接続", "資産処理決定充足", "記録あり",
    "仮説記録あり", "処理完了記録済", "対象外決定記録済", "保全継続・決定記録済",
    "割当記録あり", "稼働記録あり", "Run記録あり・内容審査別",
    "記録あり・採算判断別", "記録あり・採用判断別", "限定採用判断記録・一般化不可",
}


VERDICT_CODES = {
    "計画記録あり": "PLAN_COMPLETE", "対象外計画記録": "PLAN_EXCLUDED",
    "計画・構成一致": "PLAN_MANIFEST_MATCH", "記録あり・内容審査別": "RUN_RECORDED",
    "必須・合格Run記録": "REQUIRED_RUN_PASSED", "承認済み対象外": "EVALUATION_EXCLUDED",
    "必須評価セット充足": "EVALUATION_SET_COMPLETE", "整合済・正本決裁要確認": "GATE_CHECKS_COMPLETE",
    "準備記録整合・実行許可は正本": "RELEASE_CHECKS_COMPLETE", "決裁・構成一致": "RELEASE_DECISION_MATCH",
    "決裁整合未充足": "RELEASE_DECISION_INCOMPLETE", "決裁対象・版不一致": "RELEASE_SCOPE_MISMATCH",
    "Manifest不一致": "MANIFEST_MISMATCH", "必須分類・集合不足": "EVALUATION_CLASSIFICATIONS_MISSING",
    "評価記録未充足": "EVALUATION_RECORD_INCOMPLETE", "必須評価セット未充足": "EVALUATION_SET_INCOMPLETE",
    "正本決裁未確認": "SOURCE_DECISION_UNVERIFIED", "リスク・前提再確認要": "RISK_RECONFIRMATION_REQUIRED",
    "無効化Run": "EVALUATION_RUN_REVOKED", "取消・置換済": "DECISION_REVOKED",
    "未計測・必要入力不足": "MEASUREMENT_MISSING", "未計測": "UNMEASURED",
    "時差付き日時で再確認要": "EVENT_PRECISION_MISSING", "実施ロール未割当": "ROLE_UNASSIGNED",
    "能力の第三者確認不足": "ASSESSMENT_UNVERIFIED", "未充足": "REQUIREMENTS_INCOMPLETE",
    "記録あり": "RECORD_COMPLETE", "仮説記録あり": "HYPOTHESIS_COMPLETE",
    "日時整合": "EVENT_ORDER_VALID", "条件整合": "CONDITIONS_VALID", "判定整合": "DECISION_CONSISTENT",
    "解消確認済": "CONDITION_RESOLVED", "期限内・制約継続": "CONDITION_ACTIVE",
    "G0仮説記録接続": "HYPOTHESIS_CONNECTED", "資産処理決定充足": "ASSET_DECISIONS_COMPLETE",
    "記録あり・公開判断別": "RELEASE_RECORD_COMPLETE", "処理完了記録済": "RETIREMENT_COMPLETE",
    "対象外決定記録済": "ASSET_EXCLUDED", "保全継続・決定記録済": "ASSET_PRESERVED",
    "割当記録あり": "ASSIGNMENT_COMPLETE", "稼働記録あり": "STAFFING_COMPLETE",
    "Run記録あり・内容審査別": "TASK_RUN_COMPLETE", "記録あり・採算判断別": "UNIT_COST_RECORDED",
    "記録あり・採用判断別": "EFFECT_RECORDED", "限定採用判断記録・一般化不可": "EFFECT_ADOPTED_WITH_LIMITS",
}


def check_statuses(derived: dict[str, str]) -> dict[str, dict[str, str]]:
    return {key: {"code": VERDICT_CODES.get(value, "UNCLASSIFIED_REQUIRES_REVIEW"),
                  "severity": "success" if value in SUCCESS_VERDICTS else "warning",
                  "label": value} for key, value in derived.items()}
