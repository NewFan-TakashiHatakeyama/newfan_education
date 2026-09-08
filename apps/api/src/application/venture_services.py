"""事業PJ台帳のアプリケーションサービス。

工程マスタは読み取り専用で全員が参照できる。案件台帳の更新は役割で制限する。
学習者は自分に割り当てられた工程タスクだけ更新できる。
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from domain.models import UserContext
from infrastructure.postgres_venture import LedgerRowKeyConflictError, PostgresVentureRepository
from infrastructure.settings import load_settings
from infrastructure.venture_ledger_checks import blocking, evaluate
from infrastructure.venture_rules import as_of, is_before, parse_date
from infrastructure.venture_master import (
    APPLICABILITY_EXCLUDED,
    APPLICABILITY_VALUES,
    SCALE_VALUES,
    TASK_STATUS_VALUES,
    VENTURE_STATUS_VALUES,
    load_master,
)

# 原本 06_ロール・要員計画: R19 は独立品質・安全の決裁者で「実装責任者と分離」。
# このロールが承認するタスクは、担当者本人が完了承認できない。
INDEPENDENT_APPROVER_ROLE = "R19"

VIEWER_ROLES = {"learner", "mentor", "recruiter", "admin", "content_editor"}
MANAGER_ROLES = {"admin", "recruiter"}
EDITOR_ROLES = {"admin", "recruiter", "content_editor"}
ASSESSOR_ROLES = {"admin", "recruiter", "mentor"}

# テナント内の全案件を見られる役割。これ以外は要員として登録された案件だけ見える。
# 案件台帳にはデータ台帳の個人情報区分・保存場所や、要員のスキル評価・育成計画が
# 入るため、案件に関与していない利用者には見せない。
ALL_VENTURES_ROLES = MANAGER_ROLES


class VentureAccessError(PermissionError):
    """役割が操作を許可されていない。"""


class VentureNotFoundError(ValueError):
    """案件または台帳の行が見つからない。"""


class VentureValidationError(ValueError):
    """入力値がマスタの定義に合わない。"""


@dataclass
class VentureService:
    repository: PostgresVentureRepository

    # ── 権限 ────────────────────────────────────────
    def _assert(self, actor: UserContext, allowed: set[str]) -> None:
        # 工程マスタは自社の工程定義そのものなので、有効なテナントだけに提供する。
        if actor.tenant_id not in load_settings().venture_ledger_tenants:
            raise VentureAccessError("この機能はこのテナントでは利用できません")
        if actor.role not in allowed:
            raise VentureAccessError("この操作は許可されていません")

    def _get_venture(self, actor: UserContext, venture_id: str) -> dict:
        venture = self.repository.get_venture(actor.tenant_id, venture_id)
        if venture is None:
            raise VentureNotFoundError("案件が見つかりません")
        if actor.role not in ALL_VENTURES_ROLES and not self.repository.is_member(
            actor.tenant_id, venture_id, actor.user_id
        ):
            # 存在自体を伏せるため 403 ではなく 404 に倒す。
            raise VentureNotFoundError("案件が見つかりません")
        return venture

    def _can_see_all_assessments(self, actor: UserContext) -> bool:
        return actor.role in ALL_VENTURES_ROLES or actor.role in ASSESSOR_ROLES

    # ── マスタ ──────────────────────────────────────
    def get_master(self, actor: UserContext) -> dict:
        self._assert(actor, VIEWER_ROLES)
        return self.repository.master_overview()

    def get_master_tasks(self, actor: UserContext, phase_id: str | None = None) -> dict:
        self._assert(actor, VIEWER_ROLES)
        master = load_master()
        tasks = master.tasks
        if phase_id:
            tasks = [task for task in tasks if task["phase_id"] == phase_id]
        return {
            "items": [
                {
                    "taskId": task["task_id"],
                    "phaseId": task["phase_id"],
                    "phaseName": task["phase_name"],
                    "workType": task["work_type"],
                    "name": task["name"],
                    "description": task["description"],
                    "deliverables": task["deliverables"],
                    "completionCriteria": task["completion_criteria"],
                    "applicability": task["applicability"],
                    "gateId": task["gate_id"],
                    "execRoleIds": task["exec_role_ids"],
                    "approverRoleId": task["approver_role_id"],
                    "dependsOn": task["depends_on"],
                    "skillIds": task["skill_ids"],
                    "aiBoundary": task["ai_boundary"],
                    "sourceIds": task.get("source_ids", []),
                    "referenceUrls": task.get("reference_urls", []),
                }
                for task in tasks
            ]
        }

    def get_master_standards(self, actor: UserContext) -> dict:
        self._assert(actor, VIEWER_ROLES)
        return self.repository.master_standards()

    def get_master_skills(self, actor: UserContext) -> dict:
        self._assert(actor, VIEWER_ROLES)
        master = load_master()
        return {
            "items": [
                {
                    "skillId": skill["skill_id"],
                    "axis": skill["axis"],
                    "category": skill["category"],
                    "name": skill["name"],
                    "definition": skill["definition"],
                    "level1": skill["level1"],
                    "level2": skill["level2"],
                    "level3": skill["level3"],
                    "evidence": skill["evidence"],
                    "sourceIds": skill.get("source_ids", []),
                    "note": skill.get("note", ""),
                }
                for skill in master.skills
            ]
        }

    # ── 案件 ────────────────────────────────────────
    def list_ventures(self, actor: UserContext) -> dict:
        self._assert(actor, VIEWER_ROLES)
        items = self.repository.list_ventures(actor.tenant_id)
        if actor.role not in ALL_VENTURES_ROLES:
            visible = self.repository.member_venture_ids(actor.tenant_id, actor.user_id)
            items = [item for item in items if item["id"] in visible]
        return {"items": items}

    def get_venture(self, actor: UserContext, venture_id: str) -> dict:
        self._assert(actor, VIEWER_ROLES)
        return self._get_venture(actor, venture_id)

    def create_venture(self, actor: UserContext, payload: dict) -> dict:
        self._assert(actor, MANAGER_ROLES)
        self._validate_venture_payload(payload)
        if not (payload.get("name") or "").strip():
            raise VentureValidationError("事業・サービス名を入力してください")
        return self.repository.create_venture(actor.tenant_id, actor.user_id, payload)

    def update_venture(self, actor: UserContext, venture_id: str, payload: dict) -> dict:
        self._assert(actor, MANAGER_ROLES)
        self._get_venture(actor, venture_id)
        self._validate_venture_payload(payload)
        venture = self.repository.update_venture(actor.tenant_id, venture_id, payload)
        if venture is None:
            raise VentureNotFoundError("案件が見つかりません")
        return venture

    def delete_venture(self, actor: UserContext, venture_id: str) -> dict:
        self._assert(actor, MANAGER_ROLES)
        self._get_venture(actor, venture_id)
        if not self.repository.delete_venture(actor.tenant_id, venture_id, actor.user_id, actor.role):
            raise VentureNotFoundError("案件が見つかりません")
        return {"removed": True}

    def _validate_venture_payload(self, payload: dict) -> None:
        master = load_master()
        if payload.get("scale") and payload["scale"] not in SCALE_VALUES:
            raise VentureValidationError(f"規模は {', '.join(SCALE_VALUES)} のいずれかです")
        if payload.get("status") and payload["status"] not in VENTURE_STATUS_VALUES:
            raise VentureValidationError(f"状態は {', '.join(VENTURE_STATUS_VALUES)} のいずれかです")
        tiers = {tier["tier_id"] for tier in master.risk_tiers}
        if payload.get("riskTier") and payload["riskTier"] not in tiers:
            raise VentureValidationError(f"Risk Tier は {', '.join(sorted(tiers))} のいずれかです")
        phases = {phase["phase_id"] for phase in master.phases}
        if payload.get("currentPhaseId") and payload["currentPhaseId"] not in phases:
            raise VentureValidationError(f"工程は {', '.join(sorted(phases))} のいずれかです")
        conditions = payload.get("conditions")
        if conditions:
            known = set(master.condition_keys)
            for key, value in conditions.items():
                if key not in known:
                    raise VentureValidationError(f"未知の適用条件です: {key}")
                if value not in APPLICABILITY_VALUES:
                    raise VentureValidationError(f"適用条件の値は {', '.join(APPLICABILITY_VALUES)} のいずれかです")

    # ── 工程タスク ──────────────────────────────────
    def list_tasks(self, actor: UserContext, venture_id: str, **filters) -> dict:
        self._assert(actor, VIEWER_ROLES)
        self._get_venture(actor, venture_id)
        return {"items": self.repository.list_tasks(actor.tenant_id, venture_id, **filters)}

    def update_task(self, actor: UserContext, venture_id: str, task_row_id: str, payload: dict) -> dict:
        self._assert(actor, VIEWER_ROLES)
        self._get_venture(actor, venture_id)
        if payload.get("status") and payload["status"] not in TASK_STATUS_VALUES:
            raise VentureValidationError(f"状態は {', '.join(TASK_STATUS_VALUES)} のいずれかです")
        if payload.get("applicability") and payload["applicability"] not in APPLICABILITY_VALUES:
            raise VentureValidationError(f"適用判定は {', '.join(APPLICABILITY_VALUES)} のいずれかです")
        current = self.repository.get_task(actor.tenant_id, venture_id, task_row_id)
        if current is None:
            raise VentureNotFoundError("タスクが見つかりません")

        if actor.role not in EDITOR_ROLES:
            # 学習者・メンターは自分に割り当てられたタスクの進捗だけ更新できる。
            if current["assigneeUserId"] != actor.user_id:
                raise VentureAccessError("自分が担当するタスクのみ更新できます")
            allowed_keys = {"status", "actualStart", "actualEnd", "actualHours", "evidenceUri", "blocker", "note"}
            rejected = set(payload) - allowed_keys
            if rejected:
                raise VentureAccessError(f"この項目は担当者では変更できません: {', '.join(sorted(rejected))}")

        if payload.get("applicability") == APPLICABILITY_EXCLUDED and not (
            payload.get("applicabilityReason") or current["applicabilityReason"] or ""
        ).strip():
            # 原本 17 は対象外に除外理由・代替証拠を要求している。
            raise VentureValidationError("対象外にする理由（代替証拠）を入力してください")

        self._assert_task_dates(self._get_venture(actor, venture_id), current, payload)

        if payload.get("dependsOn") is not None:
            self._assert_dependency_change(current, payload)

        if payload.get("approveCompletion") is True:
            self._assert_completion_approvable(actor, current, payload)

        task = self.repository.update_task(
            actor.tenant_id, venture_id, task_row_id, payload, actor.user_id, actor.role
        )
        if task is None:
            raise VentureNotFoundError("タスクが見つかりません")
        return task

    def _assert_dependency_change(self, current: dict, payload: dict) -> None:
        """原本17の依存記法点検と依存変更承認。

        標準依存（原本02の基本依存ID）から変えるには理由が要る。区切り文字だけの
        依存、未知のID、自己参照、8件超過は受け付けない。
        """
        depends_on = payload["dependsOn"]
        for token in depends_on:
            if not token or token != token.strip():
                raise VentureValidationError("依存記法不正: 空の依存や余分な空白は指定できません")
        if len(depends_on) > 8:
            raise VentureValidationError("依存8件超過: 直接依存は8件までです")
        known = set(load_master().task_by_id)
        unknown = [token for token in depends_on if token not in known]
        if unknown:
            raise VentureValidationError(f"依存ID不正: 未知のタスクです: {', '.join(unknown)}")
        if current["taskId"] in depends_on:
            raise VentureValidationError("依存ID不正: 自分自身を依存にできません")
        if sorted(depends_on) != sorted(current["standardDependsOn"]) and not (
            payload.get("dependencyChangeReason") or ""
        ).strip():
            raise VentureValidationError("依存変更承認不足: 標準依存を変える理由を入力してください")

    def _assert_task_dates(self, venture: dict, current: dict, payload: dict) -> None:
        """原本17!W の日付の節。未来日と前後逆転を入口で弾く。

        管理基準日（原本00）より後の実績は、原本では「実績・承認日不正」として
        完了記録フラグを立てない。
        """
        basis, _ = as_of(venture)
        merged = {**current, **{k: v for k, v in payload.items() if v is not None}}
        for key, label in (("actualStart", "実開始"), ("actualEnd", "実完了")):
            value = parse_date(merged.get(key))
            if value is not None and value > basis:
                raise VentureValidationError(
                    f"実績・承認日不正: {label} は管理基準日（{basis.isoformat()}）より未来にできません"
                )
        if is_before(merged.get("plannedEnd"), merged.get("plannedStart")):
            raise VentureValidationError("予定日不正: 予定完了は予定開始より前にできません")
        if is_before(merged.get("actualEnd"), merged.get("actualStart")):
            raise VentureValidationError("完了・適用日逆転: 実完了は実開始より前にできません")

    def _assert_completion_approvable(self, actor: UserContext, current: dict, payload: dict) -> None:
        """完了承認の前提をサーバ側で確かめる。

        画面のボタン制御だけでは、APIを直接叩けば素通りする。原本 17 の完了記録点検は
        完了証拠・状態・承認の独立性を満たさない記録を「完了証拠不足」「独立承認不足」
        として弾いている。
        """
        evidence = payload.get("evidenceUri", current["evidenceUri"]) or ""
        if not evidence.strip():
            raise VentureValidationError("完了証拠のURIを記録してから承認してください")
        status = payload.get("status", current["status"])
        if status != "完了":
            raise VentureValidationError("状態を「完了」にしてから承認してください")
        if current["approverRoleId"] == INDEPENDENT_APPROVER_ROLE:
            assignee = payload.get("assigneeUserId", current["assigneeUserId"])
            if assignee and assignee == actor.user_id:
                raise VentureValidationError(
                    "このタスクの承認は実施者と分離が必要です（承認ロール "
                    f"{INDEPENDENT_APPROVER_ROLE}）。担当者以外が承認してください"
                )

    def bulk_decide_applicability(self, actor: UserContext, venture_id: str, payload: dict) -> dict:
        self._assert(actor, EDITOR_ROLES)
        self._get_venture(actor, venture_id)
        applicability = payload.get("applicability")
        if applicability not in APPLICABILITY_VALUES:
            raise VentureValidationError(f"適用判定は {', '.join(APPLICABILITY_VALUES)} のいずれかです")
        task_row_ids = payload.get("taskRowIds") or []
        if not task_row_ids:
            raise VentureValidationError("対象のタスクを選択してください")
        if applicability == APPLICABILITY_EXCLUDED and not (payload.get("reason") or "").strip():
            raise VentureValidationError("対象外にする理由（代替証拠）を入力してください")
        updated = self.repository.bulk_decide_applicability(
            actor.tenant_id, venture_id, task_row_ids, applicability, payload.get("reason", ""), actor.user_id
        )
        return {"updated": updated}

    # ── ゲート ──────────────────────────────────────
    def list_gates(self, actor: UserContext, venture_id: str) -> dict:
        self._assert(actor, VIEWER_ROLES)
        self._get_venture(actor, venture_id)
        return {"items": self.repository.list_gates(actor.tenant_id, venture_id)}

    def update_gate(self, actor: UserContext, venture_id: str, gate_row_id: str, payload: dict) -> dict:
        self._assert(actor, MANAGER_ROLES)
        self._get_venture(actor, venture_id)
        if payload.get("decision"):
            gates = self.repository.list_gates(actor.tenant_id, venture_id)
            gate = next((item for item in gates if item["id"] == gate_row_id), None)
            if gate is None:
                raise VentureNotFoundError("ゲートが見つかりません")
            allowed = set(gate["allowedDecisions"])
            if payload["decision"] not in allowed:
                raise VentureValidationError(
                    f"{gate['gateId']} で選べる判断は {', '.join(sorted(allowed))} です"
                )
        gate = self.repository.update_gate(
            actor.tenant_id, venture_id, gate_row_id, payload, actor.user_id, actor.role
        )
        if gate is None:
            raise VentureNotFoundError("ゲートが見つかりません")
        return gate

    # ── 要員 ────────────────────────────────────────
    def list_members(self, actor: UserContext, venture_id: str) -> dict:
        self._assert(actor, VIEWER_ROLES)
        self._get_venture(actor, venture_id)
        return {"items": self.repository.list_members(actor.tenant_id, venture_id)}

    def add_member(self, actor: UserContext, venture_id: str, payload: dict) -> dict:
        self._assert(actor, MANAGER_ROLES)
        self._get_venture(actor, venture_id)
        master = load_master()
        role_id = payload.get("roleId", "")
        if role_id not in master.role_by_id:
            raise VentureValidationError(f"未知のロールです: {role_id}")
        user_id = (payload.get("userId") or "").strip()
        if not user_id:
            raise VentureValidationError("担当者を選択してください")
        return self.repository.add_member(
            actor.tenant_id, venture_id, user_id, role_id, payload.get("allocationNote", "")
        )

    def remove_member(self, actor: UserContext, venture_id: str, member_id: str) -> dict:
        self._assert(actor, MANAGER_ROLES)
        self._get_venture(actor, venture_id)
        if not self.repository.remove_member(actor.tenant_id, venture_id, member_id):
            raise VentureNotFoundError("要員が見つかりません")
        return {"removed": True}

    # ── 汎用台帳 ────────────────────────────────────
    def list_ledger(self, actor: UserContext, venture_id: str, ledger_key: str) -> dict:
        self._assert(actor, VIEWER_ROLES)
        self._get_venture(actor, venture_id)
        result = self.repository.list_ledger_entries(actor.tenant_id, venture_id, ledger_key)
        if result is None:
            raise VentureNotFoundError(f"台帳が見つかりません: {ledger_key}")
        return result

    def upsert_ledger_entry(self, actor: UserContext, venture_id: str, ledger_key: str, payload: dict) -> dict:
        self._assert(actor, EDITOR_ROLES)
        self._get_venture(actor, venture_id)
        ledger = load_master().ledger_by_key.get(ledger_key)
        if ledger is None:
            raise VentureNotFoundError(f"台帳が見つかりません: {ledger_key}")
        values = payload.get("values") or {}

        # 原本にない列は黙って捨てず拒否する（IT03）。
        unknown = [column for column in values if column not in set(ledger["input_columns"])]
        if unknown:
            raise VentureValidationError(f"この台帳にない列です: {', '.join(sorted(unknown))}")

        current = self.repository.list_ledger_entries(actor.tenant_id, venture_id, ledger_key) or {
            "items": []
        }
        entry_id = payload.get("id")
        existing = next((item for item in current["items"] if item["id"] == entry_id), None)

        limit = ledger.get("row_limit")
        if existing is None and limit is not None and len(current["items"]) >= limit:
            # 原本33 K03 の予約行数。上限外は原本の改訂が要る（IT04）。
            raise VentureValidationError(
                f"この台帳の予約行は {limit} 行です。上限を超える記録は正本側で管理してください"
            )

        state_column = ledger.get("state_column", "")
        locked = set(ledger.get("locked_states", []))
        if existing is not None and locked and state_column:
            state = (existing["values"].get(state_column) or "").strip()
            if state in locked:
                # 原本15「承認後の上書きをせず新しい版を作る」（IT11）
                raise VentureValidationError(
                    f"{state} の行は上書きできません。版を上げて新しい行を起票してください"
                )

        self._validate_ledger_values(ledger, values)

        # 記録点検。その値だけで不正と決まるものは入口で拒否する。
        merged = {**(existing["values"] if existing else {}), **values}
        if payload.get("status"):
            merged.setdefault(ledger["id_column"], existing["rowKey"] if existing else "")
        row_key = existing["rowKey"] if existing else (payload.get("rowKey") or "").strip()
        merged[ledger["id_column"]] = row_key
        siblings = {
            item["rowKey"]: item["values"]
            for item in current["items"]
            if not existing or item["id"] != existing["id"]
        }
        # 何も書かれていない起票直後の行は「途中経過」なので点検で止めない。
        # 行IDの重複はリポジトリ側の一意制約が行IDつきのメッセージで返す。
        if any((merged.get(column) or "").strip() for column in ledger["input_columns"]):
            derived = evaluate(
                ledger_key,
                merged,
                self.repository.check_context(
                    actor.tenant_id, venture_id, ledger_key, row_key, siblings
                ),
            )
            refused = blocking(ledger_key, derived)
            if refused and not refused.endswith("重複"):
                raise VentureValidationError(refused)

        try:
            entry = self.repository.upsert_ledger_entry(
                actor.tenant_id, venture_id, ledger_key, payload, actor.user_id
            )
        except LedgerRowKeyConflictError as error:
            raise VentureValidationError(f"この行IDは既に使われています: {error.row_key}") from error
        if entry is None:
            raise VentureNotFoundError("台帳の行が見つかりません")
        return entry

    def _validate_ledger_values(self, ledger: dict, values: dict) -> None:
        """原本の入力規則（ドロップダウン・日付・数値）に従わせる。

        統制語彙が守られないと、「学習利用可否=禁止」のデータを機械的に
        抽出できなくなる。
        """
        rules = ledger.get("column_rules", {})
        for column, value in values.items():
            rule = rules.get(column)
            text = (value or "").strip()
            if not rule or not text:
                continue
            if rule["type"] == "select" and rule.get("options"):
                if text not in rule["options"]:
                    raise VentureValidationError(
                        f"{column} は {'、'.join(rule['options'])} のいずれかです"
                    )
            elif rule["type"] == "date":
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
                    raise VentureValidationError(f"{column} は YYYY-MM-DD で入力してください")
            elif rule["type"] == "number":
                try:
                    number = float(text)
                except ValueError:
                    raise VentureValidationError(f"{column} は数値で入力してください") from None
                minimum = rule.get("min")
                if minimum is not None and number < minimum:
                    raise VentureValidationError(f"{column} は {minimum:g} 以上で入力してください")

    def delete_ledger_entry(self, actor: UserContext, venture_id: str, ledger_key: str, entry_id: str) -> dict:
        self._assert(actor, EDITOR_ROLES)
        self._get_venture(actor, venture_id)
        result = self.repository.delete_ledger_entry(actor.tenant_id, venture_id, ledger_key, entry_id)
        if result == "not_found":
            raise VentureNotFoundError("台帳の行が見つかりません")
        if result == "master_row":
            raise VentureValidationError("この行は削除できません。点検行は状態で管理してください")
        return {"removed": True}

    # ── スキル ──────────────────────────────────────
    def skill_gap(self, actor: UserContext, venture_id: str) -> dict:
        self._assert(actor, VIEWER_ROLES)
        self._get_venture(actor, venture_id)
        result = self.repository.skill_gap(actor.tenant_id, venture_id)
        if not self._can_see_all_assessments(actor):
            # 充足の集計は全員に見せるが、個人別の到達Lvと育成計画は本人と評価者だけ。
            for item in result.get("items", []):
                item["assessments"] = [
                    assessment
                    for assessment in item.get("assessments", [])
                    if assessment.get("userId") == actor.user_id
                ]
        return result

    def upsert_skill_assessment(self, actor: UserContext, venture_id: str, payload: dict) -> dict:
        self._assert(actor, ASSESSOR_ROLES)
        self._get_venture(actor, venture_id)
        master = load_master()
        if payload.get("skillId") not in master.skill_by_id:
            raise VentureValidationError(f"未知のスキルです: {payload.get('skillId')}")
        level = payload.get("assessedLevel")
        if level is not None and not (0 <= int(level) <= 3):
            raise VentureValidationError("到達Lvは0〜3で入力してください")
        target_user_id = (payload.get("userId") or "").strip()
        if not target_user_id:
            raise VentureValidationError("評価する担当者を選択してください")
        # 原本 28 は「自己申告だけで配置しない」とし、評価者と対象者が同一なら
        # 第三者評価として認めない。
        if target_user_id == actor.user_id:
            raise VentureValidationError("自分の到達Lvは登録できません。第三者が評価してください")
        if not self.repository.is_member(actor.tenant_id, venture_id, target_user_id):
            raise VentureValidationError("案件の要員として登録されている人だけを評価できます")
        return self.repository.upsert_skill_assessment(actor.tenant_id, venture_id, payload, actor.user_id)

    # ── ダッシュボード ──────────────────────────────
    def summary(self, actor: UserContext, venture_id: str) -> dict:
        self._assert(actor, VIEWER_ROLES)
        self._get_venture(actor, venture_id)
        result = self.repository.summary(actor.tenant_id, venture_id)
        if result is None:
            raise VentureNotFoundError("案件が見つかりません")
        return result
