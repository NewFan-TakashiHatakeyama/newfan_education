"""事業PJ台帳の永続化。

工程マスタ（venture_process_master.json）は読み取り専用の標準定義。
案件を作ると、その時点のマスタから 132 タスク・6 ゲート・台帳の点検行を
インスタンス化して台帳を持たせる。
"""
from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import replace
import json
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from infrastructure.sql_models import (
    AuditLogModel,
    UserModel,
    VentureGateModel,
    VentureLedgerEntryModel,
    VentureMemberModel,
    VentureModel,
    VentureSkillAssessmentModel,
    VentureTaskModel,
)
from infrastructure.course_seed import default_courses
from infrastructure.skill_course_map import courses_for_skill
from infrastructure.venture_ledger_checks import CHECK_COLUMNS, CheckContext, evaluate, plan_key
from infrastructure.venture_rules import as_of, parse_date
from infrastructure.venture_governance import task_checks, risk_fingerprint, check_statuses
from infrastructure.venture_master import (
    APPLICABILITY_APPLIED,
    APPLICABILITY_EXCLUDED,
    APPLICABILITY_UNDECIDED,
    load_master,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.isoformat()


def _dependencies(model: VentureTaskModel, task: dict) -> list[str]:
    """案件の実効依存。上書きが無ければ標準依存（原本02の基本依存ID）。"""
    override = (model.depends_on_override or "").strip()
    if not override:
        if model.dependency_change_approved_by and model.dependency_change_reason:
            return []
        return task.get("depends_on", [])
    return [part.strip() for part in override.split(",")]


def _dependency_check(model: VentureTaskModel, task: dict) -> str:
    """原本17!BC 依存記法点検と、W の依存変更承認不足。"""
    override = (model.depends_on_override or "").strip()
    if not override:
        if model.dependency_change_approved_by and model.dependency_change_reason:
            return "依存なし"
        return "標準依存"
    parts = override.split(",")
    if any(not part.strip() or part != part.strip() for part in parts):
        # 『,』『B0-01,』『,B0-01』『B0-01,,B0-02』を通さない
        return "依存記法不正"
    if len(parts) > 8:
        return "依存8件超過"
    known = set(load_master().task_by_id)
    if any(part not in known for part in parts) or model.task_id in parts:
        return "依存ID不正"
    if sorted(parts) == sorted(task.get("depends_on", [])):
        return "標準依存"
    if (
        not (model.dependency_change_reason or "").strip()
        or not model.dependency_change_approved_by
        or model.dependency_change_approved_at is None
    ):
        return "依存変更承認不足"
    return "記法OK"


class LedgerRowKeyConflictError(Exception):
    """同じ行IDが台帳に既にある。"""

    def __init__(self, row_key: str) -> None:
        super().__init__(row_key)
        self.row_key = row_key


class PostgresVentureRepository:
    """案件台帳の読み書き。マスタ参照は `load_master()` を通す。"""

    def __init__(self, db: Session) -> None:
        self._db = db

    def lock_venture(self, tenant_id: str, venture_id: str) -> None:
        """Serialize validation and mutation so an approval cannot race a core edit."""
        connection = self._db.connection()
        if connection.dialect.name == "sqlite" and not connection.connection.driver_connection.in_transaction:
            connection.exec_driver_sql("BEGIN IMMEDIATE")
        self._db.execute(select(VentureModel.id).where(
            VentureModel.id == venture_id, VentureModel.tenant_id == tenant_id).with_for_update()).first()
        self._db.expire_all()

    def _commit(self) -> None:
        """コミットに失敗したら必ずロールバックしてからそのまま投げる。

        ロールバックを省くとSessionが壊れたまま残り、以後の操作が
        PendingRollbackError で連鎖的に失敗する。
        """
        try:
            self._db.commit()
        except SQLAlchemyError:
            self._db.rollback()
            raise

    def _write_audit(
        self,
        *,
        tenant_id: str,
        event_type: str,
        resource_type: str,
        resource_id: str,
        action: str,
        actor_user_id: str,
        actor_role: str,
        summary: str,
        metadata: dict | None = None,
    ) -> None:
        """判断の記録を追記専用で残す。

        案件台帳の行は最新値しか持たないため、承認を取り消すと誰がいつ承認したかが
        行からは消える。原本 29_ゲート承認記録 は判断を追記で残す設計なので、
        少なくとも監査ログには痕跡を残す。
        """
        self._db.add(
            AuditLogModel(
                id=f"al-{uuid4().hex[:16]}",
                tenant_id=tenant_id,
                event_type=event_type,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                summary=summary,
                metadata_json={key: str(value) for key, value in (metadata or {}).items()},
            )
        )

    def is_member(self, tenant_id: str, venture_id: str, user_id: str) -> bool:
        """その利用者が案件の要員として登録されているか。"""
        found = self._db.execute(
            select(VentureMemberModel.id).where(
                VentureMemberModel.tenant_id == tenant_id,
                VentureMemberModel.venture_id == venture_id,
                VentureMemberModel.user_id == user_id,
            )
        ).first()
        return found is not None

    def member_venture_ids(self, tenant_id: str, user_id: str) -> set[str]:
        """その利用者が要員として登録されている案件のID。"""
        rows = self._db.execute(
            select(VentureMemberModel.venture_id).where(
                VentureMemberModel.tenant_id == tenant_id,
                VentureMemberModel.user_id == user_id,
            )
        ).scalars()
        return set(rows)

    # ─────────────────────────────────────────────
    # マスタ
    # ─────────────────────────────────────────────
    def master_overview(self) -> dict:
        master = load_master()
        return {
            "version": master.version,
            "phases": [
                {
                    "phaseId": p["phase_id"],
                    "name": p["name"],
                    "purpose": p["purpose"],
                    "precondition": p["precondition"],
                    "gateId": p["gate_id"],
                    "approverRoleId": p["approver_role_id"],
                    "requiredEvidence": p["required_evidence"],
                    "decision": p["decision"],
                    "taskCount": sum(1 for t in master.tasks if t["phase_id"] == p["phase_id"]),
                }
                for p in master.phases
            ],
            "gates": [
                {
                    "gateId": g["gate_id"],
                    "subject": g["subject"],
                    "standardTaskId": g["standard_task_id"],
                    "approverRoleId": g["approver_role_id"],
                    "requiredEvidence": g["required_evidence"],
                    "allowedDecisions": g["allowed_decisions"],
                }
                for g in master.gates
            ],
            "riskTiers": [
                {
                    "tierId": t["tier_id"],
                    "name": t["name"],
                    "impact": t["impact"],
                    "rigor": t["rigor"],
                    "caution": t["caution"],
                }
                for t in master.risk_tiers
            ],
            "roles": [
                {
                    "roleId": r["role_id"],
                    "name": r["name"],
                    "responsibility": r["responsibility"],
                    "involvement": r["involvement"],
                    "independenceNote": r["independence_note"],
                }
                for r in master.roles
            ],
            "conditionKeys": master.condition_keys,
            "ledgers": [
                {
                    "key": l["key"],
                    "name": l["name"],
                    "summary": l["summary"],
                    "sourceSheet": l["source_sheet"],
                    "idColumn": l["id_column"],
                    "seeded": l["seeded"],
                    "masterColumns": l["master_columns"],
                    "inputColumns": l["input_columns"],
                    "notes": l["notes"],
                    "columnRules": l.get("column_rules", {}),
                    "derivedColumns": l.get("derived_columns", []),
                    "rowLimit": l.get("row_limit"),
                    "stateColumn": l.get("state_column", ""),
                    "lockedStates": l.get("locked_states", []),
                    "checkColumns": CHECK_COLUMNS.get(l["key"], []),
                    "masterRowCount": len(l["rows"]),
                }
                for l in master.ledgers
            ],
            "taskCount": len(master.tasks),
            "skillCount": len(master.skills),
        }

    def master_standards(self) -> dict:
        """工程の標準。案件を作らなくても読める参照情報。

        原本 03 のTier別強度、04 のテーラリング原則と参考工数、14 のハーネス標準・
        標準開発ループ・実行設定・負の試験、24 の調査ソース、32 の評価分類。
        """
        master = load_master()
        return {
            "version": master.version,
            "tailoring": [
                {
                    "aspect": item["aspect"],
                    "approach": item["approach"],
                    "operation": item["operation"],
                    "caution": item["caution"],
                }
                for item in master.tailoring
            ],
            "scales": {
                key: [
                    {
                        "aspect": item["aspect"],
                        "approach": item["approach"],
                        "operation": item["operation"],
                        "caution": item["caution"],
                    }
                    for item in items
                ]
                for key, items in master.scales.items()
            },
            "effortReference": [
                {
                    "phase": item["phase"],
                    "sMin": item["s_min"],
                    "sMax": item["s_max"],
                    "mMin": item["m_min"],
                    "mMax": item["m_max"],
                    "lMin": item["l_min"],
                    "lMax": item["l_max"],
                    "unit": item["unit"],
                }
                for item in master.effort_reference
            ],
            "evalTypes": [
                {
                    "evalTypeId": item["eval_type_id"],
                    "axis": item["axis"],
                    "metrics": item["metrics"],
                    "designNote": item["design_note"],
                    "applicability": item["applicability"],
                }
                for item in master.eval_types
            ],
            "harness": [
                {
                    "controlId": item["control_id"],
                    "target": item["target"],
                    "standard": item["standard"],
                    "detail": item["detail"],
                    "ownerRoleId": item["owner_role_id"],
                    "evidence": item["evidence"],
                    "relatedTaskIds": item["related_task_ids"],
                }
                for item in master.harness
            ],
            "harnessTests": [
                {
                    "testId": item["test_id"],
                    "appliesWhen": item["applies_when"],
                    "theme": item["theme"],
                    "specification": item["specification"],
                    "ownerRoleId": item["owner_role_id"],
                    "evidence": item["evidence"],
                    "relatedTaskIds": item["related_task_ids"],
                    "note": item["note"],
                }
                for item in master.harness_tests
            ],
            "devLoop": [
                {
                    "step": item["step"],
                    "name": item["name"],
                    "input": item["input"],
                    "aiRole": item["ai_role"],
                    "humanRole": item["human_role"],
                    "stopCondition": item["stop_condition"],
                }
                for item in master.dev_loop
            ],
            "runtimeSettings": [
                {"name": item["name"], "check": item["check"]} for item in master.runtime_settings
            ],
            "investmentDecisions": [
                {
                    "decision": item["decision"],
                    "condition": item["condition"],
                    "caution": item["caution"],
                }
                for item in master.investment_decisions
            ],
            "sources": [
                {
                    "sourceId": item["source_id"],
                    "published": item["published"],
                    "organization": item["organization"],
                    "title": item["title"],
                    "evidenceType": item["evidence_type"],
                    "adopted": item["adopted"],
                    "limitation": item["limitation"],
                    "appliedTo": item["applied_to"],
                    "url": item["url"],
                    "checkedOn": item["checked_on"],
                }
                for item in master.sources
            ],
        }

    # ─────────────────────────────────────────────
    # 案件
    # ─────────────────────────────────────────────
    def _venture_row(self, model: VentureModel, counts: dict | None = None) -> dict:
        value = {
            "id": model.id,
            "name": model.name,
            "summary": model.summary,
            "offeringType": model.offering_type,
            "industry": model.industry,
            "serviceCountries": model.service_countries,
            "processingCountries": model.processing_countries,
            "scale": model.scale,
            "riskTier": model.risk_tier,
            "riskTierRationale": model.risk_tier_rationale,
            "governance": model.governance or {},
            "status": model.status,
            "currentPhaseId": model.current_phase_id,
            "businessOwnerUserId": model.business_owner_user_id,
            "conditions": dict(model.conditions or {}),
            "asOfDate": model.as_of_date or "",
            "asOfDateSource": as_of({"asOfDate": model.as_of_date or ""})[1],
            "createdBy": model.created_by,
            "createdAt": _iso(model.created_at),
            "updatedAt": _iso(model.updated_at),
        }
        if counts:
            value.update(counts)
        return value

    def list_ventures(self, tenant_id: str) -> list[dict]:
        models = (
            self._db.execute(
                select(VentureModel).where(VentureModel.tenant_id == tenant_id).order_by(VentureModel.created_at.desc())
            )
            .scalars()
            .all()
        )
        result = []
        for model in models:
            result.append(self._venture_row(model, self._progress_counts(model.id)))
        return result

    def get_venture(self, tenant_id: str, venture_id: str) -> dict | None:
        model = self._db.get(VentureModel, venture_id)
        if model is None or model.tenant_id != tenant_id:
            return None
        return self._venture_row(model, self._progress_counts(venture_id))

    def _progress_counts(self, venture_id: str) -> dict:
        venture = self._db.get(VentureModel, venture_id)
        rows = self.list_tasks(venture.tenant_id, venture_id) if venture else []
        applied = [r for r in rows if r["applicability"] == APPLICABILITY_APPLIED]
        return {"taskTotal": len(rows), "taskApplied": len(applied),
                "taskUndecided": sum(r["applicability"] == APPLICABILITY_UNDECIDED for r in rows),
                "taskCompleted": sum(r["completionValid"] for r in applied)}

    def create_venture(self, tenant_id: str, created_by: str, payload: dict) -> dict:
        master = load_master()
        venture_id = f"venture-{uuid4().hex[:10]}"
        conditions = master.default_conditions()
        conditions.update(payload.get("conditions") or {})
        model = VentureModel(
            id=venture_id,
            tenant_id=tenant_id,
            name=payload["name"],
            summary=payload.get("summary", ""),
            offering_type=payload.get("offeringType", "社内事業"),
            industry=payload.get("industry", ""),
            service_countries=payload.get("serviceCountries", ""),
            processing_countries=payload.get("processingCountries", ""),
            scale=payload.get("scale", "S"),
            risk_tier=payload.get("riskTier", "未判定"),
            risk_tier_rationale=payload.get("riskTierRationale", ""),
            governance={"riskConfirmed": False, "riskState": "未判定" if payload.get("riskTier", "未判定") == "未判定" else "判定案", "riskLedgerRevision": 0},
            status=payload.get("status", "計画中"),
            current_phase_id=payload.get("currentPhaseId", "B0"),
            business_owner_user_id=payload.get("businessOwnerUserId"),
            conditions=conditions,
            as_of_date=payload.get("asOfDate", "") or "",
            created_by=created_by,
        )
        self._db.add(model)

        # There are no ORM relationships ordering these inserts. Persist the parent
        # inside this transaction before adding rows with a venture_id foreign key.
        self._db.flush([model])

        # 工程タスク 132 件を展開する
        self._db.add(VentureMemberModel(id=f"vm-{uuid4().hex[:12]}", venture_id=venture_id,
            tenant_id=tenant_id, user_id=created_by, role_id="R02", allocation_note="案件作成時の管理担当"))
        for task in master.tasks:
            self._db.add(
                VentureTaskModel(
                    id=f"vt-{uuid4().hex[:12]}",
                    venture_id=venture_id,
                    tenant_id=tenant_id,
                    task_id=task["task_id"],
                    phase_id=task["phase_id"],
                    gate_id=task.get("gate_id", ""),
                    applicability=master.suggest_applicability(task["task_id"], conditions),
                    role_id=(task.get("exec_role_ids") or [""])[0],
                )
            )

        # ゲート 6 件
        for gate in master.gates:
            self._db.add(
                VentureGateModel(
                    id=f"vg-{uuid4().hex[:12]}",
                    venture_id=venture_id,
                    tenant_id=tenant_id,
                    gate_id=gate["gate_id"],
                )
            )

        # 点検行を持つ台帳を展開する
        for ledger in master.ledgers:
            if not ledger["seeded"]:
                continue
            for row in ledger["rows"]:
                row_key = row.get(ledger["id_column"], "")
                if not row_key:
                    continue
                self._db.add(
                    VentureLedgerEntryModel(
                        id=f"vl-{uuid4().hex[:12]}",
                        venture_id=venture_id,
                        tenant_id=tenant_id,
                        ledger_key=ledger["key"],
                        row_key=row_key,
                        is_master_row=True,
                        status="未着手",
                        values_json={},
                    )
                )

        self._commit()
        return self.get_venture(tenant_id, venture_id) or {}

    def update_venture(self, tenant_id: str, venture_id: str, payload: dict) -> dict | None:
        model = self._db.get(VentureModel, venture_id)
        if model is None or model.tenant_id != tenant_id:
            return None
        before = self._venture_row(model)
        field_map = {
            "name": "name",
            "summary": "summary",
            "offeringType": "offering_type",
            "industry": "industry",
            "serviceCountries": "service_countries",
            "processingCountries": "processing_countries",
            "scale": "scale",
            "riskTier": "risk_tier",
            "riskTierRationale": "risk_tier_rationale",
            "status": "status",
            "currentPhaseId": "current_phase_id",
            "businessOwnerUserId": "business_owner_user_id",
            "asOfDate": "as_of_date",
            "governance": "governance",
        }
        for key, attribute in field_map.items():
            if key in payload and payload[key] is not None:
                setattr(model, attribute, payload[key])

        if payload.get("conditions") is not None:
            master = load_master()
            conditions = dict(model.conditions or {})
            conditions.update(payload["conditions"])
            model.conditions = conditions
            # 条件を変えたら、まだ人が判定していないタスクの提案だけを更新する。
            # 人が決めた適用判定は上書きしない。
            tasks = (
                self._db.execute(
                    select(VentureTaskModel).where(
                        VentureTaskModel.venture_id == venture_id,
                        VentureTaskModel.applicability_decided_by.is_(None),
                    )
                )
                .scalars()
                .all()
            )
            for task in tasks:
                task.applicability = master.suggest_applicability(task.task_id, conditions)

        self._write_audit(tenant_id=tenant_id, event_type="venture.context.change", resource_type="venture",
            resource_id=venture_id, action="update", actor_user_id=payload.get("_actor", ""), actor_role="",
            summary="案件前提・確認状態の更新", metadata={"before": json.dumps(before, ensure_ascii=False), "after": json.dumps(self._venture_row(model), ensure_ascii=False)})
        self._commit()
        return self.get_venture(tenant_id, venture_id)

    def delete_venture(self, tenant_id: str, venture_id: str, actor_user_id: str, actor_role: str) -> bool:
        return False  # Historical evidence is retained. Archive through update_venture.

    # ─────────────────────────────────────────────
    # 工程タスク台帳
    # ─────────────────────────────────────────────
    def _task_row(self, model: VentureTaskModel, master, user_names: dict[str, str]) -> dict:
        task = master.task_by_id.get(model.task_id, {})
        evidence = master.evidence_by_task_id.get(model.task_id, {})
        return {
            "id": model.id,
            "ventureId": model.venture_id,
            "taskId": model.task_id,
            "phaseId": model.phase_id,
            "phaseName": task.get("phase_name", ""),
            "workType": task.get("work_type", ""),
            "name": task.get("name", model.task_id),
            "description": task.get("description", ""),
            "deliverables": task.get("deliverables", ""),
            "completionCriteria": task.get("completion_criteria", ""),
            "aiBoundary": task.get("ai_boundary", ""),
            # 原本の根拠ID・確認用URL。どの一次資料に依るタスクかを辿れるようにする。
            "sourceIds": task.get("source_ids", []),
            "referenceUrls": task.get("reference_urls", []),
            "legacyTaskIds": task.get("legacy_task_ids", []),
            "applicabilityCondition": task.get("applicability", ""),
            "execRoleIds": task.get("exec_role_ids", []),
            "approverRoleId": task.get("approver_role_id", ""),
            "dependsOn": _dependencies(model, task),
            "standardDependsOn": task.get("depends_on", []),
            "dependencyChangeReason": model.dependency_change_reason or "",
            "dependencyChangeApprovedBy": model.dependency_change_approved_by,
            "dependencyChangeApprovedAt": _iso(model.dependency_change_approved_at),
            "dependencyCheck": _dependency_check(model, task),
            "skillIds": task.get("skill_ids", []),
            "gateId": model.gate_id,
            "evidenceId": evidence.get("evidence_id", ""),
            "recommendedSource": evidence.get("recommended_source", ""),
            "minimumEvidence": evidence.get("minimum_content", ""),
            "applicability": model.applicability,
            "applicabilityReason": model.applicability_reason,
            "applicabilityDecidedBy": model.applicability_decided_by,
            "applicabilityDecidedByName": user_names.get(model.applicability_decided_by or "", ""),
            "applicabilityDecidedAt": _iso(model.applicability_decided_at),
            "status": model.status,
            "assigneeUserId": model.assignee_user_id,
            "assigneeName": user_names.get(model.assignee_user_id or "", ""),
            "roleId": model.role_id,
            "plannedStart": model.planned_start,
            "plannedEnd": model.planned_end,
            "actualStart": model.actual_start,
            "actualEnd": model.actual_end,
            "plannedHours": model.planned_hours,
            "actualHours": model.actual_hours,
            "evidenceUri": model.evidence_uri,
            "completionApprovedBy": model.completion_approved_by,
            "completionApprovedByName": user_names.get(model.completion_approved_by or "", ""),
            "completionApprovedAt": _iso(model.completion_approved_at),
            "blocker": model.blocker,
            "note": model.note,
            "updatedAt": _iso(model.updated_at),
        }

    def _user_names(self, tenant_id: str) -> dict[str, str]:
        users = (
            self._db.execute(select(UserModel).where(UserModel.tenant_id == tenant_id)).scalars().all()
        )
        return {user.user_id: user.display_name for user in users}

    def list_tasks(
        self,
        tenant_id: str,
        venture_id: str,
        phase_id: str | None = None,
        applicability: str | None = None,
        status: str | None = None,
        assignee_user_id: str | None = None,
    ) -> list[dict]:
        query = select(VentureTaskModel).where(
            VentureTaskModel.tenant_id == tenant_id, VentureTaskModel.venture_id == venture_id
        )
        models = self._db.execute(query).scalars().all()
        master = load_master()
        names = self._user_names(tenant_id)
        rows = [self._task_row(model, master, names) for model in models]
        venture = self._db.get(VentureModel, venture_id)
        checked = task_checks(rows, self.list_members(tenant_id, venture_id),
                              as_of({"asOfDate": venture.as_of_date})[0],
                              self._ledger_values(tenant_id, venture_id, "gate_run"))
        for row in rows:
            row.update(checked[row["taskId"]])
        rows = [r for r in rows if (not phase_id or r["phaseId"] == phase_id)
                and (not applicability or r["applicability"] == applicability)
                and (not status or r["status"] == status)
                and (not assignee_user_id or r["assigneeUserId"] == assignee_user_id)]
        return sorted(rows, key=lambda row: row["taskId"])

    def get_task(self, tenant_id: str, venture_id: str, task_row_id: str) -> dict | None:
        return next((r for r in self.list_tasks(tenant_id, venture_id) if r["id"] == task_row_id), None)

    def update_task(
        self,
        tenant_id: str,
        venture_id: str,
        task_row_id: str,
        payload: dict,
        actor_user_id: str,
        actor_role: str = "",
    ) -> dict | None:
        model = self._db.get(VentureTaskModel, task_row_id)
        if model is None or model.tenant_id != tenant_id or model.venture_id != venture_id:
            return None

        before = self._task_row(model, load_master(), self._user_names(tenant_id))
        important = {"status", "evidenceUri", "assigneeUserId", "roleId", "actualStart", "actualEnd", "dependsOn", "applicability", "applicabilityReason"}
        if any(key in payload and payload[key] != before.get(key) for key in important):
            model.completion_approved_by = None
            model.completion_approved_at = None
        if "applicability" in payload and payload["applicability"]:
            model.applicability = payload["applicability"]
            model.applicability_decided_by = actor_user_id
            model.applicability_decided_at = _now()
        if "applicabilityReason" in payload and payload["applicabilityReason"] is not None:
            model.applicability_reason = payload["applicabilityReason"]

        simple = {
            "status": "status",
            "roleId": "role_id",
            "plannedStart": "planned_start",
            "plannedEnd": "planned_end",
            "actualStart": "actual_start",
            "actualEnd": "actual_end",
            "evidenceUri": "evidence_uri",
            "blocker": "blocker",
            "note": "note",
        }
        for key, attribute in simple.items():
            if key in payload and payload[key] is not None:
                setattr(model, attribute, payload[key])
        for key, attribute in (("plannedHours", "planned_hours"), ("actualHours", "actual_hours")):
            if key in payload:
                setattr(model, attribute, payload[key])
        if "assigneeUserId" in payload:
            model.assignee_user_id = payload["assigneeUserId"] or None
        if "dependsOn" in payload and payload["dependsOn"] is not None:
            model.depends_on_override = ",".join(payload["dependsOn"])
            model.dependency_change_reason = payload.get("dependencyChangeReason", "") or ""
            model.dependency_change_approved_by = actor_user_id
            model.dependency_change_approved_at = _now()

        # 完了承認は明示的な操作としてのみ記録する
        if payload.get("approveCompletion") is not None:
            previous_by = model.completion_approved_by
            previous_at = _iso(model.completion_approved_at)
            approved = payload["approveCompletion"] is True
            if approved:
                model.completion_approved_by = actor_user_id
                model.completion_approved_at = _now()
            else:
                model.completion_approved_by = None
                model.completion_approved_at = None
            # 承認の取り消しは行から痕跡が消えるので、監査ログに追記する。
            self._write_audit(
                tenant_id=tenant_id,
                event_type="venture.task.completion",
                resource_type="venture_task",
                resource_id=task_row_id,
                action="approve" if approved else "revoke",
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                summary=f"{model.task_id} の完了承認を{'記録' if approved else '取り消し'}",
                metadata={
                    "ventureId": venture_id,
                    "taskId": model.task_id,
                    "previousApprovedBy": previous_by or "",
                    "previousApprovedAt": previous_at or "",
                    "evidenceUri": model.evidence_uri or "",
                },
            )

        self._write_audit(tenant_id=tenant_id, event_type="venture.task.change", resource_type="venture_task",
            resource_id=task_row_id, action="update", actor_user_id=actor_user_id, actor_role=actor_role,
            summary=f"{model.task_id} を更新", metadata={"before": json.dumps(before, ensure_ascii=False), "patch": json.dumps(payload, ensure_ascii=False)})
        self._commit()
        return self.get_task(tenant_id, venture_id, task_row_id)

    def bulk_decide_applicability(
        self, tenant_id: str, venture_id: str, task_row_ids: list[str], applicability: str, reason: str, actor_user_id: str
    ) -> int:
        models = (
            self._db.execute(
                select(VentureTaskModel).where(
                    VentureTaskModel.tenant_id == tenant_id,
                    VentureTaskModel.venture_id == venture_id,
                    VentureTaskModel.id.in_(task_row_ids),
                )
            )
            .scalars()
            .all()
        )
        for model in models:
            before = {"applicability": model.applicability, "reason": model.applicability_reason}
            model.completion_approved_by = None
            model.completion_approved_at = None
            model.applicability = applicability
            model.applicability_reason = reason
            model.applicability_decided_by = actor_user_id
            model.applicability_decided_at = _now()
            self._write_audit(tenant_id=tenant_id, actor_user_id=actor_user_id, action="update",
                event_type="venture.task.applicability", resource_type="venture_task", actor_role="project_member",
                resource_id=model.id, summary=f"{model.task_id} の適用判定を更新",
                metadata={"before": json.dumps(before, ensure_ascii=False), "after": json.dumps({"applicability": applicability, "reason": reason}, ensure_ascii=False)})
        self._commit()
        return len(models)

    # ─────────────────────────────────────────────
    # ゲート
    # ─────────────────────────────────────────────
    def list_gates(self, tenant_id: str, venture_id: str) -> list[dict]:
        master = load_master()
        tasks = self.list_tasks(tenant_id, venture_id)
        result = self.list_ledger_entries(tenant_id, venture_id, "gate_run") or {"items": []}
        runs = result["items"]
        rows = []
        for gate in master.gates:
            candidates = [r for r in runs if r["values"].get("Gate") == gate["gate_id"]]
            candidates.sort(key=lambda r: (r.get("createdAt") or "", r["rowKey"]), reverse=True)
            run = candidates[0] if candidates else None
            values = run["values"] if run else {}
            derived = run["derived"] if run else {}
            effective = derived.get("有効性点検") == "整合済・正本決裁要確認"
            gate_tasks = [t for t in tasks if t["gateId"] == gate["gate_id"] and t["applicability"] == "適用"]
            rows.append({"id": run["id"] if run else gate["gate_id"], "gateId": gate["gate_id"],
                "subject": gate["subject"], "standardTaskId": gate["standard_task_id"],
                "approverRoleId": gate["approver_role_id"], "requiredEvidence": gate["required_evidence"],
                "allowedDecisions": gate["allowed_decisions"],
                "decision": values.get("判断結果", "未審査") if effective else "未審査",
                "recordedDecision": values.get("判断結果", "未審査"), "effective": effective,
                "validity": derived.get("有効性点検", "判断記録なし"), "gateRunId": run["rowKey"] if run else "",
                "scope": values.get("対象範囲/版", ""), "evidencePackageUri": values.get("証拠パッケージURI", ""),
                "conditions": values.get("条件・制約", ""), "conditionDue": values.get("条件期限", ""),
                "decidedBy": values.get("承認者PersonID"), "decidedByName": values.get("A実名", ""),
                "recordedByName": run["updatedByName"] if run else "", "decidedAt": values.get("判断日") or None,
                "nextAction": values.get("次Gate/Issue", ""), "reviewTrigger": values.get("再審査トリガー", ""),
                "appliedTaskCount": len(gate_tasks), "completedTaskCount": sum(t["completionValid"] for t in gate_tasks),
                "unapprovedTaskCount": sum(not t["completionValid"] for t in gate_tasks),
                "updatedAt": run["updatedAt"] if run else None})
        return rows

    def update_gate(self, *args, **kwargs):
        raise ValueError("GateRun台帳から判断を記録してください")

    # ─────────────────────────────────────────────
    # 要員
    # ─────────────────────────────────────────────
    def list_members(self, tenant_id: str, venture_id: str) -> list[dict]:
        models = (
            self._db.execute(
                select(VentureMemberModel).where(
                    VentureMemberModel.tenant_id == tenant_id, VentureMemberModel.venture_id == venture_id
                )
            )
            .scalars()
            .all()
        )
        master = load_master()
        names = self._user_names(tenant_id)
        return [
            {
                "id": model.id,
                "userId": model.user_id,
                "userName": names.get(model.user_id, model.user_id),
                "roleId": model.role_id,
                "roleName": master.role_by_id.get(model.role_id, {}).get("name", model.role_id),
                "allocationNote": model.allocation_note,
                "createdAt": _iso(model.created_at),
            }
            for model in sorted(models, key=lambda m: (m.role_id, m.user_id))
        ]

    def add_member(self, tenant_id: str, venture_id: str, user_id: str, role_id: str, note: str) -> dict:
        existing = (
            self._db.execute(
                select(VentureMemberModel).where(
                    VentureMemberModel.venture_id == venture_id,
                    VentureMemberModel.user_id == user_id,
                    VentureMemberModel.role_id == role_id,
                )
            )
            .scalars()
            .first()
        )
        if existing is None:
            self._db.add(
                VentureMemberModel(
                    id=f"vm-{uuid4().hex[:12]}",
                    venture_id=venture_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    role_id=role_id,
                    allocation_note=note,
                )
            )
        else:
            existing.allocation_note = note
        self._commit()
        rows = self.list_members(tenant_id, venture_id)
        return next(row for row in rows if row["userId"] == user_id and row["roleId"] == role_id)

    def remove_member(self, tenant_id: str, venture_id: str, member_id: str) -> bool:
        model = self._db.get(VentureMemberModel, member_id)
        if model is None or model.tenant_id != tenant_id or model.venture_id != venture_id:
            return False
        self._db.delete(model)
        self._commit()
        return True

    # ─────────────────────────────────────────────
    # 汎用台帳
    # ─────────────────────────────────────────────
    #: 点検が参照する他の台帳。原本の数式が引くシートに対応する。
    RELATED_LEDGERS = {
        "eval_run": ("eval_plan",),
        "required_eval": ("eval_plan", "eval_run"),
        "gate_run": ("required_eval", "retirement", "hypothesis", "condition", "eval_plan", "eval_run"),
        "release": (
            "gate_run", "condition", "required_eval", "retirement", "hypothesis",
            "eval_plan", "eval_run",
        ),
        "task_run": ("gate_run",),
        "role_staffing": ("role_staffing",),
    }

    def _ledger_values(self, tenant_id: str, venture_id: str, ledger_key: str) -> dict[str, dict]:
        rows = self._db.execute(
            select(VentureLedgerEntryModel).where(
                VentureLedgerEntryModel.tenant_id == tenant_id,
                VentureLedgerEntryModel.venture_id == venture_id,
                VentureLedgerEntryModel.ledger_key == ledger_key,
            )
        ).scalars()
        master = load_master().ledger_by_key.get(ledger_key, {})
        id_column = master.get("id_column", "")
        values: dict[str, dict] = {}
        for row in rows:
            item = dict(row.values_json or {})
            if ledger_key == "eval_plan":
                if row.is_master_row:
                    item.setdefault("EvalType", row.row_key)
            elif id_column:
                item.setdefault(id_column, row.row_key)
            values[row.row_key] = item
        return values

    def check_context(
        self, tenant_id: str, venture_id: str, ledger_key: str, row_key: str, siblings: dict
    ) -> CheckContext:
        """記録点検に必要な案件側の文脈を組み立てる。"""
        master = load_master()
        venture = self._db.get(VentureModel, venture_id)
        basis = as_of({"asOfDate": (venture.as_of_date if venture else "") or ""})[0]

        related: dict[str, dict[str, dict]] = {}
        for key in self.RELATED_LEDGERS.get(ledger_key, ()):
            related[key] = self._ledger_values(tenant_id, venture_id, key)
        related.setdefault(ledger_key, dict(siblings))

        plans: dict[str, dict] = {}
        for values in related.get("eval_plan", {}).values():
            key = plan_key(values)
            if key:
                plans[key] = values
        runs = dict(related.get("eval_run", {}))

        gate_ids = set(self._ledger_values(tenant_id, venture_id, "gate_run"))

        assessments: dict[str, dict[str, int]] = {}
        assessment_records = {}
        if ledger_key == "assignment":
            for record in self._db.execute(
                select(VentureSkillAssessmentModel).where(
                    VentureSkillAssessmentModel.tenant_id == tenant_id,
                    VentureSkillAssessmentModel.venture_id == venture_id,
                )
            ).scalars():
                assessments.setdefault(record.skill_id, {})[record.user_id] = record.assessed_level
                assessment_records[record.id] = {"skillId": record.skill_id, "userId": record.user_id,
                    "level": record.assessed_level, "evidenceUri": record.evidence_uri, "assessedBy": record.assessed_by}

        return CheckContext(
            as_of=basis,
            row_key=row_key,
            siblings=siblings,
            eval_plans=plans,
            eval_runs=runs,
            gate_row_ids=gate_ids,
            eval_type_ids={item["eval_type_id"] for item in master.eval_types},
            related=related,
            master_ids={
                "tasks_by_id": master.task_by_id,
                "skills_by_id": master.skill_by_id,
                "gates_by_id": master.gate_by_id,
                "role_ids": set(master.role_by_id),
            },
            assessments=assessments,
            assessment_records=assessment_records,
            member_roles={(m["userId"], m["roleId"]) for m in self.list_members(tenant_id, venture_id)} if ledger_key == "assignment" else set(),
            venture=self._venture_row(venture, {}) if venture else {},
            tasks={t["taskId"]: t for t in self.list_tasks(tenant_id, venture_id)} if ledger_key in ("gate_run", "release") else {},
        )

    def list_ledger_entries(self, tenant_id: str, venture_id: str, ledger_key: str) -> dict | None:
        master = load_master()
        ledger = master.ledger_by_key.get(ledger_key)
        if ledger is None:
            return None
        models = (
            self._db.execute(
                select(VentureLedgerEntryModel).where(
                    VentureLedgerEntryModel.tenant_id == tenant_id,
                    VentureLedgerEntryModel.venture_id == venture_id,
                    VentureLedgerEntryModel.ledger_key == ledger_key,
                )
            )
            .scalars()
            .all()
        )
        master_rows = {row.get(ledger["id_column"], ""): row for row in ledger["rows"]}
        input_columns = set(ledger["input_columns"])
        names = self._user_names(tenant_id)
        all_values = {model.row_key: dict(model.values_json or {}) for model in models}
        base_context = self.check_context(tenant_id, venture_id, ledger_key, "", all_values)
        entries = []
        for model in models:
            entries.append(
                {
                    "id": model.id,
                    "rowKey": model.row_key,
                    "isMasterRow": model.is_master_row,
                    "status": model.status,
                    "master": master_rows.get(model.row_key, {}),
                    # 入力列に射影して返す。画面はここで受けた値をそのまま送り返すので、
                    # 未知の列や入力列から外した列を渡すと保存時に弾かれてしまう。
                    "values": {
                        column: value
                        for column, value in (model.values_json or {}).items()
                        if column in input_columns
                    },
                    "updatedBy": model.updated_by,
                    "createdAt": _iso(model.created_at),
                    "derived": evaluate(
                        ledger_key,
                        {**(model.values_json or {}), **({"EvalType": (model.values_json or {}).get("EvalType", model.row_key if model.is_master_row else "")} if ledger_key == "eval_plan" else {ledger["id_column"]: model.row_key})},
                        replace(base_context, row_key=model.row_key,
                            siblings={k: v for k, v in all_values.items() if k != model.row_key}),
                    ),
                    "updatedByName": names.get(model.updated_by or "", ""),
                    "updatedAt": _iso(model.updated_at),
                }
            )
        for entry in entries:
            if ledger_key == "eval_plan" and entry["isMasterRow"]:
                entry["values"].setdefault("EvalType", entry["rowKey"])
            entry["checks"] = check_statuses(entry["derived"])
        entries.sort(key=lambda entry: (not entry["isMasterRow"], entry["rowKey"]))
        return {
            "ledger": {
                "key": ledger["key"],
                "name": ledger["name"],
                "summary": ledger["summary"],
                "sourceSheet": ledger["source_sheet"],
                "idColumn": ledger["id_column"],
                "seeded": ledger["seeded"],
                "masterColumns": ledger["master_columns"],
                "inputColumns": ledger["input_columns"],
                "notes": ledger["notes"],
                "columnRules": ledger.get("column_rules", {}),
                "derivedColumns": ledger.get("derived_columns", []),
                "rowLimit": ledger.get("row_limit"),
                "stateColumn": ledger.get("state_column", ""),
                "lockedStates": ledger.get("locked_states", []),
                "checkColumns": CHECK_COLUMNS.get(ledger_key, []),
                "masterRowCount": len(ledger["rows"]),
            },
            "items": entries,
        }

    def upsert_ledger_entry(
        self, tenant_id: str, venture_id: str, ledger_key: str, payload: dict, actor_user_id: str
    ) -> dict | None:
        master = load_master()
        ledger = master.ledger_by_key.get(ledger_key)
        if ledger is None:
            return None
        allowed = set(ledger["input_columns"])
        entry_id = payload.get("id")
        if entry_id:
            model = self._db.get(VentureLedgerEntryModel, entry_id)
            # ledger_key を照合しないと、別台帳のURLで他台帳の行に別スキーマの列を
            # 書き込めてしまう。書き込む前に弾く。
            if (
                model is None
                or model.tenant_id != tenant_id
                or model.venture_id != venture_id
                or model.ledger_key != ledger_key
            ):
                return None
        else:
            row_key = (payload.get("rowKey") or "").strip()
            if not row_key:
                row_key = f"{ledger['id_column']}-{uuid4().hex[:6]}"
            # 一意制約に当てて IntegrityError を出す前に、意味のあるエラーへ倒す。
            existing = self._db.execute(
                select(VentureLedgerEntryModel.id).where(
                    VentureLedgerEntryModel.tenant_id == tenant_id,
                    VentureLedgerEntryModel.venture_id == venture_id,
                    VentureLedgerEntryModel.ledger_key == ledger_key,
                    VentureLedgerEntryModel.row_key == row_key,
                )
            ).first()
            if existing is not None:
                raise LedgerRowKeyConflictError(row_key)
            model = VentureLedgerEntryModel(
                id=f"vl-{uuid4().hex[:12]}",
                venture_id=venture_id,
                tenant_id=tenant_id,
                ledger_key=ledger_key,
                row_key=row_key,
                is_master_row=False,
                values_json={},
                created_at=_now(),
            )
            self._db.add(model)

        before = dict(model.values_json or {})
        if payload.get("status"):
            model.status = payload["status"]
        incoming = payload.get("values") or {}
        values = dict(model.values_json or {})
        # マスタが定義した入力列だけを受け付ける
        for key, value in incoming.items():
            if key in allowed:
                values[key] = value
        model.values_json = values
        model.updated_by = actor_user_id
        if values != before and ledger_key in {"data", "dependency", "privacy", "feature_decision", "risk_screening", "adr"}:
            venture = self._db.get(VentureModel, venture_id)
            governance = dict(venture.governance or {})
            governance.update(riskConfirmed=False, riskState="再判定待ち",
                riskLedgerRevision=governance.get("riskLedgerRevision", 0) + 1,
                riskRecheckReason=f"{ledger_key} / {model.row_key} の変更")
            venture.governance = governance
        self._write_audit(tenant_id=tenant_id, event_type="venture.ledger.change", resource_type="venture_ledger",
            resource_id=model.id, action="update" if entry_id else "create", actor_user_id=actor_user_id, actor_role="",
            summary=f"{ledger_key} / {model.row_key}", metadata={"before": json.dumps(before, ensure_ascii=False),
            "after": json.dumps(values, ensure_ascii=False), "ventureId": venture_id})
        self._commit()

        result = self.list_ledger_entries(tenant_id, venture_id, ledger_key)
        if result is None:
            return None
        return next((item for item in result["items"] if item["id"] == model.id), None)

    def delete_ledger_entry(self, tenant_id: str, venture_id: str, ledger_key: str, entry_id: str) -> str:
        model = self._db.get(VentureLedgerEntryModel, entry_id)
        if model is None or model.tenant_id != tenant_id or model.venture_id != venture_id or model.ledger_key != ledger_key:
            return "not_found"
        return "protected"

    # ─────────────────────────────────────────────
    # スキル需要とギャップ
    # ─────────────────────────────────────────────
    def skill_gap(self, tenant_id: str, venture_id: str) -> dict:
        master = load_master()
        applied = (
            self._db.execute(
                select(VentureTaskModel).where(
                    VentureTaskModel.tenant_id == tenant_id,
                    VentureTaskModel.venture_id == venture_id,
                    VentureTaskModel.applicability == APPLICABILITY_APPLIED,
                )
            )
            .scalars()
            .all()
        )
        demand = master.skill_demand([task.task_id for task in applied])

        assessments = (
            self._db.execute(
                select(VentureSkillAssessmentModel).where(
                    VentureSkillAssessmentModel.tenant_id == tenant_id,
                    VentureSkillAssessmentModel.venture_id == venture_id,
                )
            )
            .scalars()
            .all()
        )
        by_skill: dict[str, list[VentureSkillAssessmentModel]] = {}
        for assessment in assessments:
            by_skill.setdefault(assessment.skill_id, []).append(assessment)

        assignments = self._ledger_values(tenant_id, venture_id, "assignment")
        members = {(m["userId"], m["roleId"]) for m in self.list_members(tenant_id, venture_id)}
        staffing = self._ledger_values(tenant_id, venture_id, "role_staffing")
        basis = as_of(self.get_venture(tenant_id, venture_id) or {})[0]
        def has_capacity(person):
            active = []
            for row in staffing.values():
                if row.get("PersonID") != person:
                    continue
                start, end = parse_date(row.get("配置開始")), parse_date(row.get("配置終了"))
                try:
                    amount = float(row.get("割当FTE（入力）", ""))
                    cap = float(row.get("当人の当日上限FTE", ""))
                except ValueError:
                    continue
                if start and end and start <= basis <= end:
                    active.append((amount, cap))
            return bool(active) and 0 < sum(x[0] for x in active) <= min(x[1] for x in active)
        names = self._user_names(tenant_id)
        course_titles = {course.slug: course.title for course in default_courses()}
        items = []
        for entry in demand:
            skill_id = entry["skillId"]
            records = by_skill.get(skill_id, [])
            allocation_checks = []
            for task_id in entry["taskIds"]:
                standard = next(x for x in master.skills_for_task(task_id) if x["skill_id"] == skill_id)
                for required_role in standard["exec_role_ids"]:
                    candidates = [x for x in assignments.values() if x.get("Task ID") == task_id and x.get("Skill ID") == skill_id and x.get("Role ID") == required_role]
                    best_for_task = 0
                    for allocation in candidates:
                        approved_on = parse_date(allocation.get("承認日"))
                        if not all(allocation.get(k) for k in ("割当承認者", "対象期間", "必要性・担当範囲")) or not approved_on or approved_on > basis:
                            continue
                        person, role = allocation.get("PersonID", ""), allocation.get("Role ID", "")
                        if (person, role) not in members or role not in standard["exec_role_ids"]:
                            continue
                        if allocation.get("役割区分") in ("独立評価", "品質決裁") and person == allocation.get("当該実装PersonID"):
                            continue
                        if not has_capacity(person):
                            continue
                        assessment = next((r for r in records if r.user_id == person and r.id == allocation.get("能力評価記録ID") and r.evidence_uri and r.assessed_by != person and (not r.due_date or (parse_date(r.due_date) and parse_date(r.due_date) >= basis))), None)
                        if assessment:
                            best_for_task = max(best_for_task, assessment.assessed_level)
                        supporter = allocation.get("支援者PersonID")
                        if allocation.get("支援方法") and allocation.get("支援証拠URI") and supporter and has_capacity(supporter) and (supporter, role) in members:
                            support = next((r for r in records if r.user_id == supporter and r.evidence_uri and r.assessed_by != supporter), None)
                            if support and allocation.get("役割区分") not in ("独立評価", "品質決裁"):
                                best_for_task = max(best_for_task, support.assessed_level)
                    required = standard["required_level"]
                    allocation_checks.append({"taskId": task_id, "roleId": required_role, "requiredLevel": required, "coveredLevel": best_for_task,
                                              "gap": max(0, required - best_for_task)})
            gap = max((r["gap"] for r in allocation_checks), default=entry["requiredLevel"])
            best = max(0, entry["requiredLevel"] - gap)
            items.append(
                {
                    **entry,
                    "coveredLevel": best,
                    "gap": gap,
                    "assignments": allocation_checks,
                    # 学習へ戻す導線。対応が無いスキルは空配列を返し、画面はリンクを出さない。
                    "courses": [
                        {
                            "courseSlug": link.course_slug,
                            "title": course_titles.get(link.course_slug, link.course_slug),
                            "coversLevel": link.covers_level,
                            "note": link.note,
                        }
                        for link in courses_for_skill(skill_id)
                        if link.course_slug in course_titles
                    ],
                    "assessments": [
                        {
                            "id": record.id,
                            "userId": record.user_id,
                            "userName": names.get(record.user_id, record.user_id),
                            "assessedLevel": record.assessed_level,
                            "evidenceUri": record.evidence_uri,
                            "developmentPlan": record.development_plan,
                            "dueDate": record.due_date,
                            "assessedAt": _iso(record.assessed_at),
                        }
                        for record in sorted(records, key=lambda r: -r.assessed_level)
                    ],
                }
            )
        return {
            "items": items,
            "appliedTaskCount": len(applied),
            "gapCount": sum(1 for item in items if item["gap"] > 0),
        }

    def upsert_skill_assessment(
        self, tenant_id: str, venture_id: str, payload: dict, actor_user_id: str
    ) -> dict:
        skill_id = payload["skillId"]
        user_id = payload["userId"]
        model = (
            self._db.execute(
                select(VentureSkillAssessmentModel).where(
                    VentureSkillAssessmentModel.venture_id == venture_id,
                    VentureSkillAssessmentModel.skill_id == skill_id,
                    VentureSkillAssessmentModel.user_id == user_id,
                )
            )
            .scalars()
            .first()
        )
        if model is None:
            model = VentureSkillAssessmentModel(
                id=f"vs-{uuid4().hex[:12]}",
                venture_id=venture_id,
                tenant_id=tenant_id,
                skill_id=skill_id,
                user_id=user_id,
            )
            self._db.add(model)
        if payload.get("assessedLevel") is not None:
            model.assessed_level = int(payload["assessedLevel"])
        for key, attribute in (
            ("evidenceUri", "evidence_uri"),
            ("developmentPlan", "development_plan"),
            ("dueDate", "due_date"),
        ):
            if payload.get(key) is not None:
                setattr(model, attribute, payload[key])
        model.assessed_by = actor_user_id
        model.assessed_at = _now()
        self._commit()
        names = self._user_names(tenant_id)
        return {
            "id": model.id,
            "skillId": model.skill_id,
            "userId": model.user_id,
            "userName": names.get(model.user_id, model.user_id),
            "assessedLevel": model.assessed_level,
            "evidenceUri": model.evidence_uri,
            "developmentPlan": model.development_plan,
            "dueDate": model.due_date,
            "assessedAt": _iso(model.assessed_at),
        }

    # ─────────────────────────────────────────────
    # ダッシュボード
    # ─────────────────────────────────────────────
    def summary(self, tenant_id: str, venture_id: str) -> dict | None:
        venture = self.get_venture(tenant_id, venture_id)
        if venture is None:
            return None
        master = load_master()
        tasks = self.list_tasks(tenant_id, venture_id)
        phases = []
        for phase in master.phases:
            phase_tasks = [t for t in tasks if t["phaseId"] == phase["phase_id"]]
            applied = [t for t in phase_tasks if t["applicability"] == APPLICABILITY_APPLIED]
            phases.append(
                {
                    "phaseId": phase["phase_id"],
                    "name": phase["name"],
                    "purpose": phase["purpose"],
                    "gateId": phase["gate_id"],
                    "total": len(phase_tasks),
                    "applied": len(applied),
                    "undecided": sum(1 for t in phase_tasks if t["applicability"] == APPLICABILITY_UNDECIDED),
                    "excluded": sum(1 for t in phase_tasks if t["applicability"] == APPLICABILITY_EXCLUDED),
                    "completed": sum(t["completionValid"] for t in applied),
                    "inProgress": sum(1 for t in applied if t["status"] == "進行中"),
                    "blocked": sum(1 for t in applied if t["blocker"]),
                }
            )
        gaps = self.skill_gap(tenant_id, venture_id)
        ledger_counts = []
        for ledger in master.ledgers:
            result = self.list_ledger_entries(tenant_id, venture_id, ledger["key"])
            items = result["items"] if result else []
            ledger_counts.append(
                {
                    "key": ledger["key"],
                    "name": ledger["name"],
                    "total": len(items),
                    "filled": sum(1 for item in items if item["values"]),
                }
            )
        panels = {}
        for key in ("hypothesis", "kpi", "condition", "cash_plan", "task_run"):
            data = self.list_ledger_entries(tenant_id, venture_id, key) or {"items": []}
            panels[key] = [{"id": r["rowKey"], "values": r["values"], "checks": r["derived"]}
                           for r in data["items"] if r["values"]]
        decisions = {"hypotheses": panels["hypothesis"], "kpis": panels["kpi"],
                     "conditions": panels["condition"], "cashPlans": panels["cash_plan"], "runs": panels["task_run"],
                     "riskState": venture.get("governance", {}).get("riskState", "未確認")}
        basis = as_of(venture)[0]
        actions = []
        for key, deadline in (("hypothesis", "再判断日"), ("condition", "期限"), ("task_run", "次回期限")):
            for row in panels[key]:
                if key == "condition" and row["checks"].get("条件点検") == "解消確認済":
                    continue
                values = row["values"]
                due = parse_date(values.get(deadline))
                actions.append({"ledgerKey": key, "rowId": row["id"], "dueDate": due.isoformat() if due else "",
                    "overdue": bool(due and due < basis),
                    "action": values.get("次の実験") or values.get("失効時処置") or values.get("Task ID") or "必要証拠と次の判断を設定",
                    "owner": values.get("Owner") or values.get("Owner PersonID") or "未割当"})
                if key == "hypothesis":
                    from infrastructure.venture_ledger_checks import _number, _fmt
                    cap, spent = _number(values, "追加投資上限（円）"), _number(values, "追加投資実績（円）")
                    row["checks"]["追加投資残額（円）"] = _fmt(cap - spent) if cap is not None and spent is not None and values.get("投資実績根拠URI") else "未計測"
        actions.sort(key=lambda a: (not a["overdue"], a["dueDate"] or "9999-12-31", a["rowId"]))
        decisions["nextActions"] = actions
        return {
            "venture": venture,
            "decisions": decisions,
            "phases": phases,
            "gates": self.list_gates(tenant_id, venture_id),
            "skillGapCount": gaps["gapCount"],
            "topSkillGaps": [item for item in gaps["items"] if item["gap"] > 0][:5],
            "ledgers": ledger_counts,
            "members": self.list_members(tenant_id, venture_id),
        }
