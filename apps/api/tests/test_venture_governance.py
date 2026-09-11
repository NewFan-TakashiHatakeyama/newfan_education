"""PdM adversarial findings: exercise the authoritative path and downstream invalidation."""
from datetime import datetime, timezone
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import select

from main import app
from infrastructure.db import ScopedSession
from infrastructure.sql_models import AuditLogModel
from infrastructure.venture_governance import check_statuses
from infrastructure.venture_master import load_master
from test_acceptance_sheet33 import (sign_in, make_venture, put, rows_of, seed_required_eval,
    GATE_RUN_BASE, RELEASE_BASE, RUN_BASE, APPROVED_PLAN, SET_APPROVAL)


def setup():
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    vid = make_venture(client, admin, asOfDate="2099-12-31")["id"]
    return client, admin, vid


def prepare_task(client, admin, vid, task_id="B0-01", person="demo-user"):
    task = next(r for r in client.get(f"/api/v1/ventures/{vid}/tasks", headers=admin).json()["items"] if r["taskId"] == task_id)
    for user, role in ((person, task["roleId"]), ("admin-user", task["approverRoleId"])):
        added = client.post(f"/api/v1/ventures/{vid}/members", headers=admin, json={"userId": user, "roleId": role})
        assert added.status_code == 200, added.text
    now = datetime.now(timezone.utc).date().isoformat()
    res = client.patch(f"/api/v1/ventures/{vid}/tasks/{task['id']}", headers=admin, json={
        "applicability": "適用", "assigneeUserId": person, "actualStart": now, "actualEnd": now})
    assert res.status_code == 200, res.text
    return res.json()


def test_canonical_release_and_eval_revocation_propagate():
    client, admin, vid = setup()
    seed_required_eval(client, admin, vid)
    gate = put(client, admin, vid, "gate_run", GATE_RUN_BASE, row_key="GR-1", verify=True)
    assert gate.status_code == 200, gate.text
    assert gate.json()["derived"]["有効性点検"] == "整合済・正本決裁要確認", gate.json()
    release = put(client, admin, vid, "release", {**RELEASE_BASE, "GateRun ID": "GR-1", "公開ManifestHash": "sha256:aaa"}, row_key="REL-001")
    assert release.status_code == 200, release.text
    assert release.json()["derived"]["公開準備点検"] == "準備記録整合・実行許可は正本"
    projected = next(r for r in client.get(f"/api/v1/ventures/{vid}/gates", headers=admin).json()["items"] if r["gateId"] == "G3")
    assert projected["effective"] and projected["gateRunId"] == "GR-1"
    run = next(r for r in rows_of(client, admin, vid, "eval_run") if r["rowKey"] == "R-PASS")
    cancelled = put(client, admin, vid, "eval_run", {"無効化・取消理由": "評価データの混入"}, entry_id=run["id"])
    assert cancelled.status_code == 200, cancelled.text
    assert rows_of(client, admin, vid, "required_eval")[0]["derived"]["充足フラグ"] == "0"
    assert rows_of(client, admin, vid, "release")[0]["derived"]["公開準備点検"] == "決裁整合未充足"
    summary = client.get(f"/api/v1/ventures/{vid}/summary", headers=admin).json()
    assert not next(r for r in summary["gates"] if r["gateId"] == "G3")["effective"]
    assert put(client, admin, vid, "eval_run", {"無効化・取消理由": ""}, entry_id=run["id"]).status_code == 400


def test_risk_change_invalidates_and_full_set_is_required():
    client, admin, vid = setup()
    seed_required_eval(client, admin, vid)
    gate = put(client, admin, vid, "gate_run", GATE_RUN_BASE, row_key="GR", verify=True)
    assert gate.json()["derived"]["必須評価・前提点検"] == "必須評価セット充足"
    changed = client.patch(f"/api/v1/ventures/{vid}", headers=admin, json={"serviceCountries": "追加地域"})
    assert changed.status_code == 200, changed.text
    assert not changed.json()["governance"]["riskConfirmed"]
    assert rows_of(client, admin, vid, "gate_run")[0]["derived"]["必須評価・前提点検"] == "リスク・前提再確認要"


def test_completed_status_does_not_count_without_approval_and_edits_invalidate():
    client, admin, vid = setup()
    task = prepare_task(client, admin, vid)
    path = f"/api/v1/ventures/{vid}/tasks/{task['id']}"
    raw = client.patch(path, headers=admin, json={"status": "完了"})
    assert not raw.json()["completionValid"]
    assert client.get(f"/api/v1/ventures/{vid}", headers=admin).json()["taskCompleted"] == 0
    complete = client.patch(path, headers=admin, json={"evidenceUri": "https://example.test/evidence", "approveCompletion": True})
    assert complete.status_code == 200, complete.text
    assert complete.json()["completionValid"]
    assert client.get(f"/api/v1/ventures/{vid}", headers=admin).json()["taskCompleted"] == 1
    edited = client.patch(path, headers=admin, json={"evidenceUri": "https://example.test/revised"})
    assert not edited.json()["completionValid"] and not edited.json()["completionApprovedAt"]
    ScopedSession.remove()
    logs = ScopedSession.execute(select(AuditLogModel).where(AuditLogModel.resource_id == task["id"])).scalars().all()
    assert any(log.metadata_json.get("before") for log in logs)
    ScopedSession.remove()


def test_negative_verdicts_never_use_success_style():
    checks = check_statuses({s: s for s in ("未充足", "Manifest不一致", "決裁整合未充足", "記録あり", "新しい未知の判定")})
    assert checks["記録あり"]["severity"] == "success"
    assert all(v["severity"] == "warning" for k, v in checks.items() if k != "記録あり")


def test_same_day_approval_order_and_timezone_required():
    client, admin, vid = setup()
    plan = put(client, admin, vid, "eval_plan", {**APPROVED_PLAN, "EvalType": "E01"}, row_key="PLAN")
    assert plan.status_code == 200
    date_only = put(client, admin, vid, "eval_run", {**RUN_BASE, "日時": "2026-09-01"}, row_key="DATE")
    assert date_only.status_code == 400
    inverted = put(client, admin, vid, "eval_run", {**RUN_BASE, "日時": "2026-09-01T18:00:00+09:00", "承認日": "2026-09-01T08:00:00+09:00"}, row_key="BACKWARDS")
    assert inverted.status_code == 400 and inverted.json()["detail"] == "評価承認日時逆転"


def test_archive_preserves_history_and_legacy_gate_cannot_approve():
    client, admin, vid = setup()
    assert client.patch(f"/api/v1/ventures/{vid}/gates/G3", headers=admin, json={"decision": "承認"}).status_code == 400
    assert client.delete(f"/api/v1/ventures/{vid}", headers=admin).status_code == 400
    archived = client.patch(f"/api/v1/ventures/{vid}", headers=admin, json={"status": "アーカイブ"})
    assert archived.status_code == 200
    assert len(client.get(f"/api/v1/ventures/{vid}/tasks", headers=admin).json()["items"]) == 132


@pytest.mark.parametrize("classification_count", [1, 17])
def test_incomplete_eval_classifications_never_satisfy_g3(classification_count):
    client, admin, vid = setup()
    seed_required_eval(client, admin, vid, classification_count=classification_count)
    gate = put(client, admin, vid, "gate_run", GATE_RUN_BASE, row_key="GR", verify=True)
    assert gate.status_code == 200, gate.text
    assert gate.json()["derived"]["必須評価・前提点検"] == "必須分類・集合不足"
    assert gate.json()["derived"]["有効性点検"] != "整合済・正本決裁要確認"


def test_rag_requires_completed_task_even_when_all_classifications_exist():
    client, admin, vid = setup()
    seed_required_eval(client, admin, vid)
    changed = client.patch(f"/api/v1/ventures/{vid}", headers=admin, json={
        "conditions": {"RAG": "適用"}, "confirmRisk": True, "riskEvidenceUri": "https://example.test/risk/rag"})
    assert changed.status_code == 200, changed.text
    gate = put(client, admin, vid, "gate_run", GATE_RUN_BASE, row_key="GR", verify=True)
    assert gate.json()["derived"]["必須評価・前提点検"] == "機能別評価・対象外未完"


def test_eval_set_requires_exact_plan_release_and_source_approval():
    client, admin, vid = setup()
    plan = put(client, admin, vid, "eval_plan", {**APPROVED_PLAN, "EvalType": "E01"}, row_key="P")
    assert plan.status_code == 200
    assert client.delete(f"/api/v1/ventures/{vid}/ledgers/eval_plan/entries/{plan.json()['id']}", headers=admin).status_code == 400
    foreign = put(client, admin, vid, "eval_run", {**RUN_BASE, "対象Release/Issue": "OTHER"}, row_key="FOREIGN")
    assert foreign.status_code == 200
    base = {**SET_APPROVAL, "EvalPlanKey": "EP-001@1", "Release ID": "REL-001", "ManifestHash": "sha256:aaa", "適用": "必須", "EvalRun ID": "FOREIGN"}
    mismatch = put(client, admin, vid, "required_eval", base, row_key="SET")
    assert mismatch.status_code == 400 and mismatch.json()["detail"] == "評価対象不一致"
    missing = put(client, admin, vid, "required_eval", {**base, "集合承認URI": ""}, row_key="NO-APPROVAL")
    assert missing.status_code == 200
    assert missing.json()["derived"]["充足フラグ"] == "0"


def test_project_role_overrides_application_role_without_granting_verification():
    client, admin, vid = setup()
    learner = sign_in(client, "learner@example.com", "Learner123!")
    path = f"/api/v1/ventures/{vid}"
    assert client.patch(path, headers=learner, json={"summary": "outside"}).status_code == 404
    assert client.post(f"{path}/members", headers=admin, json={"userId": "demo-user", "roleId": "R02"}).status_code == 200
    assert client.patch(path, headers=learner, json={"summary": "担当PdM"}).status_code == 200
    forged = put(client, learner, vid, "gate_run", {**GATE_RUN_BASE, "正本確認者PersonID": "admin-user"}, row_key="FORGED")
    assert forged.status_code == 403
    assert put(client, learner, vid, "gate_run", GATE_RUN_BASE, row_key="GR", verify=True).status_code == 403
    assessed = client.post(f"{path}/skill-assessments", headers=learner, json={"skillId": "S001", "userId": "admin-user", "assessedLevel": 1, "evidenceUri": "https://example.test/proof"})
    assert assessed.status_code == 200, assessed.text


def test_skill_coverage_requires_role_assignment_evidence_and_current_capacity():
    client, admin, vid = setup()
    link = load_master().task_skills[0]
    task_id, skill_id = link["task_id"], link["skill_id"]
    roles = link["exec_role_ids"]
    tasks = client.get(f"/api/v1/ventures/{vid}/tasks", headers=admin).json()["items"]
    assert client.post(f"/api/v1/ventures/{vid}/tasks/applicability", headers=admin, json={"taskRowIds": [t["id"] for t in tasks if t["taskId"] != task_id], "applicability": "対象外", "reason": "このテストの対象工程を限定"}).status_code == 200
    for role in roles:
        assert client.post(f"/api/v1/ventures/{vid}/members", headers=admin, json={"userId": "demo-user", "roleId": role}).status_code == 200
    assessment = client.post(f"/api/v1/ventures/{vid}/skill-assessments", headers=admin, json={"skillId": skill_id, "userId": "demo-user", "assessedLevel": 3, "evidenceUri": "https://example.test/assessment"}).json()
    def gap():
        return next(r for r in client.get(f"/api/v1/ventures/{vid}/skill-gap", headers=admin).json()["items"] if r["skillId"] == skill_id)
    assert gap()["gap"] > 0  # A capable but unallocated person does not cover demand.
    for role in roles:
        allocation = put(client, admin, vid, "assignment", {"Task ID": task_id, "Skill ID": skill_id, "Role ID": role,
            "必要Lv": str(link["required_level"]), "PersonID": "demo-user", "能力評価記録ID": assessment["id"],
            "必要性・担当範囲": "実施担当", "割当承認者": "admin-user", "承認日": "2026-09-01", "対象期間": "2026-2099"}, row_key=role)
        assert allocation.status_code == 200, allocation.text
    assert gap()["gap"] > 0  # Still no current capacity.
    staffing = put(client, admin, vid, "role_staffing", {"PersonID": "demo-user", "配置開始": "2026-01-01", "配置終了": "2099-12-31", "割当FTE（入力）": "0.5", "当人の当日上限FTE": "1"}, row_key="CAPACITY")
    assert staffing.status_code == 200, staffing.text
    assert gap()["gap"] == 0
    expired = put(client, admin, vid, "role_staffing", {"配置終了": "2026-09-01"}, entry_id=staffing.json()["id"])
    assert expired.status_code == 200
    assert gap()["gap"] > 0


def test_unmeasured_finances_remain_unknown_and_zero_is_explicit():
    client, admin, vid = setup()
    missing = put(client, admin, vid, "cash_plan", {"期首現金": "100"}, row_key="MISSING")
    assert missing.json()["derived"]["期末現金"] == ""
    explicit = {k: "0" for k in ("期首現金", "確定調達/投資受入", "期間入金", "期間支出", "最低確保現金")}
    zero = put(client, admin, vid, "cash_plan", explicit, row_key="ZERO")
    assert zero.json()["derived"]["期末現金"] == "0"
    unmeasured = put(client, admin, vid, "cash_plan", {**explicit, "測定区分": "未計測"}, row_key="UNMEASURED")
    assert unmeasured.json()["derived"]["期末現金"] == ""


def test_repeated_runs_can_exceed_workbook_reserved_rows():
    client, admin, vid = setup()
    for i in range(61):
        response = put(client, admin, vid, "task_run", {}, row_key=f"REPEAT-{i:03}")
        assert response.status_code == 200, response.text
    assert len(rows_of(client, admin, vid, "task_run")) == 61


def test_migration_preserves_old_gate_without_promoting_it():
    import importlib.util
    from pathlib import Path
    from sqlalchemy import create_engine, text
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from infrastructure.db import Base
    from infrastructure.sql_models import VentureModel, VentureGateModel, VentureLedgerEntryModel
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    path = Path(__file__).parents[1] / "migrations/versions/20260911_0004_venture_governance.py"
    spec = importlib.util.spec_from_file_location("governance_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    with engine.begin() as connection:
        connection.execute(VentureModel.__table__.insert().values(id="v", tenant_id="t", name="legacy", created_by="u"))
        connection.execute(VentureGateModel.__table__.insert().values(id="old", tenant_id="t", venture_id="v", gate_id="G3", decision="承認", evidence_package_uri="https://example.test/old"))
        connection.execute(text("ALTER TABLE ventures DROP COLUMN governance"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(select(VentureLedgerEntryModel.__table__)).mappings().all()
        assert len(rows) == 1 and rows[0]["status"] == "移行・正本未確認"
        assert rows[0]["values_json"]["判断結果"] == "承認"
        assert not rows[0]["values_json"].get("正本確認日時")
        assert connection.execute(select(VentureGateModel.id)).scalar() == "old"
    engine.dispose()


def test_new_agent_plan_versions_keep_classification_and_trial_requirements():
    client, admin, vid = setup()
    incomplete = put(client, admin, vid, "eval_plan", {**APPROVED_PLAN, "EvalType": "E05"}, row_key="AGENT@1")
    assert incomplete.status_code == 200
    assert incomplete.json()["values"]["EvalType"] == "E05"
    assert incomplete.json()["derived"]["計画記録点検"] == "試行状態・成功定義不足"
    revision = put(client, admin, vid, "eval_plan", {**APPROVED_PLAN, "EvalType": "E05", "計画版": "2",
        "初期状態／Fixture定義URI": "https://example.test/fixture", "Reset・副作用検査": "初期状態を復元・副作用差分を比較",
        "試行成功率の定義": "3反復すべて成功"}, row_key="AGENT@2")
    assert revision.status_code == 200
    assert revision.json()["derived"]["計画記録点検"] == "計画記録あり"
    run = put(client, admin, vid, "eval_run", {**RUN_BASE, "EvalPlanKey": "EP-001@2"}, row_key="TRIAL")
    assert run.json()["derived"]["記録点検"] == "Trial状態証拠不足"


def test_concurrent_plan_confirmation_and_edit_cannot_rewrite_final_plan():
    from concurrent.futures import ThreadPoolExecutor
    client, admin, vid = setup()
    draft = put(client, admin, vid, "eval_plan", {**APPROVED_PLAN, "EvalType": "E01", "状態": "設計中"}, row_key="PLAN").json()
    with ThreadPoolExecutor(max_workers=2) as pool:
        approved = pool.submit(put, client, admin, vid, "eval_plan", {"状態": "承認", "合格閾値/方向": APPROVED_PLAN["合格閾値/方向"]}, entry_id=draft["id"])
        edited = pool.submit(put, client, admin, vid, "eval_plan", {"合格閾値/方向": "閾値を0へ変更"}, entry_id=draft["id"])
        assert approved.result().status_code == 200
        assert edited.result().status_code in (200, 400)
    final = next(r for r in rows_of(client, admin, vid, "eval_plan") if r["id"] == draft["id"])
    assert final["values"]["合格閾値/方向"] == APPROVED_PLAN["合格閾値/方向"]


def test_summary_prioritizes_overdue_decisions_and_calculates_evidenced_budget():
    client, admin, vid = setup()
    row = put(client, admin, vid, "hypothesis", {"具体仮説/対象者": "現場監督の反復利用", "再判断日": "2026-09-01", "次の実験": "有償継続の確認", "追加投資上限（円）": "1000", "追加投資実績（円）": "300", "投資実績根拠URI": "https://example.test/spend"}, row_key="DECISION")
    assert row.status_code == 200, row.text
    decisions = client.get(f"/api/v1/ventures/{vid}/summary", headers=admin).json()["decisions"]
    assert decisions["nextActions"][0]["overdue"]
    assert decisions["nextActions"][0]["action"] == "有償継続の確認"
    assert decisions["hypotheses"][0]["checks"]["追加投資残額（円）"] == "700"


def test_data_use_change_invalidates_risk_and_old_decision_after_reconfirmation():
    client, admin, vid = setup()
    seed_required_eval(client, admin, vid)
    gate = put(client, admin, vid, "gate_run", GATE_RUN_BASE, row_key="GR", verify=True)
    assert gate.json()["derived"]["有効性点検"] == "整合済・正本決裁要確認"
    assert put(client, admin, vid, "data", {"名称・種類": "個人情報を含む新データ", "個人情報区分": "個人情報"}, row_key="D-NEW").status_code == 200
    current = client.get(f"/api/v1/ventures/{vid}", headers=admin).json()
    assert current["governance"]["riskState"] == "再判定待ち"
    reconfirmed = client.patch(f"/api/v1/ventures/{vid}", headers=admin, json={"confirmRisk": True, "riskEvidenceUri": "https://example.test/risk/v2"})
    assert reconfirmed.status_code == 200
    assert rows_of(client, admin, vid, "gate_run")[0]["derived"]["必須評価・前提点検"] == "リスク・前提再確認要"


def test_set_versions_and_duplicate_classifications_are_not_mixed():
    client, admin, vid = setup()
    seed_required_eval(client, admin, vid)
    wrong_version = put(client, admin, vid, "gate_run", {**GATE_RUN_BASE, "集合版／正本ID": "SET@2"}, row_key="WRONG", verify=True)
    assert wrong_version.json()["derived"]["必須評価・前提点検"] == "必須分類・集合不足"
    duplicate = put(client, admin, vid, "required_eval", {**SET_APPROVAL, "Release ID": "REL-001", "ManifestHash": "sha256:aaa", "EvalPlanKey": "EP-001@1", "適用": "必須", "EvalRun ID": "R-PASS"}, row_key="DUP")
    assert duplicate.status_code == 200
    gate = put(client, admin, vid, "gate_run", GATE_RUN_BASE, row_key="DUPLICATE", verify=True)
    assert gate.json()["derived"]["重複した評価分類"] == "E01"
    assert gate.json()["derived"]["必須評価・前提点検"] == "必須分類・集合不足"


def test_timezone_equivalence_and_overnight_incident_order():
    from infrastructure.venture_rules import parse_timestamp
    assert parse_timestamp("2026-09-11T09:00:00+09:00") == parse_timestamp("2026-09-11T00:00:00Z")
    client, admin, vid = setup()
    base = {"概要・利用者影響": "応答停止", "重大度/境界": "運用上の障害", "Owner": "R12", "状態": "復旧",
        "検知日時": "2026-09-10T23:50:00+09:00", "受付日時": "2026-09-10T23:55:00+09:00", "復旧日時": "2026-09-11T00:10:00+09:00",
        "封じ込め/手動対応": "手動経路", "manifest/trace URI": "https://example.test/trace"}
    good = put(client, admin, vid, "incident", base, row_key="OVERNIGHT")
    assert good.status_code == 200, good.text
    assert good.json()["derived"]["状態・日時点検"] == "復旧記録あり・原因審査継続"


def test_dependency_evidence_invalidation_and_runtime_cycle_detection():
    client, admin, vid = setup()
    parent = prepare_task(client, admin, vid, "B0-01")
    child = prepare_task(client, admin, vid, "B0-02")
    parent_path = f"/api/v1/ventures/{vid}/tasks/{parent['id']}"
    child_path = f"/api/v1/ventures/{vid}/tasks/{child['id']}"
    completion = {"status": "完了", "evidenceUri": "https://example.test/evidence", "approveCompletion": True}
    premature = client.patch(child_path, headers=admin, json=completion)
    assert premature.status_code == 400 and premature.json()["detail"] == "前提未充足"
    assert client.patch(parent_path, headers=admin, json=completion).status_code == 200
    assert client.patch(child_path, headers=admin, json=completion).json()["completionValid"]
    cycle = client.patch(parent_path, headers=admin, json={"dependsOn": ["B0-02"], "dependencyChangeReason": "循環を作る誤操作"})
    assert cycle.status_code == 400 and "循環" in cycle.json()["detail"]
    assert client.patch(parent_path, headers=admin, json={"evidenceUri": "https://example.test/revised"}).status_code == 200
    after = next(r for r in client.get(f"/api/v1/ventures/{vid}/tasks", headers=admin).json()["items"] if r["id"] == child["id"])
    assert after["completionApprovedAt"] and not after["completionValid"]
    assert after["completionCheck"] == "前提未充足"
