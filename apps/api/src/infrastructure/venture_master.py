"""事業PJ工程マスタ（読み取り専用）.

`docs/AIシステム自社事業PJ工程管理_v1_1_敵対的レビュー反映版.xlsx` から
`tools/extract_venture_master.py` で生成した JSON を読み込む。

マスタはテナントに依存しない標準定義であり、案件（Venture）はこの定義を参照して
自分の台帳を持つ。文言は原本のまま扱い、システム側で書き換えない。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parent / "data" / "venture_process_master.json"

# 適用判定の値
APPLICABILITY_UNDECIDED = "未判定"
APPLICABILITY_APPLIED = "適用"
APPLICABILITY_EXCLUDED = "対象外"
APPLICABILITY_VALUES = (APPLICABILITY_UNDECIDED, APPLICABILITY_APPLIED, APPLICABILITY_EXCLUDED)

# タスクの進捗状態
TASK_STATUS_VALUES = ("未着手", "進行中", "完了", "保留")

# 案件の状態
VENTURE_STATUS_VALUES = ("計画中", "進行中", "停止", "終了")

SCALE_VALUES = ("S", "M", "L")


@dataclass(frozen=True, slots=True)
class VentureProcessMaster:
    """抽出済みマスタのラッパー。"""

    raw: dict[str, Any]

    # ── 基本アクセサ ──────────────────────────────────
    @property
    def version(self) -> str:
        return self.raw.get("version", "")

    @property
    def phases(self) -> list[dict]:
        return self.raw["phases"]

    @property
    def gates(self) -> list[dict]:
        return self.raw["gates"]

    @property
    def eval_types(self) -> list[dict]:
        return self.raw["eval_types"]

    @property
    def risk_tiers(self) -> list[dict]:
        return self.raw["risk_tiers"]

    @property
    def scales(self) -> dict[str, list[dict]]:
        return self.raw["scales"]

    @property
    def roles(self) -> list[dict]:
        return self.raw["roles"]

    @property
    def skills(self) -> list[dict]:
        return self.raw["skills"]

    @property
    def tasks(self) -> list[dict]:
        return self.raw["tasks"]

    @property
    def task_skills(self) -> list[dict]:
        return self.raw["task_skills"]

    @property
    def evidence(self) -> list[dict]:
        return self.raw["evidence"]

    @property
    def harness(self) -> list[dict]:
        return self.raw["harness"]

    @property
    def ledgers(self) -> list[dict]:
        return self.raw["ledgers"]

    @property
    def harness_tests(self) -> list[dict]:
        """原本14の負の試験 AT01〜AT07。v1.1で追加された実試験仕様。"""
        return self.raw.get("harness_tests", [])

    @property
    def dev_loop(self) -> list[dict]:
        """原本14の標準開発ループ（工程を横断して繰り返す8ステップ）。"""
        return self.raw.get("dev_loop", [])

    @property
    def runtime_settings(self) -> list[dict]:
        """原本14のAgent/Skill実行設定。案件で実運用値を記入する項目。"""
        return self.raw.get("runtime_settings", [])

    @property
    def tailoring(self) -> list[dict]:
        """原本04の区分「全」。規模によらず省略できない原則。"""
        return self.raw.get("tailoring", [])

    @property
    def effort_reference(self) -> list[dict]:
        """原本04の参考工数。未較正の目安。"""
        return self.raw.get("effort_reference", [])

    @property
    def investment_decisions(self) -> list[dict]:
        """原本26末尾の投資/継続判断の原則。G4の判断語彙の意味。"""
        return self.raw.get("investment_decisions", [])

    @property
    def sources(self) -> list[dict]:
        """原本24の調査ソース。各シートの「根拠ID」はこの表を引く。"""
        return self.raw.get("sources", [])

    # ── 索引 ────────────────────────────────────────
    @property
    def task_by_id(self) -> dict[str, dict]:
        return {task["task_id"]: task for task in self.tasks}

    @property
    def skill_by_id(self) -> dict[str, dict]:
        return {skill["skill_id"]: skill for skill in self.skills}

    @property
    def role_by_id(self) -> dict[str, dict]:
        return {role["role_id"]: role for role in self.roles}

    @property
    def gate_by_id(self) -> dict[str, dict]:
        return {gate["gate_id"]: gate for gate in self.gates}

    @property
    def ledger_by_key(self) -> dict[str, dict]:
        return {ledger["key"]: ledger for ledger in self.ledgers}

    @property
    def source_by_id(self) -> dict[str, dict]:
        return {source["source_id"]: source for source in self.sources}

    @property
    def evidence_by_task_id(self) -> dict[str, dict]:
        return {item["task_id"]: item for item in self.evidence}

    def skills_for_task(self, task_id: str) -> list[dict]:
        """タスクが要求するスキルと必要Lv。"""
        return [item for item in self.task_skills if item["task_id"] == task_id]

    @property
    def condition_keys(self) -> list[str]:
        """タスクの適用条件に現れる条件キー（RAG / Agent / 外販・課金 など）。

        原本の「適用条件」列の値をそのまま使う。「外販・課金」「事故・重大失敗」の
        ように中黒を含む条件は1つの概念なので、分解しない。
        """
        keys: list[str] = []
        for task in self.tasks:
            condition = task.get("condition_key", "")
            if condition and condition not in keys:
                keys.append(condition)
        return keys

    # ── 適用判定 ────────────────────────────────────
    def suggest_applicability(self, task_id: str, conditions: dict[str, str]) -> str:
        """案件の条件判定から、タスクの適用可否を提案する。

        提案であって決定ではない。最終的な適用判定は人が承認する
        （原本 17_ロードマップ・案件実行管理 の「適用判定承認者」に対応）。

        - 適用条件が「全」のタスクは常に「適用」
        - 案件がその条件をそのまま判定していれば、その判定に従う
        - 未判定の場合に限り、中黒で分けた部分条件から推測する。
          いずれかが「適用」なら「適用」。取りこぼしを防ぐため広めに倒す。
        - すべての部分条件が「対象外」なら「対象外」、それ以外は「未判定」
        """
        task = self.task_by_id.get(task_id)
        if task is None:
            return APPLICABILITY_UNDECIDED
        condition = task.get("condition_key", "")
        if not condition:
            return APPLICABILITY_APPLIED
        declared = conditions.get(condition, APPLICABILITY_UNDECIDED)
        if declared in (APPLICABILITY_APPLIED, APPLICABILITY_EXCLUDED):
            return declared
        parts = [part.strip() for part in condition.split("・") if part.strip()]
        if len(parts) < 2:
            return APPLICABILITY_UNDECIDED
        decisions = [conditions.get(part, APPLICABILITY_UNDECIDED) for part in parts]
        if APPLICABILITY_APPLIED in decisions:
            return APPLICABILITY_APPLIED
        if all(value == APPLICABILITY_EXCLUDED for value in decisions):
            return APPLICABILITY_EXCLUDED
        return APPLICABILITY_UNDECIDED

    def default_conditions(self) -> dict[str, str]:
        return {key: APPLICABILITY_UNDECIDED for key in self.condition_keys}

    # ── スキル需要 ──────────────────────────────────
    def skill_demand(self, task_ids: list[str]) -> list[dict]:
        """対象タスク群が要求するスキルを、必要Lvの最大値で集約する。"""
        wanted = set(task_ids)
        demand: dict[str, dict] = {}
        for item in self.task_skills:
            if item["task_id"] not in wanted:
                continue
            skill_id = item["skill_id"]
            current = demand.get(skill_id)
            if current is None:
                skill = self.skill_by_id.get(skill_id, {})
                demand[skill_id] = {
                    "skillId": skill_id,
                    "name": skill.get("name", skill_id),
                    "axis": skill.get("axis", ""),
                    "category": skill.get("category", ""),
                    "definition": skill.get("definition", ""),
                    "requiredLevel": item["required_level"],
                    "taskIds": [item["task_id"]],
                }
            else:
                current["requiredLevel"] = max(current["requiredLevel"], item["required_level"])
                current["taskIds"].append(item["task_id"])
        ordered = sorted(
            demand.values(),
            key=lambda value: (-value["requiredLevel"], -len(value["taskIds"]), value["skillId"]),
        )
        return ordered


@lru_cache(maxsize=1)
def load_master() -> VentureProcessMaster:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"事業PJ工程マスタが見つかりません: {DATA_PATH}. "
            "`python tools/extract_venture_master.py` を実行してください。"
        )
    return VentureProcessMaster(raw=json.loads(DATA_PATH.read_text(encoding="utf-8")))
