"""台帳の記録点検。

原本は台帳ごとに「記録点検」列を数式で持ち、状態に応じて必要な欄が揃っているかを
判定している（15!W・16!S/Y・20!U/AG/AH・21!Q・22!O/U/V/W・25!AE）。
Excelの数式は移せないので、同じ節順をここに書き写す。

**判定文字列は原本の語をそのまま使う。** 「復旧記録不足」「承認前の通常公開」などは
原本の数式が返す値であり、言い換えない。

**拒否と点検は分ける。** その値だけで不正と決まるもの（重複・未来日・前後逆転・語彙外）は
書き込みを400で拒否する。他欄が未記入という途中経過は拒否せず、点検値として示す。
原本 00 の「記録・参照・日時・定義整合を点検」に合わせる。
"""
from __future__ import annotations

import re
import math
from dataclasses import dataclass, field
from datetime import date

from infrastructure.venture_rules import parse_date, parse_timestamp

# 台帳ごとの点検列名（原本の見出し）
CHECK_COLUMNS: dict[str, list[str]] = {
    "eval_plan": ["計画記録点検"],
    "eval_run": ["凍結計画Key照合", "記録点検"],
    "release": ["記録点検", "日時点検", "公開準備点検"],
    "incident": ["状態・日時点検"],
    "retirement": ["点検", "実削除フラグ", "保全継続フラグ", "資産処理決定フラグ"],
    "hypothesis": ["仮説記録点検"],
    "condition": ["条件点検"],
    "required_eval": ["EvalType（参照）", "評価判定（参照）", "接続点検", "充足フラグ"],
    "effect": [
        "AI人時間計", "純削減人時間", "純削減率", "経過短縮率",
        "追加費合計", "純経済効果", "点検", "見積採用点検",
    ],
    "unit_economics": [
        "純売上", "変動費計", "限界利益", "限界利益率", "簡易営業収支",
        "成功業務あたり変動原価", "固定費配賦込み単位費用", "入力点検",
    ],
    "cash_plan": ["期末現金", "不足額"],
    "gate_run": [
        "判断対象", "標準Task", "最終A Role", "必要証拠の定義",
        "記録点検", "判定整合", "必須評価・前提点検", "条件点検", "有効性点検",
    ],
    "task_run": ["名称（参照）", "Run記録点検"],
    "assignment": [
        "Task名（参照）", "Skill名（参照）", "評価Lv（参照）", "能力不足Lv", "割当点検",
    ],
    "role_staffing": ["不足FTE", "当日合計FTE", "稼働点検"],
}

# この判定値になる書き込みは入口で拒否する。
BLOCKING_VERDICTS: dict[str, set[str]] = {
    "eval_plan": {"EvalType不正", "PlanKey不足・重複", "状態不正"},
    "eval_run": {"Run ID重複", "実績日時不正", "評価承認日時逆転"},
    "release": {
        "Release ID重複",
        "実績日時不正",
        "承認前の通常公開",
        "緊急時刻不正",
        "運用適用値不正",
    },
    "incident": {"Incident ID重複", "実績日時不正", "時刻不正", "状態不正"},
    "retirement": {"処理実績日不正", "処理確認日逆転"},
    "hypothesis": {"GateRun不正"},
    "condition": set(),
    "required_eval": {"PlanKey不正", "評価対象不一致"},
    "effect": {"入力値不正"},
    "unit_economics": {"入力値不正", "試行数不整合"},
    "cash_plan": set(),
    "gate_run": {"判断Run ID重複", "Gate不正", "実績日時不正"},
    "task_run": {"TaskRun ID重複", "Task ID不正", "Run実績日不正", "確認日逆転"},
    "assignment": {"ID不正"},
    "role_staffing": set(),
}


@dataclass(slots=True)
class CheckContext:
    """点検に必要な案件側の文脈。"""

    as_of: date
    row_key: str
    #: 同じ台帳の他の行（行キー -> 値）。重複検査に使う。
    siblings: dict[str, dict[str, str]] = field(default_factory=dict)
    #: eval_plan の PlanKey -> その行の値。eval_run と 30 の参照整合に使う。
    eval_plans: dict[str, dict[str, str]] = field(default_factory=dict)
    #: eval_run の Run ID -> その行の値。30 の合否参照に使う。
    eval_runs: dict[str, dict[str, str]] = field(default_factory=dict)
    #: 案件のゲート判断行のID集合。仮説の承認記録IDの解決に使う。
    gate_row_ids: set[str] = field(default_factory=set)
    assessment_records: dict[str, dict] = field(default_factory=dict)
    member_roles: set[tuple[str, str]] = field(default_factory=set)
    #: マスタの評価分類ID（E01〜E18）。
    eval_type_ids: set[str] = field(default_factory=set)
    #: 他の台帳の行（台帳キー -> 行キー -> 値）。台帳間の参照整合に使う。
    related: dict[str, dict[str, dict[str, str]]] = field(default_factory=dict)
    #: マスタの索引（task_ids / role_ids / skill_ids / gate_ids）。
    master_ids: dict[str, set[str]] = field(default_factory=dict)
    #: 案件のスキル評価（skill_id -> user_id -> 到達Lv）。
    assessments: dict[str, dict[str, int]] = field(default_factory=dict)
    venture: dict = field(default_factory=dict)
    tasks: dict[str, dict] = field(default_factory=dict)

    def rows(self, ledger_key: str) -> dict[str, dict[str, str]]:
        return self.related.get(ledger_key, {})


def _blank(values: dict[str, str], *columns: str) -> bool:
    """指定した列のどれかが空なら True。"""
    return any(not (values.get(column) or "").strip() for column in columns)


def _future(values: dict[str, str], context: CheckContext, *columns: str) -> bool:
    """指定した列のどれかが管理基準日より未来なら True。空欄は見ない。"""
    for column in columns:
        parsed = parse_date(values.get(column))
        if parsed is not None and parsed > context.as_of:
            return True
    return False

def _unreadable(values: dict[str, str], *columns: str) -> bool:
    """値が入っているのに日付として読めない列があるなら True。"""
    for column in columns:
        raw = (values.get(column) or "").strip()
        if raw and parse_date(raw) is None:
            return True
    return False


def _both(values: dict[str, str], first: str, second: str) -> tuple[date, date] | None:
    if "T" in (values.get(first) or "") or "T" in (values.get(second) or ""):
        a, b = parse_timestamp(values.get(first)), parse_timestamp(values.get(second))
        return (a, b) if a is not None and b is not None else None
    a = parse_date(values.get(first))
    b = parse_date(values.get(second))
    return (a, b) if a is not None and b is not None else None


def _duplicated(context: CheckContext) -> bool:
    """同じ行キーが案件内に既にあるか。"""
    return context.row_key in context.siblings


# ── 15_評価計画・品質ゲート ───────────────────────────
def plan_key(values: dict[str, str]) -> str:
    """原本15の PlanKey（自動）= EvalPlan ID & '@' & 計画版。"""
    plan_id = (values.get("EvalPlan ID") or "").strip()
    version = (values.get("計画版") or "").strip()
    return f"{plan_id}@{version}" if plan_id and version else ""


def _check_eval_plan(values: dict[str, str], context: CheckContext) -> dict[str, str]:
    # 点検行は EvalType（E01〜E18）を行キーに持つ。案件が版ごとに足す行は
    # PlanKey（EP-001@2 形式）を行キーにするので、EvalType は値から取る。
    # 点検行は EvalType（E01〜E18）を行キーに持つ。案件が版ごとに足す行の行キーは
    # PlanKey（EP-001@2 形式）なので、E形式でなければ EvalType 未設定として扱う。
    eval_type = (values.get("EvalType") or "").strip()
    if not re.fullmatch(r"E\d+", eval_type):
        eval_type = ""
    if eval_type and context.eval_type_ids and eval_type not in context.eval_type_ids:
        return {"計画記録点検": "EvalType不正"}
    key = plan_key(values)
    if not key or any(
        plan_key(row) == key for row_key, row in context.siblings.items() if row_key != context.row_key
    ):
        return {"計画記録点検": "PlanKey不足・重複"}
    state = (values.get("状態") or "").strip()
    if values.get("取消理由"):
        return {"計画記録点検": "取消済み計画"}
    if state in ("", "未設定", "設計中", "改訂中"):
        return {"計画記録点検": "計画未確定"}
    if state not in ("承認", "対象外承認"):
        return {"計画記録点検": "状態不正"}
    if not eval_type:
        return {"計画記録点検": "EvalType不足"}
    if _blank(values, "対象機能／業務", "対象ManifestHash", "計画承認URI"):
        return {"計画記録点検": "計画対象・承認不足"}
    if state == "対象外承認":
        if _blank(values, "対象外理由") and _blank(values, "母集団/分母（入力）"):
            return {"計画記録点検": "対象外理由不足"}
        return {"計画記録点検": "対象外計画記録"}
    if _blank(
        values,
        "母集団/分母（入力）",
        "slice/標本/反復",
        "比較対象・版",
        "合格閾値/方向",
        "重大失敗条件",
        "評価Data ID/凍結版",
        "grader/較正方式",
        "独立評価者",
    ):
        return {"計画記録点検": "評価設計不足"}
    # E05（Agent評価）は試行状態とResetの定義まで要る（原本AR23）
    if eval_type == "E05" and _blank(
        values, "初期状態／Fixture定義URI", "Reset・副作用検査", "試行成功率の定義"
    ):
        return {"計画記録点検": "試行状態・成功定義不足"}
    return {"計画記録点検": "計画記録あり"}


# ── 16_評価実績インデックス ───────────────────────────
def _check_eval_run(values: dict[str, str], context: CheckContext) -> dict[str, str]:
    # 凍結計画Key照合（原本16!Y）
    referenced_key = (values.get("EvalPlanKey") or "").strip()
    plan = context.eval_plans.get(referenced_key)
    if plan is None:
        match = {"凍結計画Key照合": "PlanKey不正"}
    elif _blank(values, "ManifestHash") or (values.get("ManifestHash") or "").strip() != (
        plan.get("対象ManifestHash") or ""
    ).strip():
        match = {"凍結計画Key照合": "Manifest不一致"}
    elif _check_eval_plan(plan, CheckContext(as_of=context.as_of, row_key=referenced_key,
                                             eval_type_ids=context.eval_type_ids))["計画記録点検"] != "計画記録あり":
        match = {"凍結計画Key照合": "計画未承認・不足"}
    else:
        match = {"凍結計画Key照合": "計画・構成一致"}

    if _duplicated(context):
        return {**match, "記録点検": "Run ID重複"}
    if match["凍結計画Key照合"] != "計画・構成一致":
        return {**match, "記録点検": match["凍結計画Key照合"]}
    if not _blank(values, "無効化・取消理由") or values.get("取消理由"):
        return {**match, "記録点検": "無効化Run"}
    if any(values.get(col) and parse_timestamp(values[col]) is None for col in ("日時", "承認日")):
        return {**match, "記録点検": "時差付き日時で再確認要"}
    if _blank(
        values,
        "対象Release/Issue",
        "Model版",
        "Prompt/Policy版",
        "Data/Evalセット版",
        "Tool/Skill/Runtime版",
        "母集団/slice/試行数",
        "実測/区間/単位",
        "採点者/方式",
        "独立確認者",
        "証拠URI",
        "ManifestHash",
        "重大失敗/未解決",
    ) or _both(values, "日時", "承認日") is None:
        return {**match, "記録点検": "記録不足"}
    if _future(values, context, "日時", "承認日") or _unreadable(values, "日時", "承認日"):
        return {**match, "記録点検": "実績日時不正"}
    pair = _both(values, "承認日", "日時")
    if pair and pair[0] < pair[1]:
        return {**match, "記録点検": "評価承認日時逆転"}
    if _blank(values, "実行者PersonID", "独立確認者PersonID") or (
        (values.get("実行者PersonID") or "").strip() == (values.get("独立確認者PersonID") or "").strip()
    ):
        return {**match, "記録点検": "独立確認Person不足"}
    if plan is not None and (plan.get("EvalType") or "").strip() == "E05" and _blank(
        values, "Trial／初期状態・副作用URI"
    ):
        return {**match, "記録点検": "Trial状態証拠不足"}
    if (values.get("人の合否") or "").strip() in ("", "未判定", "無効/再実行"):
        return {**match, "記録点検": "評価判定未確定"}
    return {**match, "記録点検": "記録あり・内容審査別"}


# ── 20_リリース・変更・ロールバック ───────────────────
def _check_release(values: dict[str, str], context: CheckContext) -> dict[str, str]:
    change_type = (values.get("変更区分") or "").strip()
    state = (values.get("状態") or "").strip()

    # 日時点検（原本20!AG）
    if _future(values, context, "承認日", "公開日時", "緊急権限行使日時") or _unreadable(
        values, "承認日", "公開日時", "緊急権限行使日時"
    ):
        timing = "実績日時不正"
    elif state in ("展開中", "安定確認") and parse_date(values.get("公開日時")) is None:
        timing = "公開日時不足"
    elif change_type == "Emergency":
        if _blank(values, "緊急例外／手順ID", "緊急権限者") or _both(
            values, "事後審査期限", "緊急権限行使日時"
        ) is None:
            timing = "緊急根拠不足"
        else:
            published = parse_timestamp(values.get("公開日時"))
            used = parse_timestamp(values.get("緊急権限行使日時"))
            review_due = parse_timestamp(values.get("事後審査期限"))
            if published and ((used and used > published) or (review_due and review_due < published)):
                timing = "緊急時刻不正"
            elif review_due and review_due.date() < context.as_of and _blank(values, "事後審査URI"):
                timing = "事後審査期限超過"
            else:
                timing = "緊急経路・正本審査要"
    else:
        pair = _both(values, "承認日", "公開日時")
        timing = "承認前の通常公開" if pair and pair[0] > pair[1] else "日時整合"

    # 記録点検（原本20!U）
    if _duplicated(context):
        record = "Release ID重複"
    elif change_type in ("", "未判定"):
        record = "変更区分未分類"
    elif change_type == "Major" and _blank(values, "Major該当理由"):
        record = "変更理由不足"
    elif state in ("", "草案", "審査中"):
        record = "草案・未審査"
    elif _blank(
        values,
        "旧/新manifest URI",
        "Model/Prompt/Data/Tool/Skill版",
        "独立品質判定URI",
        "Privacy/Security判定URI",
        "段階展開/対象者",
        "成功/停止指標",
        "監視担当",
        "Rollback/補償URI",
        "最終承認者",
    ) or parse_date(values.get("承認日")) is None:
        record = "公開根拠不足"
    else:
        operation = (values.get("運用CS適用") or "").strip()
        if operation in ("", "未判定"):
            record = "運用CS適用未判定"
        elif operation == "必要" and _blank(values, "運用/CS準備URI"):
            record = "運用CS準備不足"
        elif operation == "対象外" and _blank(values, "対象外理由", "対象外承認URI"):
            record = "運用対象外承認不足"
        elif operation not in ("必要", "対象外"):
            record = "運用適用値不正"
        elif timing not in ("日時整合", "緊急経路・正本審査要"):
            record = timing
        else:
            record = "記録あり・公開判断別"

    # 公開準備点検（原本20!AH）
    if record != "記録あり・公開判断別":
        ready = record
    elif state in ("停止", "ロールバック", "終了"):
        ready = "公開継続しない状態"
    elif change_type == "Emergency":
        ready = "緊急措置・通常公開許可ではない"
    else:
        ready = "準備記録整合・実行許可は正本"
    # 決裁・版接続点検（原本20!AF）。GateRunの有効性と対象版を突き合わせる。
    gate_run_id = (values.get("GateRun ID") or "").strip()
    gate_run = context.rows("gate_run").get(gate_run_id)
    conditions = [
        row
        for row in context.rows("condition").values()
        if (row.get("GateRun ID") or "").strip() == gate_run_id and gate_run_id
    ]
    if not gate_run_id or gate_run is None:
        approval = "GateRun不足・不正"
    else:
        gate_derived = _check_gate_run(gate_run, CheckContext(
            as_of=context.as_of, row_key=gate_run_id, related=context.related,
            master_ids=context.master_ids, eval_type_ids=context.eval_type_ids,
            eval_plans=context.eval_plans, eval_runs=context.eval_runs,
            venture=context.venture, tasks=context.tasks,
        ))
        effective = gate_derived["有効性点検"]
        if effective == "取消・置換済":
            approval = "決裁整合未充足"
        elif (gate_run.get("Release ID") or "").strip() != context.row_key or (
            (gate_run.get("ManifestHash") or "").strip()
            != (values.get("公開ManifestHash") or "").strip()
        ):
            approval = "決裁対象・版不一致"
        elif effective != "整合済・正本決裁要確認" or gate_run.get("Gate") != "G3" or gate_run.get("判断結果") not in ("承認", "条件付承認"):
            approval = "決裁整合未充足"
        else:
            approval = "決裁・構成一致"

    if ready == "準備記録整合・実行許可は正本" and approval != "決裁・構成一致":
        ready = approval
    return {
        "記録点検": record,
        "条件件数（参照）": str(len(conditions)),
        "決裁・版接続点検": approval,
        "日時点検": timing,
        "公開準備点検": ready,
    }


# ── 21_インシデント記録 ───────────────────────────────
def _check_incident(values: dict[str, str], context: CheckContext) -> dict[str, str]:
    if _duplicated(context):
        return {"状態・日時点検": "Incident ID重複"}
    if _future(values, context, "検知日時", "受付日時", "復旧日時") or _unreadable(
        values, "検知日時", "受付日時", "復旧日時"
    ):
        return {"状態・日時点検": "実績日時不正"}
    accepted = _both(values, "受付日時", "検知日時")
    recovered = _both(values, "復旧日時", "受付日時")
    if (accepted and accepted[0] < accepted[1]) or (recovered and recovered[0] < recovered[1]):
        return {"状態・日時点検": "時刻不正"}
    if _blank(values, "概要・利用者影響", "重大度/境界", "Owner", "状態") or _both(
        values, "検知日時", "受付日時"
    ) is None:
        return {"状態・日時点検": "受付情報不足"}
    state = (values.get("状態") or "").strip()
    if state == "受付":
        return {"状態・日時点検": "受付記録あり・未復旧"}
    if state in ("調査中", "対応中", "封じ込め"):
        return {"状態・日時点検": "対応中・未復旧"}
    if state in ("復旧", "解決", "再発防止中"):
        if parse_date(values.get("復旧日時")) is None or _blank(
            values, "封じ込め/手動対応", "manifest/trace URI"
        ):
            return {"状態・日時点検": "復旧記録不足"}
        if state in ("解決", "再発防止中") and _blank(
            values, "原因/不確実性", "救済/通知/法務", "再発防止Issue/Eval", "Postmortem URI"
        ):
            return {"状態・日時点検": "解決・是正記録不足"}
        if state == "復旧":
            return {"状態・日時点検": "復旧記録あり・原因審査継続"}
        return {"状態・日時点検": "解決記録あり・再発防止を追跡"}
    return {"状態・日時点検": "状態不正"}


# ── 22_廃止・移管・削除 ───────────────────────────────
def _check_retirement(values: dict[str, str], context: CheckContext) -> dict[str, str]:
    def flags(verdict: str) -> dict[str, str]:
        # 原本22!U/V/W。保全継続を削除済みと同じ数え方にしない。
        deleted = verdict == "処理完了記録済" and (values.get("処理（削除/保全等）") or "").strip() == "削除"
        preserved = verdict == "保全継続・決定記録済"
        decided = verdict in ("処理完了記録済", "対象外決定記録済", "保全継続・決定記録済")
        return {
            "点検": verdict,
            "実削除フラグ": "1" if deleted else "0",
            "保全継続フラグ": "1" if preserved else "0",
            "資産処理決定フラグ": "1" if decided else "0",
        }

    if _future(values, context, "実施日", "確認日") or _unreadable(values, "実施日", "確認日"):
        return flags("処理実績日不正")
    pair = _both(values, "確認日", "実施日")
    if pair and pair[0] < pair[1]:
        return flags("処理確認日逆転")
    state = (values.get("状態") or "").strip()
    if state == "対象外承認":
        if _blank(values, "期限/保持根拠", "独立確認者", "確認日", "証拠URI"):
            return flags("対象外承認不足")
        return flags("対象外決定記録済")
    if state == "保全継続":
        if _blank(
            values, "実資産ID/範囲", "期限/保持根拠", "独立確認者", "証拠URI", "保全Owner PersonID",
            "保全アクセス条件",
        ) or any(
            parse_date(values.get(column)) is None
            for column in ("確認日", "保全終了／見直し期限", "次回確認日")
        ):
            return flags("保全条件不足")
        for column in ("保全終了／見直し期限", "次回確認日"):
            due = parse_date(values.get(column))
            if due is not None and due < context.as_of:
                return flags("保全期限・再確認超過")
        return flags("保全継続・決定記録済")
    if state != "完了":
        return flags("未完了")
    if _blank(
        values, "実資産ID/範囲", "処理（削除/保全等）", "実施者", "独立確認者", "証拠URI"
    ) or _both(values, "実施日", "確認日") is None:
        return flags("終了証拠不足")
    if (values.get("実施者") or "").strip() == (values.get("独立確認者") or "").strip():
        return flags("独立確認不足")
    return flags("処理完了記録済")


# ── 25_事業仮説・実験・GTM ────────────────────────────
def _check_hypothesis(values: dict[str, str], context: CheckContext) -> dict[str, str]:
    approval = (values.get("承認記録ID") or "").strip()
    if not approval:
        return {"仮説記録点検": "Gate未接続"}
    if approval not in context.gate_row_ids:
        return {"仮説記録点検": "GateRun不正"}
    if _blank(
        values,
        "具体仮説/対象者",
        "成功条件/測定",
        "反証・停止条件",
        "Owner",
        "対象セグメント・期間",
        "比較対象",
        "Gateで必要な証拠",
    ):
        return {"仮説記録点検": "仮説・必要証拠不足"}
    state = (values.get("検証状態") or "").strip()
    if state == "未検証で限定継続":
        budget = (values.get("追加投資上限（円）") or "").strip()
        try:
            over = float(budget) < 0 if budget else True
        except ValueError:
            over = True
        if _blank(values, "残る不確実性", "持越し理由", "次の実験", "持越し停止条件") or over or (
            parse_date(values.get("再判断日")) is None
        ):
            return {"仮説記録点検": "持越し条件不足"}
        due = parse_date(values.get("再判断日"))
        if due is not None and due < context.as_of:
            return {"仮説記録点検": "再判断期限超過"}
        return {"仮説記録点検": "仮説記録あり"}
    if state in ("検証済み", "否定"):
        if _blank(
            values, "実測/顧客証拠URI", "実際の証拠区分", "結果の限界", "技術成立判定", "事業拡大判定"
        ) or (values.get("必要証拠の充足判定") or "").strip() in ("", "未判定"):
            return {"仮説記録点検": "実証・判定不足"}
        return {"仮説記録点検": "仮説記録あり"}
    return {"仮説記録点検": "検証状態未確定"}




# ── 数値の扱い ────────────────────────────────────────
def _number(values: dict[str, str], column: str) -> float | None:
    """数値として読める値だけ返す。空欄と文字列は None（原本の空欄・入力値不正）。"""
    raw = (values.get(column) or "").strip()
    if not raw:
        return None
    try:
        number = float(raw)
        return number if math.isfinite(number) else None
    except ValueError:
        return None


def _bad_number(values: dict[str, str], *columns: str) -> bool:
    """値が入っているのに数値として読めない列があるなら True。"""
    for column in columns:
        raw = (values.get(column) or "").strip()
        if raw:
            try:
                if not math.isfinite(float(raw)):
                    return True
            except ValueError:
                return True
    return False


def _negative(values: dict[str, str], *columns: str) -> bool:
    for column in columns:
        number = _number(values, column)
        if number is not None and number < 0:
            return True
    return False


def _sum(values: dict[str, str], *columns: str) -> float:
    return sum(_number(values, column) or 0.0 for column in columns)


def _fmt(number: float | None) -> str:
    if number is None or not math.isfinite(number):
        return ""
    if number == int(number):
        return str(int(number))
    return f"{number:.4f}".rstrip("0").rstrip(".")


# ── 31_条件・有効性 ───────────────────────────────────
def _check_condition(values: dict[str, str], context: CheckContext) -> dict[str, str]:
    severity = (values.get("重要度") or "").strip()
    state = (values.get("状態") or "").strip()
    # 原本31 R002「条件はGateRunとReleaseへ接続」。法的禁止は条件付き承認で代替しない。
    if severity == "法的禁止":
        return {"条件点検": "条件化不可・停止"}
    if _blank(values, "条件・制約", "Owner PersonID", "GateRun ID") or parse_date(
        values.get("期限")
    ) is None:
        return {"条件点検": "条件記録不足"}
    due = parse_date(values.get("期限"))
    if state == "取消":
        return {"条件点検": "取消済"}
    if state == "解消":
        if _blank(values, "解消証拠URI", "確認者PersonID") or any(
            parse_date(values.get(column)) is None for column in ("解消日", "確認日")
        ):
            return {"条件点検": "解消記録不足"}
        resolved = parse_date(values.get("解消日"))
        if due is not None and resolved is not None and resolved > due:
            # 期限を過ぎてからの解消は、元の承認を復活させない。
            return {"条件点検": "期限後解消・再承認要"}
        return {"条件点検": "解消確認済"}
    if state == "失効" or (due is not None and due < context.as_of):
        if _blank(values, "失効時処置"):
            return {"条件点検": "失効時処置不足"}
        return {"条件点検": "失効・停止再審査"}
    return {"条件点検": "期限内・制約継続"}


# ── 30_必須評価セット ─────────────────────────────────
def _check_required_eval(values: dict[str, str], context: CheckContext) -> dict[str, str]:
    key = (values.get("EvalPlanKey") or "").strip()
    plan = context.eval_plans.get(key)
    run_id = (values.get("EvalRun ID") or "").strip()
    run = context.eval_runs.get(run_id)
    eval_type = (plan or {}).get("EvalType", "")
    verdict = (run or {}).get("人の合否", "")

    def result(check: str) -> dict[str, str]:
        satisfied = check in ("必須・合格Run記録", "承認済み対象外")
        return {
            "EvalType（参照）": eval_type,
            "評価判定（参照）": verdict,
            "接続点検": check,
            "充足フラグ": "1" if satisfied else "0",
        }

    if _blank(values, "Release ID", "ManifestHash", "EvalPlanKey"):
        return result("対象版不足")
    if plan is None:
        return result("PlanKey不正")
    if values.get("取消理由"):
        return result("取消済み集合")
    if _blank(values, "集合承認URI", "承認者", "集合版／正本ID") or parse_date(values.get("承認日")) is None:
        return result("集合承認不足")
    if _future(values, context, "承認日"):
        return result("集合承認日不正")
    plan_context = CheckContext(as_of=context.as_of, row_key=key, eval_type_ids=context.eval_type_ids)
    if _check_eval_plan(plan, plan_context)["計画記録点検"] not in ("計画記録あり", "対象外計画記録"):
        return result("計画未承認・不足")
    if (values.get("ManifestHash") or "").strip() != (plan.get("対象ManifestHash") or "").strip():
        return result("評価対象不一致")
    applied = (values.get("適用") or "").strip()
    if applied == "必須":
        if not run_id or run is None:
            return result("評価Run不足・不正")
        if any((run.get(run_col) or "").strip() != (values.get(set_col) or "").strip()
               for run_col, set_col in (("ManifestHash", "ManifestHash"), ("EvalPlanKey", "EvalPlanKey"), ("対象Release/Issue", "Release ID"))):
            return result("評価対象不一致")
        run_context = CheckContext(as_of=context.as_of, row_key=run_id, eval_plans=context.eval_plans,
                                   eval_type_ids=context.eval_type_ids)
        if _check_eval_run(run, run_context)["記録点検"] != "記録あり・内容審査別":
            return result("評価記録未充足")
        if verdict != "合格":
            # 原本30 R002「単一の平均点で欠落を代替しない」
            return result("必要評価不合格・未確定")
        return result("必須・合格Run記録")
    if applied == "対象外":
        if _blank(values, "対象外理由", "集合承認URI", "承認者") or parse_date(
            values.get("承認日")
        ) is None:
            return result("対象外承認不足")
        return result("承認済み対象外")
    return result("適用未判定")


# ── 18_見積・AI効果測定 ───────────────────────────────
AI_HOUR_COLUMNS = (
    "AI準備/Harness",
    "仕様/Context人時間",
    "AI実装作業人時間",
    "Review人時間",
    "検証人時間",
    "手戻り人時間",
    "事故対応人時間",
)
COST_COLUMNS = ("AI license費", "API/compute費", "追加基盤費", "教育/統制費", "事故追加費")


def _check_effect(values: dict[str, str], context: CheckContext) -> dict[str, str]:
    numeric = (*AI_HOUR_COLUMNS, *COST_COLUMNS, "Baseline人時間", "Baseline経過時間",
               "AI経過時間", "回避できた現金支出", "増分粗利（重複除外）", "再配置した余力h", "観測件数")
    ai_hours = _sum(values, *AI_HOUR_COLUMNS)
    baseline_hours = _number(values, "Baseline人時間")
    extra_cost = _sum(values, *COST_COLUMNS)
    net_effect = (
        (_number(values, "回避できた現金支出") or 0.0)
        + (_number(values, "増分粗利（重複除外）") or 0.0)
        - extra_cost
    )
    saved = None if baseline_hours is None else baseline_hours - ai_hours
    saved_rate = None if not baseline_hours else (saved or 0.0) / baseline_hours

    baseline_elapsed = _number(values, "Baseline経過時間")
    ai_elapsed = _number(values, "AI経過時間")
    elapsed_rate: float | None = None
    if _bad_number(values, *numeric) or _negative(values, *numeric):
        # 負の経過時間から短縮率を出さない（原本AR16）
        check = "入力値不正"
    elif baseline_elapsed is not None and baseline_elapsed == 0:
        check = "基準経過0・短縮率計算不可"
    else:
        if baseline_elapsed is not None and ai_elapsed is not None:
            # 悪化（遅くなった）は負の値として正当に残す
            elapsed_rate = (baseline_elapsed - ai_elapsed) / baseline_elapsed
        if _blank(values, "作業カテゴリ/Issue", "対象期間・比較条件", "証拠URI", "確認者"):
            check = "測定記録不足"
        else:
            check = "記録あり・採用判断別"

    # 見積採用点検（原本18!AQ）
    basis = (values.get("基準値の種類") or "").strip()
    quality = (values.get("品質同等の確認") or "").strip()
    adoption = (values.get("見積係数への反映") or "").strip()
    if basis == "推定" or quality != "同等確認済":
        adopt_check = "推定・品質未確認は採用不可"
    elif adoption == "限定条件で反映":
        if _blank(values, "見積採用承認者", "採用範囲／期限") or parse_date(
            values.get("採用承認日")
        ) is None:
            adopt_check = "採用承認不足"
        else:
            adopt_check = "限定採用判断記録・一般化不可"
    elif adoption == "反映しない":
        adopt_check = "採用しない"
    else:
        adopt_check = "採用判断未記録"

    return {
        "AI人時間計": _fmt(ai_hours),
        "純削減人時間": _fmt(saved),
        "純削減率": _fmt(saved_rate),
        "経過短縮率": _fmt(elapsed_rate),
        "追加費合計": _fmt(extra_cost),
        "純経済効果": _fmt(net_effect),
        "点検": check,
        "見積採用点検": adopt_check,
    }


# ── 26_単位経済性 ─────────────────────────────────────
VARIABLE_COST_COLUMNS = ("Model/API費", "検索/データ費", "変動基盤費", "変動人手/CS費", "他変動直接費")


def _check_unit_economics(values: dict[str, str], context: CheckContext) -> dict[str, str]:
    units = _number(values, "課金単位数") or 0.0
    price = _number(values, "単価（円）") or 0.0
    revenue = units * price + (_number(values, "その他売上") or 0.0) - (
        _number(values, "返金/値引") or 0.0
    )
    variable = _sum(values, *VARIABLE_COST_COLUMNS)
    margin = revenue - variable
    margin_rate = margin / revenue if revenue else None
    fixed = _number(values, "期間固定費") or 0.0
    operating = margin - fixed
    successes = _number(values, "一意の成功業務数")
    trials = _number(values, "全試行回数（retry含む）")
    # 変動原価と固定費配賦込みを分ける（原本26 R002）
    per_success = variable / successes if successes else None
    per_success_full = (variable + fixed) / successes if successes else None

    numeric = ("課金単位数", "単価（円）", "その他売上", "返金/値引", "全試行回数（retry含む）",
               "一意の成功業務数", *VARIABLE_COST_COLUMNS, "期間固定費")
    if _bad_number(values, *numeric) or _negative(values, *numeric):
        check = "入力値不正"
    elif successes is not None and successes == 0:
        check = "成功0・単位原価計算不可"
    elif trials is not None and successes is not None and trials < successes:
        # 試行回数増を成功数増と誤認しない
        check = "試行数不整合"
    elif _blank(values, "対象期間/条件", "成功業務の定義・ID", "根拠URI"):
        check = "未入力"
    else:
        check = "記録あり・採算判断別"

    return {
        "純売上": _fmt(revenue),
        "変動費計": _fmt(variable),
        "限界利益": _fmt(margin),
        "限界利益率": _fmt(margin_rate),
        "簡易営業収支": _fmt(operating),
        "成功業務あたり変動原価": _fmt(per_success),
        "固定費配賦込み単位費用": _fmt(per_success_full),
        "入力点検": check,
    }


# ── 26_期間資金計画 ───────────────────────────────────
def _check_cash_plan(values: dict[str, str], context: CheckContext) -> dict[str, str]:
    opening = _number(values, "期首現金") or 0.0
    closing = (
        opening
        + (_number(values, "確定調達/投資受入") or 0.0)
        + (_number(values, "期間入金") or 0.0)
        - (_number(values, "期間支出") or 0.0)
    )
    floor = _number(values, "最低確保現金") or 0.0
    return {"期末現金": _fmt(closing), "不足額": _fmt(max(0.0, floor - closing))}



# ── 29_ゲート承認記録（1行=GateRun） ─────────────────────
APPROVING_DECISIONS = ("承認", "条件付承認", "Scale", "Continue", "廃止完了承認")
VERDICT_COLUMNS = ("独立QA判定", "Privacy判定", "Security判定")


def _check_gate_run(values: dict[str, str], context: CheckContext) -> dict[str, str]:
    gate_id = (values.get("Gate") or "").strip()
    gate = (context.master_ids.get("gates_by_id") or {}).get(gate_id, {}) if isinstance(
        context.master_ids.get("gates_by_id"), dict
    ) else {}
    definition = {
        "判断対象": gate.get("subject", ""),
        "標準Task": gate.get("standard_task_id", ""),
        "最終A Role": gate.get("approver_role_id", ""),
        "必要証拠の定義": gate.get("required_evidence", ""),
    }
    decision = (values.get("判断結果") or "").strip()

    # 記録点検（原本29!S）
    if _duplicated(context):
        record = "判断Run ID重複"
    elif not gate_id or not gate:
        record = "Gate不正"
    elif decision in ("", "未審査"):
        record = "未承認"
    elif _future(values, context, "判断日") or _unreadable(values, "判断日"):
        record = "実績日時不正"
    elif _blank(values, "対象範囲/版", "証拠パッケージURI", "A実名", "承認者PersonID", "正本決裁URI", "事業Risk受容/予算") or (
        parse_date(values.get("判断日")) is None
    ):
        record = "決裁記録不足"
    else:
        record = "記録あり"
    if record == "記録あり" and (_blank(values, "正本確認者PersonID", "正本確認日時") or parse_timestamp(values.get("正本確認日時")) is None):
        record = "正本決裁未確認"

    # 判定整合（原本29!AA）。事業判断で品質・法令の不合格を上書きしない。
    allowed = set(gate.get("allowed_decisions", []))
    if decision and allowed and decision not in allowed:
        consistency = "Gate判断不適合"
    elif decision in APPROVING_DECISIONS and any(
        (values.get(column) or "").strip() == "不合格" for column in VERDICT_COLUMNS
    ):
        consistency = "停止判定と承認が矛盾"
    elif decision in APPROVING_DECISIONS and any(
        (values.get(column) or "").strip() in ("", "未判定") for column in VERDICT_COLUMNS
    ):
        consistency = "独立判定未確定"
    elif gate_id == "G4" and decision in ("Scale", "Continue"):
        expanded = [
            row
            for hypothesis_id, row in context.rows("hypothesis").items()
            if (row.get("事業拡大判定") or "").strip() == "拡大可能"
            and hypothesis_id == values.get("仮説ID")
            and _check_hypothesis(row, context)["仮説記録点検"] == "仮説記録あり"
            and (row.get("必要証拠の充足判定") or "").strip() == "充足"
            and row.get("対象範囲/版") == values.get("対象範囲/版")
            and row.get("対象期間") == values.get("対象期間")
            and row.get("対象期間")
        ]
        consistency = "判定整合" if expanded else "拡大の行動証拠不足"
    else:
        consistency = "判定整合"

    # 必須評価・前提点検（原本29!AB）
    if gate_id == "G3":
        entries = [
            row
            for row in context.rows("required_eval").values()
            if (row.get("Release ID") or "").strip() == (values.get("Release ID") or "").strip()
            and (row.get("ManifestHash") or "").strip() == (values.get("ManifestHash") or "").strip()
            and row.get("集合版／正本ID") == values.get("集合版／正本ID")
        ]
        types = [(context.eval_plans.get(row.get("EvalPlanKey", "")) or {}).get("EvalType") for row in entries]
        conditions = context.venture.get("conditions", {})
        governance = context.venture.get("governance", {})
        if not governance.get("riskConfirmed") or values.get("前提版") != governance.get("riskFingerprint"):
            prerequisites = "リスク・前提再確認要"
        elif any(conditions.get(key) not in ("適用", "対象外") for key in ("RAG", "Agent")):
            prerequisites = "RAG・Agent適用未確定"
        elif set(types) != context.eval_type_ids or len(types) != len(set(types)):
            prerequisites = "必須分類・集合不足"
        elif _blank(values, "Release ID", "ManifestHash", "必須評価集合URI", "集合承認者", "集合版／正本ID"):
            prerequisites = "公開対象・集合不足"
        elif any(
            (conditions.get(feature) == "適用" and (
                not context.tasks.get(task_id, {}).get("completionValid") or
                any(not any(row.get("適用") == "必須" and (context.eval_plans.get(row.get("EvalPlanKey", "")) or {}).get("EvalType") == et for row in entries) for et in eval_types)))
            or (conditions.get(feature) == "対象外" and context.tasks.get(task_id, {}).get("completionCheck") != "除外記録済")
            for feature, task_id, eval_types in (("RAG", "B4-03", ("E03", "E04")), ("Agent", "B4-04", ("E05",)))
        ):
            prerequisites = "機能別評価・対象外未完"
        else:
            unsatisfied = [
                row
                for row in entries
                if _check_required_eval(row, context)["充足フラグ"] != "1"
                or row.get("集合承認URI") != values.get("必須評価集合URI")
                or row.get("承認者") != values.get("集合承認者")
            ]
            prerequisites = "必須評価セット未充足" if unsatisfied else "必須評価セット充足"
    elif gate_id == "G5":
        retirements = list(context.rows("retirement").values())
        if not retirements:
            prerequisites = "終了残件あり・資産台帳確認"
        else:
            decided = [
                row
                for row in retirements
                if _check_retirement(row, context)["資産処理決定フラグ"] == "1"
            ]
            prerequisites = (
                "資産処理決定充足"
                if len(decided) == len(retirements)
                else "終了残件あり・資産台帳確認"
            )
    elif gate_id == "G0":
        recorded = [
            row
            for row in context.rows("hypothesis").values()
            if _check_hypothesis(row, context)["仮説記録点検"] == "仮説記録あり"
        ]
        prerequisites = "G0仮説記録接続" if recorded else "仮説・持越し確認不足"
    else:
        prerequisites = "対象Gate証拠を正本審査"

    # 条件点検（原本29!AC）
    mode = (values.get("条件運用区分") or "").strip()
    linked = [
        row
        for row in context.rows("condition").values()
        if (row.get("GateRun ID") or "").strip() == context.row_key
    ]
    if mode in ("", "未判定"):
        condition_check = "条件有無未判定"
    elif mode == "なし":
        condition_check = "条件整合" if not linked else "条件定義不一致"
    elif not linked:
        condition_check = "条件失効・定義不備"
    else:
        verdicts = {_check_condition(row, context)["条件点検"] for row in linked}
        healthy = {"期限内・制約継続", "解消確認済"}
        condition_check = "条件整合" if verdicts <= healthy else "条件失効・定義不備"

    # 有効性点検（原本29!AD）
    if record != "記録あり":
        effective = record
    elif consistency != "判定整合":
        effective = consistency
    elif not _blank(values, "取消／置換Run ID") or values.get("取消理由"):
        # 取り消された判断は、後から公開の根拠に再利用しない。
        effective = "取消・置換済"
    else:
        expiry = parse_date(values.get("決裁有効期限"))
        if expiry is not None and expiry < context.as_of:
            effective = "決裁期限切れ"
        elif condition_check != "条件整合":
            effective = condition_check
        elif prerequisites not in ("必須評価セット充足", "資産処理決定充足", "G0仮説記録接続", "対象Gate証拠を正本審査"):
            effective = prerequisites
        else:
            effective = "整合済・正本決裁要確認"

    return {
        **definition,
        **({"未登録の評価分類": ", ".join(sorted(context.eval_type_ids - set(types))),
            "重複した評価分類": ", ".join(sorted(t for t in set(types) if t and types.count(t) > 1))} if gate_id == "G3" else {}),
        "記録点検": record,
        "判定整合": consistency,
        "必須評価・前提点検": prerequisites,
        "条件点検": condition_check,
        "有効性点検": effective,
    }


# ── 34_Run・同期管理（反復TaskRun） ─────────────────────
def _check_task_run(values: dict[str, str], context: CheckContext) -> dict[str, str]:
    task_id = (values.get("Task ID") or "").strip()
    tasks = context.master_ids.get("tasks_by_id") or {}
    name = tasks.get(task_id, {}).get("name", "") if isinstance(tasks, dict) else ""
    trigger = (values.get("開始トリガー") or "").strip()
    origin = (values.get("起点GateRun／Incident") or "").strip()

    def result(check: str) -> dict[str, str]:
        return {"名称（参照）": name, "Run記録点検": check}

    if _duplicated(context):
        return result("TaskRun ID重複")
    if not task_id or task_id not in tasks:
        return result("Task ID不正")
    if _blank(values, "開始トリガー", "Owner PersonID", "Issue正本URI"):
        return result("Run起票不足")
    if trigger == "事故" and (not origin or _blank(values, "事故後レビューRun URI")):
        # 事故起因の保守は、事故レビューを参照しないと記録として成立しない。
        return result("事故・レビュー参照不足")
    if trigger == "早期Stop":
        gate_run = context.rows("gate_run").get(origin)
        if gate_run is None or (gate_run.get("判断結果") or "").strip() != "Stop" or not gate_run.get("正本確認日時") or any(gate_run.get(k) for k in ("取消理由", "取消／置換Run ID")):
            return result("Stop判断参照不足")
    if _future(values, context, "実完了日時", "確認日") or _unreadable(values, "実完了日時", "確認日"):
        return result("Run実績日不正")
    if (values.get("状態") or "").strip() != "完了":
        return result("Run進行中")
    if _blank(values, "ManifestHash", "完了証拠URI", "確認者PersonID") or _both(
        values, "実完了日時", "確認日"
    ) is None:
        return result("Run完了証拠不足")
    pair = _both(values, "確認日", "実完了日時")
    if pair and pair[0] < pair[1]:
        return result("確認日逆転")
    if trigger == "定期" and parse_date(values.get("次回期限")) is None:
        return result("次回期限不足")
    return result("Run記録あり・内容審査別")


# ── 35_実名・能力割当 ─────────────────────────────────
def _check_assignment(values: dict[str, str], context: CheckContext) -> dict[str, str]:
    task_id = (values.get("Task ID") or "").strip()
    role_id = (values.get("Role ID") or "").strip()
    skill_id = (values.get("Skill ID") or "").strip()
    person = (values.get("PersonID") or "").strip()
    tasks = context.master_ids.get("tasks_by_id") or {}
    skills = context.master_ids.get("skills_by_id") or {}
    roles = context.master_ids.get("role_ids") or set()
    required = _number(values, "必要Lv")
    record = context.assessment_records.get(values.get("能力評価記録ID", ""), {})
    achieved = record.get("level") if record.get("skillId") == skill_id and record.get("userId") == person and record.get("evidenceUri") and record.get("assessedBy") != person else None

    def result(check: str) -> dict[str, str]:
        gap = ""
        if required is not None:
            gap = _fmt(max(0.0, required - float(achieved if achieved is not None else 0)))
        return {
            "Task名（参照）": tasks.get(task_id, {}).get("name", "") if isinstance(tasks, dict) else "",
            "Skill名（参照）": skills.get(skill_id, {}).get("name", "") if isinstance(skills, dict) else "",
            "評価Lv（参照）": "" if achieved is None else str(achieved),
            "能力不足Lv": gap,
            "割当点検": check,
        }

    if task_id not in tasks or skill_id not in skills or role_id not in roles:
        return result("ID不正")
    if not person or required is None:
        return result("割当記録不足")
    if (values.get("役割区分") or "").strip() in ("独立評価", "品質決裁") and (
        (values.get("当該実装PersonID") or "").strip() == person
    ):
        # Role名が違っても、同じPersonなら独立していない。
        return result("実装との独立性不足")
    if achieved is None:
        return result("能力の第三者確認不足")
    if (person, role_id) not in context.member_roles:
        return result("実施ロール未割当")
    if _blank(values, "割当承認者", "必要性・担当範囲", "対象期間") or parse_date(values.get("承認日")) is None:
        return result("割当承認不足")
    if required > float(achieved):
        return result("能力不足・育成又は支援要")
    return result("割当記録あり")


# ── 06_ロール・要員計画 ───────────────────────────────
def _check_role_staffing(values: dict[str, str], context: CheckContext) -> dict[str, str]:
    person = (values.get("PersonID") or "").strip()
    required = _number(values, "必要FTE（入力）")
    allocated = _number(values, "割当FTE（入力）")
    shortage = None if required is None else required - (allocated or 0.0)
    # 同じPersonが複数ロールを持つときの合計稼働（原本06 R002）
    total = allocated or 0.0
    if person:
        for row_key, row in context.rows("role_staffing").items():
            if row_key == context.row_key:
                continue
            if (row.get("PersonID") or "").strip() == person:
                total += _number(row, "割当FTE（入力）") or 0.0
    cap = _number(values, "当人の当日上限FTE")

    if not person:
        check = "Person未割当"
    elif cap is not None and total > cap:
        check = "当日FTE超過"
    elif shortage is not None and shortage > 0:
        check = "要員不足"
    elif _blank(values, "担当実名（入力）", "対象期間（入力）"):
        check = "配置記録不足"
    else:
        check = "稼働記録あり"
    return {
        "不足FTE": _fmt(shortage),
        "当日合計FTE": _fmt(total),
        "稼働点検": check,
    }


_CHECKERS = {
    "eval_plan": _check_eval_plan,
    "eval_run": _check_eval_run,
    "release": _check_release,
    "incident": _check_incident,
    "retirement": _check_retirement,
    "hypothesis": _check_hypothesis,
    "condition": _check_condition,
    "required_eval": _check_required_eval,
    "effect": _check_effect,
    "unit_economics": _check_unit_economics,
    "cash_plan": _check_cash_plan,
    "gate_run": _check_gate_run,
    "task_run": _check_task_run,
    "assignment": _check_assignment,
    "role_staffing": _check_role_staffing,
}


def evaluate(ledger_key: str, values: dict[str, str], context: CheckContext) -> dict[str, str]:
    """台帳の点検列を計算する。点検を持たない台帳では空を返す。"""
    checker = _CHECKERS.get(ledger_key)
    if checker is None:
        return {}
    result = checker(values, context)
    if ledger_key in ("unit_economics", "cash_plan", "effect"):
        required = {
            "unit_economics": ("課金単位数", "単価（円）", "その他売上", "返金/値引", "全試行回数（retry含む）", "一意の成功業務数", *VARIABLE_COST_COLUMNS, "期間固定費"),
            "cash_plan": ("期首現金", "確定調達/投資受入", "期間入金", "期間支出", "最低確保現金"),
            "effect": (*AI_HOUR_COLUMNS, *COST_COLUMNS, "Baseline人時間", "Baseline経過時間", "AI経過時間", "回避できた現金支出", "増分粗利（重複除外）"),
        }[ledger_key]
        if values.get("測定区分") in ("対象外", "未計測") or any(_number(values, column) is None for column in required):
            for key, value in list(result.items()):
                try:
                    float(value)
                    result[key] = ""
                except ValueError:
                    pass
            result["測定点検"] = ("対象外" if values.get("対象外理由") else "対象外理由不足") if values.get("測定区分") == "対象外" else "未計測・必要入力不足"
            for key in ("入力点検", "点検", "見積採用点検"):
                if key in result:
                    result[key] = result["測定点検"]
    from infrastructure.venture_governance import EVENT_COLUMNS
    invalid = [col for col in EVENT_COLUMNS.get(ledger_key, set()) if values.get(col) and parse_timestamp(values[col]) is None]
    if invalid:
        result["日時精度点検"] = "時差付き日時で再確認要"
        if "記録点検" in result:
            result["記録点検"] = "時差付き日時で再確認要"
        if ledger_key == "release":
            result["公開準備点検"] = "時差付き日時で再確認要"
    return result


def blocking(ledger_key: str, derived: dict[str, str]) -> str | None:
    """書き込みを拒否すべき判定値があれば返す。"""
    blockers = BLOCKING_VERDICTS.get(ledger_key, set())
    for verdict in derived.values():
        if verdict in blockers:
            return verdict
    return None
