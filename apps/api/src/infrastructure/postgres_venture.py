"""事業PJ台帳の永続化。

工程マスタ（venture_process_master.json）は読み取り専用の標準定義。
案件を作ると、その時点のマスタから 132 タスク・6 ゲート・台帳の点検行を
インスタンス化して台帳を持たせる。
"""
from __future__ import annotations

from datetime import datetime, timezone
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
from infrastructure.venture_rules import as_of
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
        return task.get("depends_on", [])
    return [part.strip() for part in override.split(",")]


def _dependency_check(model: VentureTaskModel, task: dict) -> str:
    """原本17!BC 依存記法点検と、W の依存変更承認不足。"""
    override = (model.depends_on_override or "").strip()
    if not override:
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
        tasks = (
            self._db.execute(select(VentureTaskModel).where(VentureTaskModel.venture_id == venture_id))
            .scalars()
            .all()
        )
        applied = [t for t in tasks if t.applicability == APPLICABILITY_APPLIED]
        return {
            "taskTotal": len(tasks),
            "taskApplied": len(applied),
            "taskUndecided": sum(1 for t in tasks if t.applicability == APPLICABILITY_UNDECIDED),
            "taskCompleted": sum(1 for t in applied if t.status == "完了"),
        }

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
            risk_tier=payload.get("riskTier", "T1"),
            risk_tier_rationale=payload.get("riskTierRationale", ""),
            status=payload.get("status", "計画中"),
            current_phase_id=payload.get("currentPhaseId", "B0"),
            business_owner_user_id=payload.get("businessOwnerUserId"),
            conditions=conditions,
            as_of_date=payload.get("asOfDate", "") or "",
            created_by=created_by,
        )
        self._db.add(model)

        # 工程タスク 132 件を展開する
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

        self._commit()
        return self.get_venture(tenant_id, venture_id)

    def delete_venture(self, tenant_id: str, venture_id: str, actor_user_id: str, actor_role: str) -> bool:
        """案件と子テーブルの行を消す。

        DBのFKに ON DELETE CASCADE を頼らず、子を明示的に消してから親を消す
        （SQLiteはデフォルトでFK制約を強制しないため、Postgres・SQLite両方で
        同じ挙動にする）。監査ログだけは resource_id が文字列参照のFKなしなので
        そのまま残り、削除された案件がかつて存在した痕跡になる。
        """
        model = self._db.get(VentureModel, venture_id)
        if model is None or model.tenant_id != tenant_id:
            return False
        name = model.name
        for child_model in (
            VentureTaskModel,
            VentureGateModel,
            VentureMemberModel,
            VentureLedgerEntryModel,
            VentureSkillAssessmentModel,
        ):
            rows = self._db.execute(
                select(child_model).where(child_model.venture_id == venture_id)
            ).scalars().all()
            for row in rows:
                self._db.delete(row)
        self._db.delete(model)
        self._write_audit(
            tenant_id=tenant_id,
            event_type="venture.delete",
            resource_type="venture",
            resource_id=venture_id,
            action="delete",
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            summary=f"案件「{name}」を削除",
        )
        self._commit()
        return True

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
        if phase_id:
            query = query.where(VentureTaskModel.phase_id == phase_id)
        if applicability:
            query = query.where(VentureTaskModel.applicability == applicability)
        if status:
            query = query.where(VentureTaskModel.status == status)
        if assignee_user_id:
            query = query.where(VentureTaskModel.assignee_user_id == assignee_user_id)
        models = self._db.execute(query).scalars().all()
        master = load_master()
        names = self._user_names(tenant_id)
        rows = [self._task_row(model, master, names) for model in models]
        rows.sort(key=lambda row: row["taskId"])
        return rows

    def get_task(self, tenant_id: str, venture_id: str, task_row_id: str) -> dict | None:
        model = self._db.get(VentureTaskModel, task_row_id)
        if model is None or model.tenant_id != tenant_id or model.venture_id != venture_id:
            return None
        return self._task_row(model, load_master(), self._user_names(tenant_id))

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

        self._commit()
        master = load_master()
        return self._task_row(model, master, self._user_names(tenant_id))

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
            model.applicability = applicability
            model.applicability_reason = reason
            model.applicability_decided_by = actor_user_id
            model.applicability_decided_at = _now()
        self._commit()
        return len(models)

    # ─────────────────────────────────────────────
    # ゲート
    # ─────────────────────────────────────────────
    def list_gates(self, tenant_id: str, venture_id: str) -> list[dict]:
        models = (
            self._db.execute(
                select(VentureGateModel).where(
                    VentureGateModel.tenant_id == tenant_id, VentureGateModel.venture_id == venture_id
                )
            )
            .scalars()
            .all()
        )
        master = load_master()
        names = self._user_names(tenant_id)
        # ゲートごとの進捗はタスク台帳から数える。1回だけ読み込む。
        all_tasks = (
            self._db.execute(
                select(VentureTaskModel).where(
                    VentureTaskModel.tenant_id == tenant_id, VentureTaskModel.venture_id == venture_id
                )
            )
            .scalars()
            .all()
        )
        rows = []
        for model in sorted(models, key=lambda m: m.gate_id):
            gate = master.gate_by_id.get(model.gate_id, {})
            standard_task_id = gate.get("standard_task_id", "")
            gate_tasks = [
                task
                for task in all_tasks
                if task.gate_id == model.gate_id and task.applicability == APPLICABILITY_APPLIED
            ]
            rows.append(
                {
                    "id": model.id,
                    "gateId": model.gate_id,
                    "subject": gate.get("subject", ""),
                    "standardTaskId": standard_task_id,
                    "approverRoleId": gate.get("approver_role_id", ""),
                    "requiredEvidence": gate.get("required_evidence", ""),
                    "allowedDecisions": gate.get("allowed_decisions", []),
                    "decision": model.decision,
                    "scope": model.scope,
                    "evidencePackageUri": model.evidence_package_uri,
                    "conditions": model.conditions,
                    "conditionDue": model.condition_due,
                    "decidedBy": model.decided_by,
                    # 承認者の実名は入力された値が正。操作した人は別項目で返す。
                    # （原本 29 の「A実名」は、プラットフォームに口座を持たない
                    #  役員などを記録するための欄で、記録係の名前ではない）
                    "decidedByName": model.decided_by_name or names.get(model.decided_by or "", ""),
                    "recordedByName": names.get(model.decided_by or "", ""),
                    "decidedAt": _iso(model.decided_at),
                    "nextAction": model.next_action,
                    "reviewTrigger": model.review_trigger,
                    "appliedTaskCount": len(gate_tasks),
                    "completedTaskCount": sum(1 for t in gate_tasks if t.status == "完了"),
                    "unapprovedTaskCount": sum(1 for t in gate_tasks if t.completion_approved_at is None),
                    "updatedAt": _iso(model.updated_at),
                }
            )
        return rows

    def update_gate(
        self,
        tenant_id: str,
        venture_id: str,
        gate_row_id: str,
        payload: dict,
        actor_user_id: str,
        actor_role: str = "",
    ) -> dict | None:
        model = self._db.get(VentureGateModel, gate_row_id)
        if model is None or model.tenant_id != tenant_id or model.venture_id != venture_id:
            return None
        simple = {
            "scope": "scope",
            "evidencePackageUri": "evidence_package_uri",
            "conditions": "conditions",
            "conditionDue": "condition_due",
            "nextAction": "next_action",
            "reviewTrigger": "review_trigger",
            "decidedByName": "decided_by_name",
        }
        for key, attribute in simple.items():
            if key in payload and payload[key] is not None:
                setattr(model, attribute, payload[key])
        if payload.get("decision"):
            previous_decision = model.decision
            previous_by = model.decided_by
            previous_at = _iso(model.decided_at)
            # 取り消しで消える値も、消す前に監査ログ用に控える。
            decided_by_name = model.decided_by_name or ""
            model.decision = payload["decision"]
            if payload["decision"] == "未審査":
                model.decided_by = None
                model.decided_at = None
                # 判断を取り消したら承認者の実名も残さない（監査ログには残る）。
                model.decided_by_name = ""
            else:
                model.decided_by = actor_user_id
                model.decided_at = _now()
            # ゲート行は最新の判断しか持たない。「未審査」に戻すと承認の事実が
            # 行から消えるので、判断の変更は必ず監査ログに追記する。
            self._write_audit(
                tenant_id=tenant_id,
                event_type="venture.gate.decision",
                resource_type="venture_gate",
                resource_id=gate_row_id,
                action=payload["decision"],
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                summary=f"{model.gate_id} の判断を {previous_decision} から {payload['decision']} に変更",
                metadata={
                    "ventureId": venture_id,
                    "gateId": model.gate_id,
                    "previousDecision": previous_decision,
                    "previousDecidedBy": previous_by or "",
                    "previousDecidedAt": previous_at or "",
                    "decidedByName": decided_by_name,
                    "evidencePackageUri": model.evidence_package_uri or "",
                },
            )
        self._commit()
        rows = self.list_gates(tenant_id, venture_id)
        return next((row for row in rows if row["id"] == gate_row_id), None)

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
            if id_column:
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

        gate_ids: set[str] = set()
        if ledger_key in ("hypothesis", "condition"):
            gate_ids = set(
                self._db.execute(
                    select(VentureGateModel.id).where(
                        VentureGateModel.tenant_id == tenant_id,
                        VentureGateModel.venture_id == venture_id,
                    )
                ).scalars()
            )

        assessments: dict[str, dict[str, int]] = {}
        if ledger_key == "assignment":
            for record in self._db.execute(
                select(VentureSkillAssessmentModel).where(
                    VentureSkillAssessmentModel.tenant_id == tenant_id,
                    VentureSkillAssessmentModel.venture_id == venture_id,
                )
            ).scalars():
                assessments.setdefault(record.skill_id, {})[record.user_id] = record.assessed_level

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
                    "derived": evaluate(
                        ledger_key,
                        {**(model.values_json or {}), ledger["id_column"]: model.row_key},
                        self.check_context(
                            tenant_id,
                            venture_id,
                            ledger_key,
                            model.row_key,
                            {k: v for k, v in all_values.items() if k != model.row_key},
                        ),
                    ),
                    "updatedByName": names.get(model.updated_by or "", ""),
                    "updatedAt": _iso(model.updated_at),
                }
            )
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
            )
            self._db.add(model)

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
        self._commit()

        result = self.list_ledger_entries(tenant_id, venture_id, ledger_key)
        if result is None:
            return None
        return next((item for item in result["items"] if item["id"] == model.id), None)

    def delete_ledger_entry(self, tenant_id: str, venture_id: str, ledger_key: str, entry_id: str) -> str:
        """行を削除する。結果は deleted / not_found / master_row のいずれか。

        ledger_key を照合しないと、ある台帳のURLで別台帳の行を消せてしまう。
        """
        model = self._db.get(VentureLedgerEntryModel, entry_id)
        if (
            model is None
            or model.tenant_id != tenant_id
            or model.venture_id != venture_id
            or model.ledger_key != ledger_key
        ):
            return "not_found"
        if model.is_master_row:
            # 点検行はマスタ由来。削除ではなく「対象外」の記録で残す。
            return "master_row"
        self._db.delete(model)
        self._commit()
        return "deleted"

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

        names = self._user_names(tenant_id)
        course_titles = {course.slug: course.title for course in default_courses()}
        items = []
        for entry in demand:
            skill_id = entry["skillId"]
            records = by_skill.get(skill_id, [])
            best = max((record.assessed_level for record in records), default=0)
            items.append(
                {
                    **entry,
                    "coveredLevel": best,
                    "gap": max(0, entry["requiredLevel"] - best),
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
                    "completed": sum(1 for t in applied if t["status"] == "完了"),
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
        return {
            "venture": venture,
            "phases": phases,
            "gates": self.list_gates(tenant_id, venture_id),
            "skillGapCount": gaps["gapCount"],
            "topSkillGaps": [item for item in gaps["items"] if item["gap"] > 0][:5],
            "ledgers": ledger_counts,
            "members": self.list_members(tenant_id, venture_id),
        }
