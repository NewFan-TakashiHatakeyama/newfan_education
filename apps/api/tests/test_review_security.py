"""Regression tests for the all-implementation PdM P0/P1 counterexamples."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import builtins
import subprocess
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from main import app
from infrastructure.db import SessionLocal
from infrastructure.sql_models import UserModel, InviteModel, VentureSkillAssessmentModel, ApplicationRecordModel
from infrastructure.exercise_execution import ExerciseExecutionGateway
from infrastructure.settings import load_settings
from infrastructure.postgres_b2b import PostgresB2BRepository
from infrastructure.persistent_records import PersistentRecords, PersistentProgress
from domain.models import ConsentRecord, Goal, ProgressEvent


def login(client, email="admin@example.com", password="Admin123!"):
    r = client.post("/api/v1/auth/sign-in", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["accessToken"]}


def invite(client, admin, role="learner"):
    identity = "review-" + uuid4().hex[:12]
    email = identity + "@example.test"
    result = client.post("/api/v1/company/invites", headers=admin, json={"email": email, "role": role})
    assert result.status_code == 200, result.text
    return {"userId": identity, "email": email, "displayName": identity, "password": "ReviewTest123!",
            "invitationToken": result.json()["token"]}


def join(client, admin, role="learner"):
    payload = invite(client, admin, role)
    result = client.post("/api/v1/auth/sign-up", json=payload)
    assert result.status_code == 200, result.text
    return payload, {"Authorization": "Bearer " + result.json()["accessToken"]}


def project(client, admin):
    response = client.post("/api/v1/ventures", headers=admin, json={"name": "Review regression", "scale": "S"})
    assert response.status_code == 200, response.text
    return response.json()["id"]


def add(client, admin, vid, uid, role):
    return client.post(f"/api/v1/ventures/{vid}/members", headers=admin, json={"userId": uid, "roleId": role})


def ledger(client, actor, vid, key, values, existing=None, verify=False):
    payload = {"values": values, "verifyRecord": verify}
    if existing: payload.update(id=existing["id"], expectedRevision=existing["revision"])
    return client.post(f"/api/v1/ventures/{vid}/ledgers/{key}/entries", headers=actor, json=payload)


def test_r01_public_registration_cannot_choose_membership_or_privileges():
    with TestClient(app) as c:
        payload = {"userId": "attacker", "email": "attack@example.test", "password": "AttackTest123!", "displayName": "attack",
            "role": "admin", "tenantId": "company-demo"}
        assert c.post("/api/v1/auth/sign-up", json=payload).status_code == 403
        del payload["role"]; del payload["tenantId"]
        assert c.post("/api/v1/auth/sign-up", json=payload).status_code == 400


def test_r01_r17_invitation_email_expiry_reuse_and_candidates():
    with TestClient(app) as c:
        admin = login(c)
        payload = invite(c, admin, "mentor")
        wrong = c.post("/api/v1/auth/sign-up", json={**payload, "email": "wrong@example.test"})
        assert wrong.status_code == 400
        accepted = c.post("/api/v1/auth/sign-up", json=payload)
        assert accepted.status_code == 200 and accepted.json()["role"] == "mentor"
        assert c.post("/api/v1/auth/sign-up", json={**payload, "userId": "other", "email": "other@example.test"}).status_code == 400
        expired = invite(c, admin)
        with SessionLocal() as db:
            row = db.scalar(select(InviteModel).where(InviteModel.token == expired["invitationToken"]))
            row.created_at = datetime.now(timezone.utc) - timedelta(days=8)
            db.commit()
        assert c.post("/api/v1/auth/sign-up", json=expired).status_code == 400
        vid = project(c, admin)
        candidates = c.get(f"/api/v1/ventures/{vid}/member-candidates", headers=admin).json()["items"]
        assert any(x["id"] == payload["userId"] for x in candidates)
        assert add(c, admin, vid, payload["userId"], "R19").status_code == 200
        assert add(c, admin, vid, "does-not-exist", "R03").status_code == 400


def test_r02_r03_admin_updates_are_durable_and_revoke_all_tokens():
    with TestClient(app) as c:
        admin = login(c)
        person, old = join(c, admin, "recruiter")
        assert any(u["userId"] == person["userId"] for u in c.get("/api/v1/admin/users", headers=admin).json()["items"])
        path = "/api/v1/admin/users/" + person["userId"]
        assert c.patch(path, headers=admin, json={"state": "suspended"}).status_code == 200
        assert c.get("/api/v1/auth/me", headers=old).status_code == 401
        assert c.post("/api/v1/auth/sign-in", json={"email": person["email"], "password": person["password"]}).status_code == 401
        with SessionLocal() as db:
            assert db.get(UserModel, person["userId"]).state == "suspended"
        assert c.patch(path, headers=admin, json={"state": "active", "role": "learner"}).status_code == 200
        assert c.get("/api/v1/auth/me", headers=old).status_code == 401
        fresh = login(c, person["email"], person["password"])
        assert c.get("/api/v1/auth/me", headers=fresh).status_code == 200
        logs = c.get("/api/v1/admin/audit-logs", headers=admin, params={"resourceId": person["userId"]}).json()["items"]
        assert any(l["eventType"] == "admin.user.updated" for l in logs)


def test_r04_independent_role_cannot_be_self_assigned_or_combined():
    with TestClient(app) as c:
        admin = login(c); person, actor = join(c, admin, "recruiter")
        vid = project(c, actor)
        assert add(c, actor, vid, person["userId"], "R19").status_code == 403
        assert add(c, admin, vid, person["userId"], "R19").status_code == 403
        reviewer, reviewer_token = join(c, admin, "mentor")
        assert add(c, admin, vid, reviewer["userId"], "R19").status_code == 200
        assert add(c, admin, vid, reviewer["userId"], "R02").status_code == 403
        assert c.get(f"/api/v1/ventures/{vid}", headers=reviewer_token).json()["capabilities"]["canVerify"]


def test_r05_r06_r15_summary_privacy_and_immutable_assessment_expiry():
    with TestClient(app) as c:
        admin = login(c); vid = project(c, admin)
        person, actor = join(c, admin); other, other_actor = join(c, admin)
        assert add(c, admin, vid, person["userId"], "R03").status_code == 200
        assert add(c, admin, vid, other["userId"], "R03").status_code == 200
        skill = c.get(f"/api/v1/ventures/{vid}/skill-gap", headers=admin).json()["items"][0]["skillId"]
        payload = {"skillId": skill, "userId": person["userId"], "assessedLevel": 1,
            "dueDate": "2020-01-01", "evidenceUri": "https://example.test/proof", "developmentPlan": "PRIVATE PLAN"}
        path = f"/api/v1/ventures/{vid}/skill-assessments"
        one = c.post(path, headers=admin, json=payload)
        assert one.status_code == 200, one.text
        del payload["dueDate"]; payload["assessedLevel"] = 3
        two = c.post(path, headers=admin, json=payload)
        assert two.status_code == 200, two.text
        assert one.json()["id"] != two.json()["id"] and two.json()["dueDate"] == "2020-01-01"
        with SessionLocal() as db:
            assert db.get(VentureSkillAssessmentModel, one.json()["id"]).assessed_level == 1
        for suffix in ("summary", "skill-gap", "skill-assessments/history"):
            assert "PRIVATE PLAN" not in c.get(f"/api/v1/ventures/{vid}/{suffix}", headers=other_actor).text
        history = c.get(f"/api/v1/ventures/{vid}/skill-assessments/history", headers=actor).json()["items"]
        assert len(history) == 2
        cancelled = c.post(path, headers=admin, json={**payload, "revoked": True, "developmentPlan": "評価証拠の誤りによる取消"})
        assert cancelled.status_code == 200 and cancelled.json()["revoked"]
        assert cancelled.json()["supersedesId"] == two.json()["id"]
        assert c.get(f"/api/v1/ventures/{vid}/skill-assessments/history", headers=actor).json()["items"][0]["revoked"]


def test_r07_r08_submissions_are_private_and_keyword_code_cannot_pass():
    with TestClient(app) as c:
        admin = login(c); person, actor = join(c, admin); _, other = join(c, admin)
        exercises = c.get("/api/v1/exercises", headers=actor).json()["items"]
        sub = c.post(f"/api/v1/exercises/{exercises[0]['id']}/submit", headers=actor, json={"code": "# return select\nraise Exception('fail')"})
        assert sub.status_code == 200, sub.text
        sid = sub.json()["id"]
        assert c.get(f"/api/v1/submissions/{sid}", headers=other).status_code == 403
        assert c.post(f"/api/v1/submissions/{sid}/ai-review", headers=other).status_code == 403
        assert c.post(f"/api/v1/submissions/{sid}/ai-review", headers=actor).status_code == 503
        assert not c.get("/api/v1/evidence", headers=actor).json()["items"]


@pytest.mark.parametrize("kind", ["notebook", "sql", "rag", "ocr"])
def test_r13_no_host_execution_even_when_sandbox_configuration_changes(kind, monkeypatch, tmp_path):
    marker = tmp_path / "must-not-exist"
    def forbidden(*args, **kwargs): raise AssertionError("Host subprocess invoked")
    monkeypatch.setattr(subprocess, "run", forbidden)
    result = ExerciseExecutionGateway(load_settings()).run({"kind": kind}, f"open({str(marker)!r}, 'w').write('executed')")
    assert result.engine == "unavailable" and result.details["executed"] is False
    assert not marker.exists()


def test_r12_stale_and_missing_revisions_cannot_overwrite():
    with TestClient(app) as c:
        admin = login(c); vid = project(c, admin)
        one = ledger(c, admin, vid, "data", {"名称・種類": "original"}).json()
        first = ledger(c, admin, vid, "data", {"名称・種類": "first writer"}, one)
        assert first.status_code == 200, first.text
        stale = ledger(c, admin, vid, "data", {"名称・種類": "stale"}, one)
        assert stale.status_code == 409
        missing = c.post(f"/api/v1/ventures/{vid}/ledgers/data/entries", headers=admin, json={"id": one["id"], "values": {"名称・種類": "missing"}})
        assert missing.status_code == 409


def test_r09_r19_reports_persist_sources_and_exports_are_real():
    with TestClient(app) as c:
        admin = login(c)
        assert c.get("/api/v1/reports/unknown", headers=admin).status_code == 404
        assert c.post("/api/v1/reports/unknown/export", headers=admin, json={"reportFormat": "pdf"}).status_code == 404
        requirement = c.post("/api/v1/requirements", headers=admin, json={"title": "Unrelated", "description": "No verified skill", "requiredSkills": ["unique-unverified-skill"]}).json()
        assessment = c.post(f"/api/v1/requirements/{requirement['id']}/assess", headers=admin)
        assert assessment.status_code == 200, assessment.text
        assert assessment.json()["fitScore"] == 0 and assessment.json()["matchedSkills"] == []
        report = c.post("/api/v1/reports/sales-summary", headers=admin, json={"requirementId": requirement["id"], "learnerId": "demo-user"})
        assert report.status_code == 200, report.text
        rid = report.json()["id"]
        assert c.get(f"/api/v1/reports/{rid}", headers=admin).json() == report.json()
        assert "第三者確認済み技能: なし" in report.json()["summary"]
        for fmt in ("pdf", "csv"):
            export = c.post(f"/api/v1/reports/{rid}/export", headers=admin, json={"reportFormat": fmt})
            assert export.status_code == 200, export.text
            downloaded = c.get(export.json()["resultUrl"], headers=admin)
            assert downloaded.status_code == 200
            assert downloaded.content.startswith(b"%PDF-" if fmt == "pdf" else b"\xef\xbb\xbf")


def test_r18_records_survive_new_database_sessions_and_progress_is_idempotent():
    uid = "persistence-" + uuid4().hex
    with SessionLocal() as db:
        record = PersistentRecords(db, "consent-test", ConsentRecord).save(ConsentRecord(user_id=uid, consent_type="career_profile", granted=True))
        event = ProgressEvent(user_id=uid, roadmap_id="roadmap", roadmap_item_id="item", event_type="lesson_completed", idempotency_key="same")
        assert PersistentProgress(db, "progress-test", ProgressEvent).save(event)
    with SessionLocal() as db:
        assert PersistentRecords(db, "consent-test", ConsentRecord).get(record.id).granted
        repo = PersistentProgress(db, "progress-test", ProgressEvent)
        assert repo.save(event) is None
        assert len(repo.list_by_user(uid)) == 1
    # A separate interpreter imports and reads the same durable record.
    import sys
    script = "from infrastructure.db import SessionLocal; from infrastructure.sql_models import ApplicationRecordModel; " \
        + f"db=SessionLocal(); assert db.get(ApplicationRecordModel, ('consent-test', {record.id!r})).payload['granted']; db.close()"
    import os
    env = {**os.environ, "PYTHONPATH": str(__import__('pathlib').Path(__file__).parents[1] / 'src')}
    subprocess.run([sys.executable, "-c", script], env=env, check=True, capture_output=True, timeout=30)


def test_r20_only_real_inbox_delivery_is_reported():
    with SessionLocal() as db:
        repo = PostgresB2BRepository(db)
        args = dict(tenant_id="company-demo", user_id="demo-user", category="learning", title="Notification test", body="body", target_url="/notifications")
        with pytest.raises(ValueError): repo.enqueue_notification_job(**args, channels=["email", "push"])
        job = repo.enqueue_notification_job(**args, channels=["in_app"])
        assert job["status"] == "completed"
        assert any(n["id"] == job["id"] for n in repo.list_notifications(tenant_id="company-demo", user_id="demo-user")["items"])


def test_r14_condition_resolution_requires_independent_real_current_confirmation():
    with TestClient(app) as c:
        admin = login(c); vid = project(c, admin)
        owner, owner_token = join(c, admin); reviewer, reviewer_token = join(c, admin, "mentor")
        assert add(c, admin, vid, owner["userId"], "R03").status_code == 200
        assert add(c, admin, vid, reviewer["userId"], "R19").status_code == 200
        gate = ledger(c, admin, vid, "gate_run", {"Gate": "G0"})
        assert gate.status_code == 200
        today = datetime.now(timezone.utc).date().isoformat()
        values = {"GateRun ID": gate.json()["rowKey"], "条件・制約": "検証完了まで提供制限",
            "Owner PersonID": owner["userId"], "期限": today, "状態": "未解消"}
        assert ledger(c, owner_token, vid, "condition", {**values, "GateRun ID": "fake"}).status_code == 400
        condition = ledger(c, owner_token, vid, "condition", values)
        assert condition.status_code == 200, condition.text
        resolved = {"状態": "解消", "解消日": today, "解消証拠URI": "https://example.test/resolved"}
        assert ledger(c, owner_token, vid, "condition", resolved, condition.json()).status_code == 403
        assert ledger(c, reviewer_token, vid, "condition", {**resolved, "確認者PersonID": "fake"}, condition.json(), True).status_code == 403
        assert ledger(c, reviewer_token, vid, "condition", {**resolved, "解消日": "2099-01-01"}, condition.json(), True).status_code == 400
        confirmed = ledger(c, reviewer_token, vid, "condition", resolved, condition.json(), True)
        assert confirmed.status_code == 200, confirmed.text
        assert confirmed.json()["derived"]["条件点検"] == "解消確認済"
        assert confirmed.json()["values"]["確認者PersonID"] == reviewer["userId"]
        assert ledger(c, admin, vid, "condition", {"解消証拠URI": "changed"}, confirmed.json()).status_code == 400


def test_r16_capacity_is_shared_across_projects_and_support_expiry_is_checked():
    from infrastructure.venture_master import load_master
    with TestClient(app) as c:
        admin = login(c); person, _ = join(c, admin); supporter, _ = join(c, admin)
        vid = project(c, admin); second = project(c, admin)
        link = load_master().task_skills[0]
        task_id, skill_id, roles = link["task_id"], link["skill_id"], link["exec_role_ids"]
        today = datetime.now(timezone.utc).date()
        start, end = today.isoformat(), (today + timedelta(days=30)).isoformat()
        tasks = c.get(f"/api/v1/ventures/{vid}/tasks", headers=admin).json()["items"]
        assert c.post(f"/api/v1/ventures/{vid}/tasks/applicability", headers=admin, json={
            "taskRowIds": [r["id"] for r in tasks if r["taskId"] != task_id], "applicability": "対象外", "reason": "対象を限定"}).status_code == 200
        for role in roles:
            assert add(c, admin, vid, person["userId"], role).status_code == 200
            assert add(c, admin, vid, supporter["userId"], role).status_code == 200
        assessment = c.post(f"/api/v1/ventures/{vid}/skill-assessments", headers=admin, json={
            "skillId": skill_id, "userId": person["userId"], "assessedLevel": 3, "evidenceUri": "https://example.test/skills"}).json()
        allocations = []
        for role in roles:
            r = ledger(c, admin, vid, "assignment", {"Task ID": task_id, "Skill ID": skill_id, "Role ID": role,
                "必要Lv": str(link["required_level"]), "PersonID": person["userId"], "能力評価記録ID": assessment["id"],
                "必要性・担当範囲": "担当", "割当承認者": "admin-user", "承認日": start,
                "対象期間": "検証期間", "対象開始": start, "対象終了": end})
            assert r.status_code == 200, r.text
            allocations.append(r.json())
        def gap():
            return next(r["gap"] for r in c.get(f"/api/v1/ventures/{vid}/skill-gap", headers=admin).json()["items"] if r["skillId"] == skill_id)
        staffing = {"PersonID": person["userId"], "配置開始": start, "配置終了": end, "割当FTE（入力）": "0.6", "当人の当日上限FTE": "1"}
        assert ledger(c, admin, vid, "role_staffing", staffing).status_code == 200
        assert gap() == 0
        overlap = ledger(c, admin, second, "role_staffing", staffing)
        assert overlap.status_code == 200 and gap() > 0
        assert ledger(c, admin, second, "role_staffing", {"配置開始": "2020-01-01", "配置終了": "2020-12-31"}, overlap.json()).status_code == 200
        assert gap() == 0
        c.post(f"/api/v1/ventures/{vid}/skill-assessments", headers=admin, json={"skillId": skill_id,
            "userId": person["userId"], "assessedLevel": 0, "evidenceUri": "https://example.test/revised"})
        c.post(f"/api/v1/ventures/{vid}/skill-assessments", headers=admin, json={"skillId": skill_id,
            "userId": supporter["userId"], "assessedLevel": 3, "dueDate": "2020-12-31", "evidenceUri": "https://example.test/expired"})
        assert ledger(c, admin, vid, "role_staffing", {**staffing, "PersonID": supporter["userId"], "割当FTE（入力）": "0.2"}).status_code == 200
        for allocation in allocations:
            assert ledger(c, admin, vid, "assignment", {"支援者PersonID": supporter["userId"], "支援方法": "同行", "支援証拠URI": "https://example.test/support"}, allocation).status_code == 200
        assert gap() > 0  # Expired support cannot make the current assignment adequate.


def test_migration_preserves_history_but_invalidates_unverified_legacy_authority(tmp_path):
    import importlib.util
    from pathlib import Path
    from sqlalchemy import create_engine, text
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from infrastructure.db import Base
    from infrastructure.sql_models import VentureModel, VentureMemberModel
    engine = create_engine("sqlite:///" + (tmp_path / "migration.db").as_posix())
    Base.metadata.create_all(engine)
    path = Path(__file__).parents[1] / "migrations/versions/20260911_0005_review_security.py"
    spec = importlib.util.spec_from_file_location("review_migration", path)
    migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
    with engine.begin() as db:
        db.execute(UserModel.__table__.insert().values(user_id="legacy", email="legacy@example.test", display_name="legacy",
            role="admin", tenant_id="t", password_hash="not-used"))
        db.execute(VentureModel.__table__.insert().values(id="v", tenant_id="t", name="legacy", created_by="legacy", governance={"riskConfirmed": True}))
        db.execute(VentureSkillAssessmentModel.__table__.insert().values(id="old-assessment", venture_id="v", tenant_id="t", skill_id="S001", user_id="legacy", assessed_level=2))
        db.execute(text("ALTER TABLE users DROP COLUMN session_version"))
        db.execute(text("ALTER TABLE venture_members DROP COLUMN appointed_by"))
        db.execute(text("ALTER TABLE venture_skill_assessments DROP COLUMN supersedes_id"))
        db.execute(text("ALTER TABLE venture_skill_assessments DROP COLUMN revoked"))
        db.execute(text("DROP TABLE application_records"))
        db.execute(text("DROP INDEX ix_venture_skill_user"))
        db.execute(text("CREATE UNIQUE INDEX ux_venture_skill_user ON venture_skill_assessments (venture_id, skill_id, user_id)"))
        with Operations.context(MigrationContext.configure(db)):
            migration.upgrade()
        assert db.execute(select(UserModel.session_version)).scalar() == 1
        assert db.execute(select(VentureSkillAssessmentModel.assessed_level)).scalar() == 2
        assert db.execute(select(VentureModel.governance)).scalar()["riskConfirmed"] is False
        db.execute(VentureSkillAssessmentModel.__table__.insert().values(id="new-assessment", venture_id="v", tenant_id="t", skill_id="S001", user_id="legacy", assessed_level=3))
        assert len(db.execute(select(VentureSkillAssessmentModel.id)).all()) == 2
    engine.dispose()


def test_alembic_fresh_database_upgrade(tmp_path):
    import sys, os
    from pathlib import Path
    env = {**os.environ, "DATABASE_URL": "sqlite:///" + (tmp_path / "fresh.db").as_posix()}
    completed = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=Path(__file__).parents[1], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    assert completed.returncode == 0, completed.stderr
