"""事業PJ台帳のアプリケーションサービス。

工程マスタは読み取り専用で全員が参照できる。案件台帳の更新は役割で制限する。
進捗担当、案件責任ロール、正本確認ロールを分けて制御する。
"""
from __future__ import annotations

import re
import math
from datetime import datetime, timezone
from infrastructure.venture_governance import (risk_fingerprint, VERIFICATION_FIELDS, PROTECTED_LEDGERS, CANCELLATION_FIELDS, record_is_final, task_checks)
from infrastructure.venture_rules import parse_timestamp
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
MANAGER_ROLES = VIEWER_ROLES
EDITOR_ROLES = VIEWER_ROLES

# テナント内の全案件を見られる役割。これ以外は要員として登録された案件だけ見える。
# 案件台帳にはデータ台帳の個人情報区分・保存場所や、要員のスキル評価・育成計画が
# 入るため、案件に関与していない利用者には見せない。
ALL_VENTURES_ROLES = {"admin"}


class VentureAccessError(PermissionError):
    """役割が操作を許可されていない。"""


class VentureNotFoundError(ValueError):
    """案件または台帳の行が見つからない。"""


class VentureValidationError(ValueError):
    """入力値がマスタの定義に合わない。"""

class VentureConflictError(VentureValidationError):
    """An editor submitted a stale revision."""


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

    def capabilities(self, actor: UserContext, venture_id: str) -> dict:
        members = self.repository.list_members(actor.tenant_id, venture_id)
        roles = {m["roleId"] for m in members if m["userId"] == actor.user_id and m.get("roleEffective", True)
            and (m["roleId"] != "R19" or (m.get("appointedBy") and m["appointedBy"] != actor.user_id))}
        if "R19" in roles and roles - {"R19"}:
            roles.remove("R19")
        result = {"canManage": actor.role == "admin" or bool(roles & {"R01", "R02", "R18"}),
                "canEdit": actor.role == "admin" or bool(roles),
                "canAssess": actor.role == "admin" or bool(roles & {"R02", "R19"}),
                "canVerify": bool(roles & {"R01", "R18", "R19"}), "roleIds": sorted(roles)}
        archived = (self.repository.get_venture(actor.tenant_id, venture_id) or {}).get("status") == "アーカイブ"
        result.update(archived=archived, canReopen=archived and result["canManage"], canViewAssessments=result["canAssess"])
        if archived:
            result.update(canManage=False, canEdit=False, canAssess=False, canVerify=False)
        return result

    def _assert_writable(self, venture: dict):
        if venture["status"] == "アーカイブ":
            raise VentureValidationError("アーカイブ済みの案件は閲覧専用です。理由を記録して再開してください")

    def _project_permission(self, actor: UserContext, venture_id: str, capability: str):
        self.repository.lock_venture(actor.tenant_id, venture_id)
        self._assert_writable(self._get_venture(actor, venture_id))
        if not self.capabilities(actor, venture_id).get(capability):
            raise VentureAccessError("案件の責任ロールにこの操作が割り当てられていません")

    def _require_role(self, actor: UserContext, venture_id: str, role_id: str):
        if role_id not in self.capabilities(actor, venture_id)["roleIds"]:
            raise VentureAccessError(f"正本確認には案件の {role_id} 割当が必要です")

    def _can_see_all_assessments(self, actor: UserContext, venture_id: str) -> bool:
        return self.capabilities(actor, venture_id)["canViewAssessments"]

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
        return {**self._get_venture(actor, venture_id), "capabilities": self.capabilities(actor, venture_id)}

    def create_venture(self, actor: UserContext, payload: dict) -> dict:
        self._assert(actor, {"admin", "recruiter"})
        self._validate_venture_payload(payload)
        if not (payload.get("name") or "").strip():
            raise VentureValidationError("事業・サービス名を入力してください")
        return self.repository.create_venture(actor.tenant_id, actor.user_id, payload)

    def update_venture(self, actor: UserContext, venture_id: str, payload: dict) -> dict:
        self._assert(actor, VIEWER_ROLES)
        self.repository.lock_venture(actor.tenant_id, venture_id)
        current = self._get_venture(actor, venture_id)
        if current["status"] == "アーカイブ":
            if not self.capabilities(actor, venture_id)["canReopen"]:
                raise VentureAccessError("案件の管理担当だけが再開できます")
            if set(payload) != {"status", "reopenReason"} or payload["status"] != "進行中" or not (payload["reopenReason"] or "").strip():
                raise VentureValidationError("再開理由を入力し、状態を進行中にしてください。その他の変更は再開後に行います")
            governance = dict(current.get("governance") or {})
            governance.update(reopenedAt=datetime.now(timezone.utc).isoformat(), reopenedBy=actor.user_id,
                reopenReason=payload["reopenReason"].strip(), riskConfirmed=False, riskState="再判定待ち")
            venture = self.repository.update_venture(actor.tenant_id, venture_id, {"status": "進行中", "governance": governance, "_actor": actor.user_id})
            return {**venture, "capabilities": self.capabilities(actor, venture_id)}
        if payload.get("confirmRisk") and set(payload) <= {"confirmRisk", "riskEvidenceUri"}:
            self._get_venture(actor, venture_id)
            self._require_role(actor, venture_id, "R19")
        else:
            self._project_permission(actor, venture_id, "canManage")
        current = self._get_venture(actor, venture_id)
        self._validate_venture_payload(payload)
        merged = {**current, **payload, "conditions": {**current["conditions"], **(payload.get("conditions") or {})}}
        governance = dict(current.get("governance") or {})
        if payload.get("status") == "アーカイブ":
            if set(payload) != {"status"}:
                raise VentureValidationError("アーカイブは他の変更と分けて行ってください")
            snapshot_id = self.repository.capture_archive(actor.tenant_id, venture_id, actor.user_id)
            governance.update(archivedAt=datetime.now(timezone.utc).isoformat(), archivedBy=actor.user_id, archiveSnapshotId=snapshot_id)
        if risk_fingerprint(merged) != risk_fingerprint(current):
            governance.update(riskConfirmed=False, riskState="再判定待ち" if governance.get("riskFingerprint") else "判定案")
        if payload.pop("confirmRisk", False):
            self._require_role(actor, venture_id, "R19")
            if merged.get("riskTier") in ("", "未判定") or not merged.get("riskTierRationale") or any(merged["conditions"].get(k) not in ("適用", "対象外") for k in ("RAG", "Agent")):
                raise VentureValidationError("Risk Tier・根拠・RAG/Agentの適用を確定してください")
            evidence = payload.pop("riskEvidenceUri", "")
            if not evidence:
                raise VentureValidationError("リスク判定の正本URIを入力してください")
            governance.update(riskConfirmed=True, riskState="確認済み", riskFingerprint=risk_fingerprint(merged),
                riskEvidenceUri=evidence, riskConfirmedBy=actor.user_id, riskConfirmedAt=datetime.now(timezone.utc).isoformat())
        payload["governance"] = governance
        payload["_actor"] = actor.user_id
        venture = self.repository.update_venture(actor.tenant_id, venture_id, payload)
        return {**venture, "capabilities": self.capabilities(actor, venture_id)}

    def delete_venture(self, actor: UserContext, venture_id: str) -> dict:
        self._assert(actor, VIEWER_ROLES)
        self._project_permission(actor, venture_id, "canManage")
        raise VentureValidationError("証拠保全のため完全削除できません。状態をアーカイブに変更してください")

    def _validate_venture_payload(self, payload: dict) -> None:
        master = load_master()
        if payload.get("scale") and payload["scale"] not in SCALE_VALUES:
            raise VentureValidationError(f"規模は {', '.join(SCALE_VALUES)} のいずれかです")
        if payload.get("status") and payload["status"] not in VENTURE_STATUS_VALUES:
            raise VentureValidationError(f"状態は {', '.join(VENTURE_STATUS_VALUES)} のいずれかです")
        tiers = {tier["tier_id"] for tier in master.risk_tiers} | {"未判定"}
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
        self.repository.lock_venture(actor.tenant_id, venture_id)
        self._assert_writable(self._get_venture(actor, venture_id))
        if payload.get("status") and payload["status"] not in TASK_STATUS_VALUES:
            raise VentureValidationError(f"状態は {', '.join(TASK_STATUS_VALUES)} のいずれかです")
        if payload.get("applicability") and payload["applicability"] not in APPLICABILITY_VALUES:
            raise VentureValidationError(f"適用判定は {', '.join(APPLICABILITY_VALUES)} のいずれかです")
        current = self.repository.get_task(actor.tenant_id, venture_id, task_row_id)
        if current is None:
            raise VentureNotFoundError("タスクが見つかりません")

        if not self.capabilities(actor, venture_id)["canManage"]:
            # 学習者・メンターは自分に割り当てられたタスクの進捗だけ更新できる。
            approver = current["approverRoleId"] in self.capabilities(actor, venture_id)["roleIds"]
            if current["assigneeUserId"] != actor.user_id and not (approver and set(payload) <= {"approveCompletion"}):
                raise VentureAccessError("自分が担当するタスクのみ更新できます")
            allowed_keys = {"status", "actualStart", "actualEnd", "actualHours", "evidenceUri", "blocker", "note"}
            if approver:
                allowed_keys.add("approveCompletion")
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
            rows = self.repository.list_tasks(actor.tenant_id, venture_id)
            graph = {r["taskId"]: r["dependsOn"] for r in rows}
            graph[current["taskId"]] = payload["dependsOn"]
            def walk(node, stack):
                if node in stack:
                    raise VentureValidationError("循環依存は登録できません")
                for child in graph.get(node, []):
                    walk(child, stack | {node})
            walk(current["taskId"], set())

        if payload.get("approveCompletion") is True:
            self._require_role(actor, venture_id, current["approverRoleId"])
            self._assert_completion_approvable(actor, current, payload)
            proposed = {**current, **payload, "completionApprovedBy": actor.user_id, "completionApprovedAt": datetime.now(timezone.utc).isoformat()}
            rows = self.repository.list_tasks(actor.tenant_id, venture_id)
            rows = [proposed if r["id"] == current["id"] else r for r in rows]
            checks = task_checks(rows, self.repository.list_members(actor.tenant_id, venture_id), as_of(self._get_venture(actor, venture_id))[0], self.repository._ledger_values(actor.tenant_id, venture_id, "gate_run"))
            if not checks[current["taskId"]]["completionValid"]:
                raise VentureValidationError(checks[current["taskId"]]["completionCheck"])

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
        self._project_permission(actor, venture_id, "canManage")
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
        self._assert(actor, VIEWER_ROLES)
        self._get_venture(actor, venture_id)
        raise VentureValidationError("承認はGateRun台帳へ統一しました。ゲート承認記録から新しい判断を作成してください")

    # ── 要員 ────────────────────────────────────────
    def list_members(self, actor: UserContext, venture_id: str) -> dict:
        self._assert(actor, VIEWER_ROLES)
        self._get_venture(actor, venture_id)
        return {"items": self.repository.list_members(actor.tenant_id, venture_id)}

    def add_member(self, actor: UserContext, venture_id: str, payload: dict) -> dict:
        self._assert(actor, MANAGER_ROLES)
        self._project_permission(actor, venture_id, "canManage")
        master = load_master()
        role_id = payload.get("roleId", "")
        if role_id not in master.role_by_id:
            raise VentureValidationError(f"未知のロールです: {role_id}")
        user_id = (payload.get("userId") or "").strip()
        if not user_id:
            raise VentureValidationError("担当者を選択してください")
        from infrastructure.sql_models import UserModel
        user = self.repository._db.get(UserModel, user_id)
        if not user or user.tenant_id != actor.tenant_id or user.state != "active":
            raise VentureValidationError("所属する有効な利用者だけを配属できます")
        if role_id == "R19" and (actor.role != "admin" or user_id == actor.user_id):
            raise VentureAccessError("独立確認者は別のテナント管理者が任命してください")
        roles = {m["roleId"] for m in self.repository.list_members(actor.tenant_id, venture_id) if m["userId"] == user_id}
        if (role_id == "R19" and roles - {"R19"}) or (role_id != "R19" and "R19" in roles):
            raise VentureAccessError("独立確認者は案件の実施・管理ロールを兼務できません")
        return self.repository.add_member(
            actor.tenant_id, venture_id, user_id, role_id, payload.get("allocationNote", ""), actor.user_id
        )

    def remove_member(self, actor: UserContext, venture_id: str, member_id: str) -> dict:
        self._assert(actor, MANAGER_ROLES)
        self._project_permission(actor, venture_id, "canManage")
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
        self._project_permission(actor, venture_id, "canEdit")
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

        if existing and payload.get("expectedRevision") != existing["revision"]:
            raise VentureConflictError("別の利用者が更新しました。下書きを保持して最新の内容と比較してください")

        if any(key in values for key in VERIFICATION_FIELDS):
            raise VentureAccessError("正本確認情報は確認操作でのみ記録できます")
        if existing and record_is_final(ledger_key, existing["values"]):
            changed = {k for k, v in values.items() if v != existing["values"].get(k, "")}
            if changed - CANCELLATION_FIELDS:
                raise VentureValidationError("確定済みの行は上書きできません。新しい版・Runを作成してください")
            if any(not values[k] or existing["values"].get(k) for k in changed & CANCELLATION_FIELDS):
                raise VentureValidationError("取消履歴は消去・変更できません")
        cancellation_added = any(values.get(k) and values.get(k) != (existing or {}).get("values", {}).get(k) for k in CANCELLATION_FIELDS)
        if ledger_key in PROTECTED_LEDGERS and (payload.get("verifyRecord") or cancellation_added):
            merged_for_role = {**(existing["values"] if existing else {}), **values}
            required_role = "R19"
            if ledger_key == "gate_run":
                required_role = load_master().gate_by_id.get(merged_for_role.get("Gate"), {}).get("approver_role_id", "R01")
            self._require_role(actor, venture_id, required_role)
        if payload.get("verifyRecord"):
            if existing and existing["values"].get("正本確認日時"):
                raise VentureValidationError("確認済みの記録は再確認で上書きできません。新しい版・Runを作成してください")
            if ledger_key not in PROTECTED_LEDGERS:
                raise VentureValidationError("この台帳は正本確認操作の対象ではありません")
            if ledger_key == "gate_run" and not ({**(existing["values"] if existing else {}), **values}).get("正本決裁URI"):
                raise VentureValidationError("正本決裁URIを入力してください")
            venture = self._get_venture(actor, venture_id)
            values = {**values, "正本確認者PersonID": actor.user_id, "正本確認日時": datetime.now(timezone.utc).isoformat(),
                      "前提版": (venture.get("governance") or {}).get("riskFingerprint", "")}
            payload["values"] = values

        self._validate_ledger_values(ledger, values)

        # 記録点検。その値だけで不正と決まるものは入口で拒否する。
        merged = {**(existing["values"] if existing else {}), **values}
        if ledger_key == "condition":
            self._validate_condition(actor, venture_id, merged, values, payload, existing)
        if payload.get("status"):
            merged.setdefault(ledger["id_column"], existing["rowKey"] if existing else "")
        row_key = existing["rowKey"] if existing else (payload.get("rowKey") or "").strip()
        if ledger_key == "eval_plan":
            if existing and existing["isMasterRow"]:
                merged.setdefault("EvalType", row_key)
            if not merged.get("EvalType") and values:
                raise VentureValidationError("EvalTypeを選択してください")
        else:
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
                if parse_date(text) is None or "T" in text:
                    raise VentureValidationError(f"{column} は YYYY-MM-DD で入力してください")
            elif rule["type"] == "datetime":
                if parse_timestamp(text) is None:
                    raise VentureValidationError(f"{column} は時差付き日時（例: 2026-09-11T09:00:00+09:00）で入力してください")
            elif rule["type"] == "number":
                try:
                    number = float(text)
                except ValueError:
                    raise VentureValidationError(f"{column} は数値で入力してください") from None
                if not math.isfinite(number):
                    raise VentureValidationError(f"{column} は有限の数値で入力してください")
                minimum = rule.get("min")
                if minimum is not None and number < minimum:
                    raise VentureValidationError(f"{column} は {minimum:g} 以上で入力してください")

    def _validate_condition(self, actor, venture_id, merged, values, payload, existing):
        gates = self.repository._ledger_values(actor.tenant_id, venture_id, "gate_run")
        if merged.get("GateRun ID") and merged["GateRun ID"] not in gates:
            raise VentureValidationError("実在するGateRunを指定してください")
        if existing:
            original_gate = gates.get(existing["values"].get("GateRun ID"), {})
            if record_is_final("gate_run", original_gate) and not payload.get("verifyRecord"):
                raise VentureValidationError("決裁後の条件は変更できません。独立した解消確認、または新しい条件・決裁を記録してください")
        members = {m["userId"] for m in self.repository.list_members(actor.tenant_id, venture_id)}
        if merged.get("Owner PersonID") and merged["Owner PersonID"] not in members:
            raise VentureValidationError("条件Ownerは案件の有効な要員を指定してください")
        if any(k in values for k in ("確認者PersonID", "確認日")):
            raise VentureAccessError("条件の確認者・確認日は確認操作で記録します")
        if existing and existing["values"].get("正本確認日時"):
            raise VentureValidationError("解消確認後は変更できません。新しい条件を作成してください")
        if merged.get("状態") == "解消":
            if not payload.get("verifyRecord"):
                raise VentureAccessError("解消は独立確認操作が必要です")
            if actor.user_id == merged.get("Owner PersonID"):
                raise VentureAccessError("条件Ownerは自身の条件を解消確認できません")
            resolved = parse_date(merged.get("解消日"))
            basis = min(as_of(self._get_venture(actor, venture_id))[0], datetime.now(timezone.utc).date())
            if not resolved or resolved > basis or not merged.get("解消証拠URI"):
                raise VentureValidationError("未来でない解消日と解消証拠URIを記録してください")
            server_values = {"確認者PersonID": actor.user_id, "確認日": datetime.now(timezone.utc).date().isoformat()}
            merged.update(server_values)
            payload["values"].update(server_values)

    def delete_ledger_entry(self, actor: UserContext, venture_id: str, ledger_key: str, entry_id: str) -> dict:
        self._assert(actor, EDITOR_ROLES)
        self._project_permission(actor, venture_id, "canEdit")
        result = self.repository.delete_ledger_entry(actor.tenant_id, venture_id, ledger_key, entry_id)
        if result == "not_found":
            raise VentureNotFoundError("台帳の行が見つかりません")
        if result in ("master_row", "protected"):
            raise VentureValidationError("証拠保全のため削除できません。取消・置換を記録してください")
        return {"removed": True}

    # ── スキル ──────────────────────────────────────
    def skill_gap(self, actor: UserContext, venture_id: str) -> dict:
        self._assert(actor, VIEWER_ROLES)
        self._get_venture(actor, venture_id)
        result = self.repository.skill_gap(actor.tenant_id, venture_id)
        if not self._can_see_all_assessments(actor, venture_id):
            # 充足の集計は全員に見せるが、個人別の到達Lvと育成計画は本人と評価者だけ。
            for item in result.get("items", []):
                item["assessments"] = [
                    assessment
                    for assessment in item.get("assessments", [])
                    if assessment.get("userId") == actor.user_id
                ]
        return result

    def upsert_skill_assessment(self, actor: UserContext, venture_id: str, payload: dict) -> dict:
        self._assert(actor, VIEWER_ROLES)
        self._get_venture(actor, venture_id)
        self._project_permission(actor, venture_id, "canAssess")
        if payload.get("revoked") and not (payload.get("developmentPlan") or "").strip():
            raise VentureValidationError("評価を取り消す理由を入力してください")
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
        result["venture"]["capabilities"] = self.capabilities(actor, venture_id)
        if not self._can_see_all_assessments(actor, venture_id):
            for item in result.get("topSkillGaps", []):
                item["assessments"] = [a for a in item.get("assessments", []) if a.get("userId") == actor.user_id]
        return result
