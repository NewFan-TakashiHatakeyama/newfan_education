# -*- coding: utf-8 -*-
"""事業PJ工程マスタの抽出.

`docs/AIシステム自社事業PJ工程管理_v1_1_敵対的レビュー反映版.xlsx` を読み、
API が参照するマスタ JSON を生成する。

    python tools/extract_venture_master.py

出力: apps/api/src/infrastructure/data/venture_process_master.json

Excel を改訂したら本スクリプトを再実行してマスタを更新する。文言は原本のまま使う。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import openpyxl
from openpyxl.utils import range_boundaries

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "AIシステム自社事業PJ工程管理_v1_1_敵対的レビュー反映版.xlsx"
DST = ROOT / "apps" / "api" / "src" / "infrastructure" / "data" / "venture_process_master.json"


def text(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("\r\n", "\n").strip()


def split_ids(value: object) -> list[str]:
    raw = text(value)
    if not raw:
        return []
    return [part.strip() for part in re.split(r"[,、\s/／]+", raw) if part.strip()]


def find_header(rows: list[tuple], first_cell: str) -> int:
    for index, row in enumerate(rows):
        if row and text(row[0]) == first_cell:
            return index
    raise ValueError(f"header row not found: {first_cell}")


def sheet_rows(workbook: openpyxl.Workbook, name: str) -> list[tuple]:
    return list(workbook[name].iter_rows(values_only=True))


def table_ex(
    workbook: openpyxl.Workbook,
    sheet: str,
    first_cell: str,
    stop_first_cell: str | None = None,
) -> tuple[list[str], list[dict], int, int]:
    """ヘッダー行を探し、列名 -> 値 の dict 一覧とヘッダー位置・データ終端を返す。

    1つのシートに表が2つある場合（21のSLOとインシデント記録）に備えて、
    `stop_first_cell` で次の表の手前まで読む。
    """
    rows = sheet_rows(workbook, sheet)
    head_index = find_header(rows, first_cell)
    headers = [text(cell) for cell in rows[head_index]]
    records: list[dict] = []
    data_end = head_index
    for offset, row in enumerate(rows[head_index + 1 :], start=head_index + 1):
        if row and all(cell is None for cell in row):
            break
        if stop_first_cell and row and text(row[0]) == stop_first_cell:
            break
        data_end = offset
        if not row or not text(row[0]):
            continue
        record = {}
        for header, cell in zip(headers, row):
            if header:
                record[header] = text(cell)
        records.append(record)
    return headers, records, head_index, data_end


def table_blocks(
    workbook: openpyxl.Workbook,
    sheet: str,
) -> list[tuple[int, int]]:
    """このシートに定義した台帳が占める行範囲を返す。

    1シートに表が複数ある（21のSLOとインシデント、26のKPI・単位経済性・期間資金計画、
    03の2表）ので、ある台帳の注記に別の台帳の行が混ざらないようにする。
    """
    rows = sheet_rows(workbook, sheet)
    blocks: list[tuple[int, int]] = []
    for spec in LEDGERS:
        if spec["sheet"] != sheet:
            continue
        _, _, head_index, data_end = table_ex(
            workbook, sheet, spec["first_cell"], spec.get("stop_first_cell")
        )
        start = head_index
        # ヘッダーの直前が見出し行（1セルだけ）なら、その見出しも表の一部として扱う。
        above = rows[head_index - 1] if head_index > 0 else []
        if above and len([cell for cell in above if text(cell)]) == 1:
            start = head_index - 1
        blocks.append((start, data_end))
    return blocks


def table_indexed(
    workbook: openpyxl.Workbook,
    sheet: str,
    first_cell: str,
    stop_first_cell: str | None = None,
) -> list[tuple[int, dict]]:
    """`table` と同じ読み方で、行番号を添えて返す。"""
    rows = sheet_rows(workbook, sheet)
    head_index = find_header(rows, first_cell)
    headers = [text(cell) for cell in rows[head_index]]
    found: list[tuple[int, dict]] = []
    for index, row in enumerate(rows[head_index + 1 :], start=head_index + 1):
        if stop_first_cell and row and text(row[0]) == stop_first_cell:
            break
        if not row or not text(row[0]):
            continue
        record = {}
        for header, cell in zip(headers, row):
            if header:
                record[header] = text(cell)
        found.append((index, record))
    return found


def table(
    workbook: openpyxl.Workbook,
    sheet: str,
    first_cell: str,
    stop_first_cell: str | None = None,
) -> tuple[list[str], list[dict]]:
    """ヘッダー行を探し、列名 -> 値 の dict 一覧を返す。

    空行では止めず、シート末尾まで読む（従来どおり）。1シートに表が2つある場合は
    `stop_first_cell` で次の表の手前で止める。
    """
    rows = sheet_rows(workbook, sheet)
    head_index = find_header(rows, first_cell)
    headers = [text(cell) for cell in rows[head_index]]
    records: list[dict] = []
    for row in rows[head_index + 1 :]:
        if stop_first_cell and row and text(row[0]) == stop_first_cell:
            break
        if not row or not text(row[0]):
            continue
        record = {}
        for header, cell in zip(headers, row):
            if header:
                record[header] = text(cell)
        records.append(record)
    return headers, records


def validation_rule(validation) -> dict | None:
    """Excelの入力規則を、システムで使える形にする。

    原本は判定・区分・状態の列にドロップダウンを、日時・金額に日付/数値制約を
    張っている。これを捨てると統制語彙が失われ、全部が自由記述になる。
    """
    if validation.type == "list":
        formula = (validation.formula1 or "").strip()
        if formula.startswith('"') and formula.endswith('"'):
            options = [o.strip() for o in formula[1:-1].split(",") if o.strip()]
            return {"type": "select", "options": options} if options else None
        # 名前付き範囲（EvalIDs 等）は別表を指す。参照名だけ残して後で解決する。
        return {"type": "select", "options": [], "source": formula}
    if validation.type == "date":
        return {"type": "date"}
    if validation.type in ("decimal", "whole"):
        rule: dict = {"type": "number"}
        raw = (validation.formula1 or "").strip()
        if validation.operator == "greaterThanOrEqual":
            try:
                rule["min"] = float(raw)
            except ValueError:
                pass
        return rule
    return None


def derived_columns(
    formula_book: openpyxl.Workbook, sheet: str, headers: list[str], head_index: int, data_end: int
) -> list[str]:
    """原本で数式が入っている列。案件が手入力する列ではないので入力列から外す。

    `EXCLUDED_COLUMN` の見出し規則（点検|（自動）|（参照）|フラグ）では拾えない
    数式列がある（16の「凍結計画Key照合」、21の「検知→受付h」など）。
    """
    worksheet = formula_book[sheet]
    found: list[str] = []
    for index, header in enumerate(headers):
        if not header:
            continue
        for row in range(head_index + 2, min(data_end + 2, head_index + 40) + 1):
            value = worksheet.cell(row=row, column=index + 1).value
            if isinstance(value, str) and value.startswith("="):
                found.append(header)
                break
    return found


def column_rules(
    workbook: openpyxl.Workbook, sheet: str, headers: list[str], head_index: int, data_end: int
) -> dict[str, dict]:
    """列見出し -> 入力規則。対象の表の行範囲に掛かっている規則だけを拾う。"""
    worksheet = workbook[sheet]
    header_row = head_index + 1  # 1始まり
    # 予約行はキャッシュ値が空になることがあるので、データ終端の1つ先まで許す。
    limit = max(data_end + 1, header_row) + 1
    rules: dict[str, dict] = {}
    for validation in worksheet.data_validations.dataValidation:
        rule = validation_rule(validation)
        if rule is None:
            continue
        for reference in str(validation.sqref).split():
            min_col, min_row, max_col, _ = range_boundaries(reference)
            if min_row <= header_row or min_row > limit:
                continue
            for column in range(min_col, max_col + 1):
                index = column - 1
                if index < len(headers) and headers[index]:
                    rules[headers[index]] = rule
    return rules


# ─────────────────────────────────────────────────────────────
# 台帳シートの定義。key はシステム上の識別子、sheet/first_cell は抽出元。
# id_column はマスタ行のキー列。
# ─────────────────────────────────────────────────────────────
LEDGERS = [
    # rows_from_master=True の台帳は、Excel のマスタ行を点検項目として引き継ぐ。
    # False の台帳は案件ごとに行を起票する（Excel 側もテンプレート行を持たない）。
    # 原本03の2表。どちらも「マスタ行＋統制語彙の判定列＋自由記述」なので汎用台帳で扱う。
    dict(key="risk_screening", sheet="03_AIリスクTier・適用判定", first_cell="判定軸", id_column="判定軸",
         row_limit=10, state_column="確認状態", id_pattern=r".+", stop_first_cell="機能判定：方式・配置・学習を独立に判定する（AR02/04）",
         master_columns=["判定軸", "確認事項"],
         name="AIリスク案件判定", summary="製品AIと開発Agentを別々に判定し、Risk Tierの根拠と承認を記録する。"),
    dict(key="feature_decision", sheet="03_AIリスクTier・適用判定", first_cell="機能／境界", id_column="機能／境界",
         row_limit=6, state_column="採用判定", id_pattern=r".+", stop_first_cell="外部APIのみ",
         master_columns=["機能／境界", "具体的な実施形態", "必須評価・能力"],
         name="機能判定", summary="RAG・Agent・追加学習などの採用を独立に判定し、判断者と承認を記録する。"),
    dict(key="data", sheet="10_データ台帳", first_cell="Data ID", id_column="Data ID",
         row_limit=40, id_pattern=None, master_columns=[],
         name="データ台帳", summary="学習・RAG・評価に使うデータの出所、権利、個人情報区分、保持と削除を記録する。"),
    dict(key="dependency", sheet="11_モデル・外部AI・ベンダー台帳", first_cell="依存ID", id_column="依存ID",
         row_limit=40, id_pattern=None, master_columns=[],
         name="モデル・外部AI・ベンダー台帳", summary="利用するモデル、外部AI、ツール、ベンダーの版・処理地域・規約・代替策を記録する。"),
    dict(key="privacy", sheet="12_プライバシー・法令判定", first_cell="判定ID", id_column="判定ID",
         row_limit=14, id_pattern=r"L\d+",
         master_columns=["判定ID", "対象", "位置づけ", "具体的な確認", "責任Role", "タイミング", "根拠ID", "公式URL"],
         name="プライバシー・法令判定", summary="適用法の範囲、根拠、責任者、再確認日を判定して記録する。"),
    dict(key="adr", sheet="13_アーキテクチャ・ADR台帳", first_cell="ADR ID", id_column="ADR ID",
         row_limit=12, id_pattern=r"ADR\d+",
         master_columns=["ADR ID", "検討テーマ", "最低限検討する論点", "関連B-ID"],
         name="アーキテクチャ・ADR台帳", summary="方式選択の論点、採用案、却下理由、残存リスク、見直しトリガーを記録する。"),
    dict(key="eval_plan", sheet="15_評価計画・品質ゲート", first_cell="EvalType", id_column="EvalType",
         row_limit=100, state_column="状態", locked_states=["承認", "対象外承認"], id_pattern=r"E\d+",
         master_columns=["EvalType", "評価軸", "指標候補", "設計上の要点", "適用条件", "設計Role", "根拠ID"],
         name="評価計画・品質ゲート", summary="評価軸ごとに母集団、閾値、独立評価者、凍結データ版を設計する。"),
    dict(key="eval_run", sheet="16_評価実績インデックス", first_cell="Run ID", id_column="Run ID",
         row_limit=100, state_column="人の合否", id_pattern=None, master_columns=[],
         name="評価実績インデックス", summary="実施した評価の対象版、実測値、重大失敗、独立確認を記録する。"),
    dict(key="risk", sheet="19_リスク・セキュリティ・例外", first_cell="Risk ID", id_column="Risk ID",
         row_limit=40, state_column="状態", id_pattern=r"RS\d+",
         master_columns=["Risk ID", "分類", "仮説/事象", "対策案", "Owner Role", "関連Task"],
         name="リスク・セキュリティ・例外", summary="リスク仮説ごとに該当判定、対策、残存リスク、停止条件、例外承認を記録する。"),
    dict(key="release", sheet="20_リリース・変更・ロールバック", first_cell="Release/Change ID", id_column="Release/Change ID",
         row_limit=40, state_column="状態", id_pattern=None, master_columns=[],
         name="リリース・変更・ロールバック", summary="公開・変更ごとに対象版、評価Run、独立判定、段階展開、復旧手順を記録する。"),
    dict(key="slo", sheet="21_SLO・運用・インシデント", first_cell="SLI ID", id_column="SLI ID",
         id_pattern=r"SL\d+",
         master_columns=["SLI ID", "指標", "定義案", "分母・留保"],
         name="SLO・運用・インシデント", summary="サービス指標の定義、目標、警報と停止条件、計測先を記録する。"),
    dict(key="retirement", sheet="22_廃止・移管・削除", first_cell="確認ID", id_column="確認ID",
         row_limit=40, state_column="状態", id_pattern=r"RT\d+",
         master_columns=["確認ID", "対象", "最低限の終了条件", "Task ID"],
         name="廃止・移管・削除", summary="終了条件ごとに処理、期限、実施者、独立確認、残存事項を記録する。"),
    dict(key="contract", sheet="23_外部契約・調達", first_cell="契約区分ID", id_column="契約区分ID",
         row_limit=10, state_column="状態", id_pattern=r"CT\d+",
         master_columns=["契約区分ID", "種別", "必要時点", "主要確認条件", "関連Task"],
         name="外部契約・調達", summary="必要な契約の種別、確認条件、有効期間、終了時条件を記録する。"),
    dict(key="hypothesis", sheet="25_事業仮説・実験・GTM", first_cell="仮説ID", id_column="仮説ID",
         row_limit=12, state_column="検証状態", id_pattern=r"HY\d+",
         master_columns=["仮説ID", "領域", "検証する問い", "手段候補", "関連Task"],
         name="事業仮説・実験・GTM", summary="事業仮説ごとに検証手段、成功条件、反証・停止条件、実測を記録する。"),
    dict(key="incident", sheet="21_SLO・運用・インシデント", first_cell="Incident ID", id_column="Incident ID",
         row_limit=30, state_column="状態", id_pattern=None, master_columns=[],
         name="インシデント記録", summary="検知・受付・復旧・解決の時刻と、救済・法務・再発防止を記録する。"),
    # 原本06は1行=Roleの定義に、案件の要員計画（実名・FTE・配置期間）が同居している。
    dict(key="role_staffing", sheet="06_ロール・要員計画", first_cell="Role ID", id_column="Role ID",
         row_limit=20, id_pattern=r"R\d+",
         master_columns=["Role ID", "ロール", "主要責任", "関与・判断", "兼務・独立性の注意", "中核Skill"],
         name="ロール・要員計画", summary="ロールごとに実名・所属・必要FTE・配置期間を割り当て、兼務の合計を点検する。"),
    # 原本29は1行=GateRun。判断のたびに行を足し、上書きしない。
    dict(key="gate_run", sheet="29_ゲート承認記録", first_cell="Gate", id_column="判断Run ID",
         row_limit=80, state_column="判断結果",
         id_pattern=None, master_columns=[],
         name="ゲート判断Run", summary="ゲートの判断を1件1行で残す。独立QA・Privacy・Securityの判定と有効性を分けて記録する。"),
    # 原本34は17の初回に対する反復Run（定期・変更・事故・早期Stop）。
    dict(key="task_run", sheet="34_Run・同期管理", first_cell="TaskRun ID", id_column="TaskRun ID",
         row_limit=60, state_column="状態",
         id_pattern=None, master_columns=[],
         name="反復TaskRun", summary="定期・変更・事故・早期Stopの反復実行を、初回とは別のRunとして残す。"),
    # 原本35は Task × Role × Skill × Person の割当。
    dict(key="assignment", sheet="35_実名・能力割当", first_cell="割当ID", id_column="割当ID",
         row_limit=100, state_column="役割区分",
         id_pattern=None, master_columns=[],
         name="実名・能力割当", summary="タスクとロールごとに担当者を割り当て、必要Lvと第三者評価を接続する。"),
    dict(key="required_eval", sheet="30_必須評価セット", first_cell="対応ID", id_column="対応ID",
         row_limit=150, state_column="適用",
         id_pattern=None, master_columns=[],
         name="必須評価セット", summary="対象版ごとに18分類の適用を決め、必須は合格Run、対象外は理由と承認を記録する。"),
    dict(key="condition", sheet="31_条件・有効性", first_cell="Condition ID", id_column="Condition ID",
         row_limit=80, state_column="状態",
         id_pattern=None, master_columns=[],
         name="条件・有効性", summary="条件付き判断のOwner・期限・解消・失効時処置を追跡する。"),
    dict(key="effect", sheet="18_見積・AI効果測定", first_cell="測定ID", id_column="測定ID",
         row_limit=40, state_column="見積係数への反映",
         id_pattern=None, master_columns=[],
         name="見積・AI効果測定", summary="品質を揃えた比較単位ごとに、人時間・経過時間・追加費・純経済効果を測る。"),
    dict(key="unit_economics", sheet="26_事業KPI・投資収益", first_cell="シナリオ", id_column="シナリオ",
         row_limit=3, state_column="予測/実績",
         id_pattern=r"(保守|基準|上振れ)", master_columns=["シナリオ"],
         stop_first_cell="期間資金計画（円／必要なら別の正式財務モデルへリンク）",
         name="単位経済性", summary="成功業務あたりの変動原価と、固定費配賦込みの単位費用を分けて置く。"),
    dict(key="cash_plan", sheet="26_事業KPI・投資収益", first_cell="ケース", id_column="ケース",
         row_limit=3, id_pattern=r"(保守|基準|上振れ)", master_columns=["ケース"],
         stop_first_cell="投資/継続判断の原則",
         name="期間資金計画", summary="期首現金・入出金・期末現金と不足額を、シナリオ別に置く。"),
    dict(key="kpi", sheet="26_事業KPI・投資収益", first_cell="KPI ID", id_column="KPI ID",
         row_limit=16, id_pattern=r"K\d+",
         master_columns=["KPI ID", "領域", "指標候補", "定義・注意", "Owner Role"],
         name="事業KPI・投資収益", summary="事業KPIの定義、対象・分母、目標と停止閾値、最新実測を記録する。"),
]

# Excel の自己点検・自動計算列。システム側では保持しない。
EXCLUDED_COLUMN = re.compile(r"点検|（自動）|（参照）|フラグ")


def input_columns_for(headers: list[str], spec: dict, computed: list[str] | None = None) -> list[str]:
    """案件が入力する列。定義列・Excel専用の点検列・数式列を除く。"""
    master = set(spec["master_columns"]) or {spec["id_column"]}
    derived = set(computed or [])
    return [
        header
        for header in headers
        if header
        and header not in master
        and header not in derived
        and not EXCLUDED_COLUMN.search(header)
    ]


def build() -> dict:
    workbook = openpyxl.load_workbook(SRC, data_only=True)
    # 数式そのものを見るための読み込み。data_only=True では値しか取れない。
    formula_book = openpyxl.load_workbook(SRC, data_only=False)

    # ── 事業ライフサイクル（B0〜B6） ──
    _, phase_rows = table(workbook, "01_事業ライフサイクル・ゲート", "ID")
    phases = [
        dict(
            phase_id=r["ID"],
            name=r["工程"],
            purpose=r["目的"],
            precondition=r.get("開始・前提", ""),
            gate_id=r.get("Gate", ""),
            approver_role_id=r.get("最終A", ""),
            required_evidence=r.get("必要な証拠", ""),
            decision=r.get("判断・戻り先", ""),
        )
        for r in phase_rows
        if re.fullmatch(r"B\d", r["ID"])
    ]

    # ── ゲート定義（G0〜G5）と評価タイプ（E01〜E18） ──
    rows = sheet_rows(workbook, "32_定義マスター")
    gate_head = find_header(rows, "Gate")
    eval_head = find_header(rows, "EvalType")
    gate_headers = [text(c) for c in rows[gate_head]]
    gates = []
    for row in rows[gate_head + 1 : eval_head]:
        if not row or not re.fullmatch(r"G\d", text(row[0])):
            continue
        record = {h: text(c) for h, c in zip(gate_headers, row) if h}
        gates.append(
            dict(
                gate_id=record["Gate"],
                subject=record["判断対象"],
                standard_task_id=record["標準Task"],
                approver_role_id=record["最終A Role"],
                required_evidence=record["必要証拠"],
                allowed_decisions=[d for d in record["許容判断（区切り付き）"].split("|") if d.strip()],
                definition_version=record.get("定義版", ""),
            )
        )
    eval_headers = [text(c) for c in rows[eval_head]]
    eval_types = []
    for row in rows[eval_head + 1 :]:
        if not row or not re.fullmatch(r"E\d+", text(row[0])):
            continue
        record = {h: text(c) for h, c in zip(eval_headers, row) if h}
        eval_types.append(
            dict(
                eval_type_id=record["EvalType"],
                axis=record["評価軸"],
                metrics=record["指標候補"],
                design_note=record["設計上の要点"],
                applicability=record["適用条件"],
                design_role_ids=split_ids(record.get("設計Role", "")),
            )
        )

    # ── AIリスクTier（T0〜T3） ──
    _, tier_rows = table(workbook, "03_AIリスクTier・適用判定", "Tier")
    risk_tiers = [
        dict(
            tier_id=r["Tier"],
            name=r["名称"],
            impact=r["典型的な影響・用途"],
            rigor=r["評価・承認強度"],
            caution=r.get("注意", ""),
        )
        for r in tier_rows
        if re.fullmatch(r"T\d", r["Tier"])
    ]

    # ── 規模テーラリング（S/M/L） ──
    _, scale_rows = table(workbook, "04_規模・テーラリング", "区分")
    scales: dict[str, list[dict]] = {}
    for r in scale_rows:
        key = r["区分"]
        if key not in {"S", "M", "L"}:
            continue
        scales.setdefault(key, []).append(
            dict(
                aspect=r.get("観点", ""),
                approach=r.get("適用の考え方", ""),
                operation=r.get("具体的な運用", ""),
                caution=r.get("留保・禁止する短絡", ""),
            )
        )

    # ── ロール（R01〜） ──
    _, role_rows = table(workbook, "06_ロール・要員計画", "Role ID")
    roles = [
        dict(
            role_id=r["Role ID"],
            name=r["ロール"],
            responsibility=r.get("主要責任", ""),
            involvement=r.get("関与・判断", ""),
            independence_note=r.get("兼務・独立性の注意", ""),
            core_skill_ids=split_ids(r.get("中核Skill", "")),
        )
        for r in role_rows
        if re.fullmatch(r"R\d+", r["Role ID"])
    ]

    # ── スキル辞書（S001〜） ──
    _, skill_rows = table(workbook, "07_スキル辞書", "Skill ID")
    skills = [
        dict(
            skill_id=r["Skill ID"],
            axis=r.get("軸", ""),
            category=r.get("分類", ""),
            name=r["スキル名"],
            definition=r.get("定義", ""),
            level1=r.get("Lv1", ""),
            level2=r.get("Lv2", ""),
            level3=r.get("Lv3", ""),
            evidence=r.get("判定エビデンス", ""),
            related_task_ids=split_ids(r.get("関連B-ID", "")),
            source_ids=split_ids(r.get("根拠ID", "")),
            legacy_skill_ids=split_ids(r.get("旧v3 Skill", "")),
            note=r.get("再編・適用メモ", ""),
        )
        for r in skill_rows
        if re.fullmatch(r"S\d+", r["Skill ID"])
    ]

    # ── 工程タスク（132） ──
    _, task_rows = table(workbook, "02_工程タスク", "タスクID")
    tasks = []
    for r in task_rows:
        if not re.fullmatch(r"B\d-\d+", r["タスクID"]):
            continue
        applicability = r.get("適用条件", "全")
        tasks.append(
            dict(
                task_id=r["タスクID"],
                phase_id=r["タスクID"].split("-")[0],
                phase_name=r.get("工程", ""),
                work_type=r.get("作業区分", ""),
                name=r["タスク名"],
                description=r.get("具体的な実施内容", ""),
                deliverables=r.get("成果物・証拠群", ""),
                exec_role_ids=split_ids(r.get("実施R", "")),
                approver_role_id=text(r.get("承認A", "")),
                completion_criteria=r.get("完了条件", ""),
                applicability=applicability,
                condition_key=applicability.split(":", 1)[1] if applicability.startswith("条件:") else "",
                gate_id=r.get("Gate", ""),
                depends_on=split_ids(r.get("基本依存ID", "")),
                skill_ids=split_ids(r.get("必要スキルID", "")),
                ai_boundary=r.get("AI活用と人の境界", ""),
                # 原本の「根拠ID」「確認用URL」「旧v3 ID」。どの一次資料に依るかを製品内で辿れるようにする。
                source_ids=split_ids(r.get("根拠ID", "")),
                reference_urls=[u.strip() for u in text(r.get("確認用URL", "")).split("\n") if u.strip()],
                legacy_task_ids=split_ids(r.get("旧v3 ID", "")),
            )
        )

    # ── タスク×ロール×スキル（必要Lv） ──
    _, ts_rows = table(workbook, "08_タスク×ロール×スキル", "Task ID")
    task_skills = []
    for r in ts_rows:
        if not re.fullmatch(r"B\d-\d+", r["Task ID"]):
            continue
        level_raw = r.get("必要Lv", "")
        try:
            level = int(float(level_raw))
        except (TypeError, ValueError):
            continue
        task_skills.append(
            dict(
                task_id=r["Task ID"],
                skill_id=r["Skill ID"],
                required_level=level,
                exec_role_ids=split_ids(r.get("実施R", "")),
                approver_role_id=text(r.get("承認A", "")),
                evidence=r.get("確認する証拠", ""),
            )
        )

    # ── 成果物・正本マップ ──
    _, ev_rows = table(workbook, "09_成果物・正本マップ", "Evidence ID")
    evidence = [
        dict(
            evidence_id=r["Evidence ID"],
            task_id=r["Task ID"],
            deliverables=r.get("成果物群", ""),
            recommended_source=r.get("推奨する正本", ""),
            owner_role_id=text(r.get("Ownerロール", "")),
            minimum_content=r.get("最低限の証拠内容", ""),
        )
        for r in ev_rows
        if r.get("Task ID")
    ]

    # ── 台帳定義とマスタ行 ──
    ledgers = []
    for spec in LEDGERS:
        # 行と注記はシート末尾まで読む（原本の注記ブロックを落とさない）。
        headers, records = table(
            workbook, spec["sheet"], spec["first_cell"], spec.get("stop_first_cell")
        )
        # 入力規則の対象範囲を決めるためだけに、表の行範囲を別途求める。
        _, _, head_index, data_end = table_ex(
            workbook, spec["sheet"], spec["first_cell"], spec.get("stop_first_cell")
        )
        rules = column_rules(workbook, spec["sheet"], headers, head_index, data_end)
        computed = derived_columns(formula_book, spec["sheet"], headers, head_index, data_end)
        # 名前付き範囲を解決できるものは値に展開する。
        for column, rule in rules.items():
            if rule.get("source") == "EvalIDs":
                rule["options"] = [item["eval_type_id"] for item in eval_types]
        pattern = re.compile(spec["id_pattern"]) if spec["id_pattern"] else None
        blocks = table_blocks(workbook, spec["sheet"])
        indexed = table_indexed(
            workbook, spec["sheet"], spec["first_cell"], spec.get("stop_first_cell")
        )
        assert len(indexed) == len(records)
        rows: list[dict] = []
        notes: list[str] = []
        for (index, _), record in zip(indexed, records):
            row_id = record.get(spec["id_column"], "")
            if pattern and pattern.fullmatch(row_id):
                rows.append({k: v for k, v in record.items() if k in spec["master_columns"] and v})
                continue
            # 表の行（自分の表も、同じシートの別台帳の表も）は注記にしない。
            if any(start <= index <= end for start, end in blocks):
                continue
            # 表の外にある行は、シート内の注記ブロック。運用上の注意として残す。
            joined = " / ".join(v for v in record.values() if v)
            if joined:
                notes.append(joined)
        ledgers.append(
            dict(
                key=spec["key"],
                name=spec["name"],
                summary=spec["summary"],
                source_sheet=spec["sheet"],
                id_column=spec["id_column"],
                seeded=bool(spec["id_pattern"]),
                master_columns=spec["master_columns"],
                input_columns=input_columns_for(headers, spec, computed),
                derived_columns=computed,
                # 原本33 K03 が名指しする予約行数。上限外は原本の改訂が要る。
                row_limit=spec.get("row_limit"),
                # 状態列と、その値になったら上書きを止める状態（原本15「承認後の上書きをせず新しい版を作る」）。
                state_column=spec.get("state_column", ""),
                locked_states=spec.get("locked_states", []),
                column_rules={
                    column: rule
                    for column, rule in rules.items()
                    if column in input_columns_for(headers, spec, computed)
                },
                rows=rows,
                notes=notes,
            )
        )

    # ── AI駆動開発・ハーネス標準（案件入力を持たない参照リスト） ──
    _, harness_rows = table(workbook, "14_AI駆動開発・ハーネス標準", "制御ID")
    harness = [
        dict(
            control_id=r["制御ID"],
            target=r.get("対象", ""),
            standard=r.get("標準", ""),
            detail=r.get("実施内容", ""),
            owner_role_id=text(r.get("Owner", "")),
            evidence=r.get("証拠", ""),
            related_task_ids=split_ids(r.get("関連Task", "")),
        )
        for r in harness_rows
        if re.fullmatch(r"A\d+", r["制御ID"])
    ]

    # ── 調査ソース（U01〜U03 / W01〜W18） ──
    # 各シートの「根拠ID」はこの表を引く。これが無いとID単体では意味を解決できない。
    _, source_rows = table(workbook, "24_調査ソース・変更履歴", "Source ID")
    sources = [
        dict(
            source_id=r["Source ID"],
            published=r.get("公開/版", ""),
            organization=r.get("組織・提供元", ""),
            title=r.get("資料名", ""),
            evidence_type=r.get("証拠の種類", ""),
            adopted=r.get("この資料で採用した内容", ""),
            limitation=r.get("確認範囲・限界", ""),
            applied_to=r.get("反映先", ""),
            url=r.get("URL/入力ファイル", ""),
            checked_on=text(r.get("確認日", ""))[:10],
        )
        for r in source_rows
        if re.fullmatch(r"[UW]\d+", r["Source ID"])
    ]

    # ── 規模によらず省略できない原則（04の区分「全」） ──
    tailoring = [
        dict(
            aspect=r.get("観点", ""),
            approach=r.get("適用の考え方", ""),
            operation=r.get("具体的な運用", ""),
            caution=r.get("留保・禁止する短絡", ""),
        )
        for r in scale_rows
        if r.get("区分") == "全"
    ]

    # ── 参考工数（未較正。計画の目安としてのみ使う） ──
    _, effort_rows = table(workbook, "04_規模・テーラリング", "工程")
    effort_reference = [
        dict(
            phase=r["工程"],
            s_min=r.get("S下限", ""),
            s_max=r.get("S上限", ""),
            m_min=r.get("M下限", ""),
            m_max=r.get("M上限", ""),
            l_min=r.get("L下限", ""),
            l_max=r.get("L上限", ""),
            unit=r.get("単位・範囲", ""),
        )
        for r in effort_rows
        if r.get("工程")
    ]

    # ── 標準開発ループ（工程を横断して繰り返す8ステップ） ──
    _, loop_rows, _, _ = table_ex(workbook, "14_AI駆動開発・ハーネス標準", "順", stop_first_cell="設定")
    dev_loop = [
        dict(
            step=r["順"],
            name=r.get("ステップ", ""),
            input=r.get("入力/処理", ""),
            ai_role=r.get("AIの担当", ""),
            human_role=r.get("人の担当", ""),
            stop_condition=r.get("停止・差戻し", ""),
        )
        for r in loop_rows
        if re.fullmatch(r"\d+", r.get("順", ""))
    ]

    # ── Agent/Skill実行設定（案件で実運用値を記入する項目） ──
    _, setting_rows, _, _ = table_ex(
        workbook, "14_AI駆動開発・ハーネス標準", "設定", stop_first_cell="試験ID"
    )
    runtime_settings = [
        dict(name=r["設定"], check=r.get("確認事項", ""))
        for r in setting_rows
        if r.get("設定") and r.get("確認事項")
    ]

    # ── 負の試験（AT01〜AT07。v1.1で追加された実試験仕様） ──
    _, at_rows = table(workbook, "14_AI駆動開発・ハーネス標準", "試験ID")
    harness_tests = [
        dict(
            test_id=r["試験ID"],
            applies_when=r.get("適用", ""),
            theme=r.get("試験テーマ", ""),
            specification=r.get("具体的な負の試験／受入条件", ""),
            owner_role_id=text(r.get("Owner", "")),
            evidence=r.get("保存する証拠", ""),
            related_task_ids=split_ids(r.get("関連Task", "")),
            note=r.get("実案件実行", ""),
        )
        for r in at_rows
        if re.fullmatch(r"AT\d+", r.get("試験ID", ""))
    ]

    # ── 投資/継続判断の原則（原本26の末尾。G4の判断語彙の意味） ──
    _, decision_rows, _, _ = table_ex(workbook, "26_事業KPI・投資収益", "判断")
    investment_decisions = [
        dict(
            decision=r["判断"],
            condition=r.get("条件を案件で定義", ""),
            caution=r.get("証拠・注意", ""),
        )
        for r in decision_rows
        if r.get("判断")
    ]

    return dict(
        version="v1.1",
        source=SRC.name,
        phases=phases,
        gates=gates,
        eval_types=eval_types,
        risk_tiers=risk_tiers,
        scales=scales,
        roles=roles,
        skills=skills,
        tasks=tasks,
        task_skills=task_skills,
        evidence=evidence,
        harness=harness,
        harness_tests=harness_tests,
        dev_loop=dev_loop,
        runtime_settings=runtime_settings,
        tailoring=tailoring,
        effort_reference=effort_reference,
        sources=sources,
        investment_decisions=investment_decisions,
        ledgers=ledgers,
    )


# 原本 v1.1 の件数。見出しや採番が変わると静かに欠損するので、ここで止める。
EXPECTED_COUNTS = {
    "phases": 7, "gates": 6, "eval_types": 18, "risk_tiers": 4, "roles": 20,
    "skills": 106, "tasks": 132, "task_skills": 427, "evidence": 132,
    "harness": 16, "harness_tests": 7, "dev_loop": 8, "runtime_settings": 8,
    "tailoring": 3, "effort_reference": 8, "sources": 21, "ledgers": 25, "investment_decisions": 3,
}
EXPECTED_LEDGER_ROWS = {
    "risk_screening": 10, "feature_decision": 6,
    "required_eval": 0, "condition": 0, "effect": 0, "unit_economics": 3, "cash_plan": 3,
    "role_staffing": 20, "gate_run": 0, "task_run": 0, "assignment": 0,
    "privacy": 14, "adr": 12, "eval_plan": 18, "risk": 12, "slo": 8,
    "retirement": 10, "contract": 10, "hypothesis": 12, "kpi": 16,
    "data": 0, "dependency": 0, "eval_run": 0, "release": 0, "incident": 0,
}


def check_counts(master: dict) -> list[str]:
    problems = []
    for key, expected in EXPECTED_COUNTS.items():
        actual = len(master[key])
        if actual != expected:
            problems.append(f"{key}: {actual} 件（期待 {expected} 件）")
    by_key = {ledger["key"]: ledger for ledger in master["ledgers"]}
    for key, expected in EXPECTED_LEDGER_ROWS.items():
        ledger = by_key.get(key)
        if ledger is None:
            problems.append(f"台帳 {key} が無い")
        elif len(ledger["rows"]) != expected:
            problems.append(f"台帳 {key} の点検行: {len(ledger['rows'])} 行（期待 {expected} 行）")
    rules = sum(len(ledger["column_rules"]) for ledger in master["ledgers"])
    if rules < 30:
        problems.append(f"台帳の入力規則: {rules} 列（原本の39件から30列以上を期待）")
    if not all(task["source_ids"] for task in master["tasks"]):
        problems.append("根拠IDの無いタスクがある")
    return problems


def main() -> int:
    if not SRC.exists():
        print(f"元資料が見つかりません: {SRC}", file=sys.stderr)
        return 1
    master = build()
    problems = check_counts(master)
    if problems:
        print("抽出結果が期待と違います。原本の見出しや採番が変わっていないか確認してください:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 2
    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(json.dumps(master, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"生成: {DST.relative_to(ROOT)}")
    for key in ("phases", "gates", "eval_types", "risk_tiers", "roles", "skills", "tasks", "task_skills",
                "evidence", "harness", "harness_tests", "dev_loop", "runtime_settings", "tailoring",
                "effort_reference", "sources", "investment_decisions"):
        print(f"  {key}: {len(master[key])}")
    print(f"  ledgers: {len(master['ledgers'])}")
    for ledger in master["ledgers"]:
        print(
            f"    {ledger['key']:<12} 点検行 {len(ledger['rows']):>3}"
            f"  定義列 {len(ledger['master_columns']):>2}"
            f"  入力列 {len(ledger['input_columns']):>2}"
            f"  入力規則 {len(ledger['column_rules']):>2}"
            f"  注記 {len(ledger['notes']):>2}"
        )
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
