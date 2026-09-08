"""事業PJ台帳のAPIテスト。

工程マスタ（132タスク・6ゲート）から案件台帳が生成され、適用判定・進捗・ゲート承認・
汎用台帳・スキルギャップが期待どおり動くことを確認する。
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from sqlalchemy import select

from infrastructure.db import ScopedSession
from infrastructure.sql_models import AuditLogModel
from main import app


def sign_in(client: TestClient, email: str, password: str) -> dict[str, str]:
    res = client.post("/api/v1/auth/sign-in", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['accessToken']}"}


def create_venture(client: TestClient, headers: dict[str, str], **overrides) -> dict:
    payload = {
        "name": "現場報告要約AI",
        "summary": "現場の日報を要約し、翌日の指示に落とす",
        "offeringType": "社内事業",
        "scale": "S",
        "riskTier": "T1",
        "conditions": {"RAG": "適用", "Agent": "対象外"},
    }
    payload.update(overrides)
    res = client.post("/api/v1/ventures", json=payload, headers=headers)
    assert res.status_code == 200, res.text
    return res.json()


def test_master_exposes_process_definition() -> None:
    client = TestClient(app)
    headers = sign_in(client, "learner@example.com", "Learner123!")

    res = client.get("/api/v1/ventures/master", headers=headers)
    assert res.status_code == 200
    master = res.json()
    assert master["taskCount"] == 132
    assert master["skillCount"] == 106
    assert [phase["phaseId"] for phase in master["phases"]] == ["B0", "B1", "B2", "B3", "B4", "B5", "B6"]
    assert [gate["gateId"] for gate in master["gates"]] == ["G0", "G1", "G2", "G3", "G4", "G5"]
    # ゲートごとに選べる判断は原本の定義マスターに従う
    g3 = next(gate for gate in master["gates"] if gate["gateId"] == "G3")
    assert "承認" in g3["allowedDecisions"]
    assert "Pivot" not in g3["allowedDecisions"]
    assert "RAG" in master["conditionKeys"]
    assert {ledger["key"] for ledger in master["ledgers"]} >= {"data", "risk", "kpi", "adr"}


def test_master_tasks_and_skills_are_readable_by_learner() -> None:
    client = TestClient(app)
    headers = sign_in(client, "learner@example.com", "Learner123!")

    tasks = client.get("/api/v1/ventures/master/tasks", params={"phaseId": "B0"}, headers=headers)
    assert tasks.status_code == 200
    items = tasks.json()["items"]
    assert len(items) == 18
    assert items[0]["taskId"] == "B0-01"

    skills = client.get("/api/v1/ventures/master/skills", headers=headers)
    assert skills.status_code == 200
    assert len(skills.json()["items"]) == 106


def test_create_venture_instantiates_task_and_gate_ledger() -> None:
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture = create_venture(client, admin)

    assert venture["taskTotal"] == 132
    assert venture["status"] == "計画中"

    tasks = client.get(f"/api/v1/ventures/{venture['id']}/tasks", headers=admin).json()["items"]
    assert len(tasks) == 132

    # 適用条件「全」のタスクは自動で適用になる
    always = next(task for task in tasks if task["taskId"] == "B0-01")
    assert always["applicabilityCondition"] == "全"
    assert always["applicability"] == "適用"

    # 条件:RAG は「適用」と宣言したので適用、条件:Agent は対象外
    rag_task = next(task for task in tasks if task["applicabilityCondition"] == "条件:RAG")
    assert rag_task["applicability"] == "適用"
    agent_task = next(task for task in tasks if task["applicabilityCondition"] == "条件:Agent")
    assert agent_task["applicability"] == "対象外"

    # 未宣言の条件は未判定のまま人の判断を待つ
    undecided = [task for task in tasks if task["applicability"] == "未判定"]
    assert undecided, "未判定のタスクが残るべき"

    gates = client.get(f"/api/v1/ventures/{venture['id']}/gates", headers=admin).json()["items"]
    assert [gate["gateId"] for gate in gates] == ["G0", "G1", "G2", "G3", "G4", "G5"]
    assert all(gate["decision"] == "未審査" for gate in gates)


def test_conditions_update_refreshes_only_undecided_tasks() -> None:
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture = create_venture(client, admin, conditions={"Agent": "対象外"})
    venture_id = venture["id"]

    tasks = client.get(f"/api/v1/ventures/{venture_id}/tasks", headers=admin).json()["items"]
    agent_task = next(task for task in tasks if task["applicabilityCondition"] == "条件:Agent")

    # 人が明示的に「適用」と決めた行は、条件変更で上書きしない
    decided = client.patch(
        f"/api/v1/ventures/{venture_id}/tasks/{agent_task['id']}",
        json={"applicability": "適用", "applicabilityReason": "限定的にAgentを試す"},
        headers=admin,
    )
    assert decided.status_code == 200
    assert decided.json()["applicabilityDecidedBy"] == "admin-user"

    updated = client.patch(
        f"/api/v1/ventures/{venture_id}",
        json={"conditions": {"Agent": "対象外"}},
        headers=admin,
    )
    assert updated.status_code == 200

    tasks = client.get(f"/api/v1/ventures/{venture_id}/tasks", headers=admin).json()["items"]
    still_applied = next(task for task in tasks if task["id"] == agent_task["id"])
    assert still_applied["applicability"] == "適用"


def test_bulk_applicability_decision() -> None:
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture = create_venture(client, admin)
    venture_id = venture["id"]

    tasks = client.get(
        f"/api/v1/ventures/{venture_id}/tasks", params={"applicability": "未判定"}, headers=admin
    ).json()["items"]
    target_ids = [task["id"] for task in tasks[:3]]

    res = client.post(
        f"/api/v1/ventures/{venture_id}/tasks/applicability",
        json={"taskRowIds": target_ids, "applicability": "対象外", "reason": "本フェーズでは扱わない"},
        headers=admin,
    )
    assert res.status_code == 200
    assert res.json()["updated"] == 3

    after = client.get(f"/api/v1/ventures/{venture_id}/tasks", headers=admin).json()["items"]
    decided = [task for task in after if task["id"] in target_ids]
    assert all(task["applicability"] == "対象外" for task in decided)
    assert all(task["applicabilityReason"] == "本フェーズでは扱わない" for task in decided)


def test_learner_can_only_update_own_assigned_task() -> None:
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    learner = sign_in(client, "learner@example.com", "Learner123!")
    venture = create_venture(client, admin)
    venture_id = venture["id"]

    tasks = client.get(f"/api/v1/ventures/{venture_id}/tasks", headers=admin).json()["items"]
    task = tasks[0]

    # 要員に入っていないうちは案件の存在自体が見えない
    assert (
        client.patch(
            f"/api/v1/ventures/{venture_id}/tasks/{task['id']}", json={"status": "進行中"}, headers=learner
        ).status_code
        == 404
    )
    added = client.post(
        f"/api/v1/ventures/{venture_id}/members",
        json={"userId": "demo-user", "roleId": "R02"},
        headers=admin,
    )
    assert added.status_code == 200

    # 未割当のうちは学習者は更新できない
    denied = client.patch(
        f"/api/v1/ventures/{venture_id}/tasks/{task['id']}", json={"status": "進行中"}, headers=learner
    )
    assert denied.status_code == 403

    assigned = client.patch(
        f"/api/v1/ventures/{venture_id}/tasks/{task['id']}",
        json={"assigneeUserId": "demo-user", "plannedStart": "2026-10-01"},
        headers=admin,
    )
    assert assigned.status_code == 200
    assert assigned.json()["assigneeUserId"] == "demo-user"

    progressed = client.patch(
        f"/api/v1/ventures/{venture_id}/tasks/{task['id']}",
        json={"status": "進行中", "evidenceUri": "https://example.test/issue/1"},
        headers=learner,
    )
    assert progressed.status_code == 200
    assert progressed.json()["status"] == "進行中"

    # 担当者は適用判定や担当変更はできない
    rejected = client.patch(
        f"/api/v1/ventures/{venture_id}/tasks/{task['id']}",
        json={"applicability": "対象外"},
        headers=learner,
    )
    assert rejected.status_code == 403


def test_gate_decision_is_restricted_to_allowed_values() -> None:
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture = create_venture(client, admin)
    venture_id = venture["id"]

    gates = client.get(f"/api/v1/ventures/{venture_id}/gates", headers=admin).json()["items"]
    g3 = next(gate for gate in gates if gate["gateId"] == "G3")

    # G3 に Pivot は定義されていない
    invalid = client.patch(
        f"/api/v1/ventures/{venture_id}/gates/{g3['id']}", json={"decision": "Pivot"}, headers=admin
    )
    assert invalid.status_code == 400

    approved = client.patch(
        f"/api/v1/ventures/{venture_id}/gates/{g3['id']}",
        json={
            "decision": "条件付承認",
            "conditions": "重大リスクの残件を2週間で解消",
            "conditionDue": "2026-10-15",
            "evidencePackageUri": "https://example.test/gate/g3",
        },
        headers=admin,
    )
    assert approved.status_code == 200
    body = approved.json()
    assert body["decision"] == "条件付承認"
    assert body["decidedBy"] == "admin-user"
    assert body["decidedAt"]


def test_ledger_entries_seed_master_rows_and_accept_input() -> None:
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture = create_venture(client, admin)
    venture_id = venture["id"]

    risk = client.get(f"/api/v1/ventures/{venture_id}/ledgers/risk", headers=admin)
    assert risk.status_code == 200
    body = risk.json()
    assert body["ledger"]["name"] == "リスク・セキュリティ・例外"
    assert len(body["items"]) == 12
    first = body["items"][0]
    assert first["isMasterRow"] is True
    assert first["rowKey"] == "RS01"
    assert first["master"]["仮説/事象"]

    saved = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/risk/entries",
        json={
            "id": first["id"],
            "status": "対応中",
            "values": {"案件での該当": "該当", "残存リスク": "支払意思の検証が未了"},
        },
        headers=admin,
    )
    assert saved.status_code == 200
    assert saved.json()["values"]["案件での該当"] == "該当"
    assert saved.json()["status"] == "対応中"

    # 点検行は削除できない
    blocked = client.delete(
        f"/api/v1/ventures/{venture_id}/ledgers/risk/entries/{first['id']}", headers=admin
    )
    assert blocked.status_code == 400

    # 行を起票できる台帳（データ台帳）は自由に追加・削除できる
    # 原本の入力規則にない語彙は受け付けない（個人情報区分は6つの候補のみ）
    invalid = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/data/entries",
        json={"rowKey": "D-000", "values": {"個人情報区分": "個人情報を含む"}},
        headers=admin,
    )
    assert invalid.status_code == 400
    assert "個人情報区分" in invalid.json()["detail"]

    created = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/data/entries",
        json={"rowKey": "D-001", "values": {"名称・種類": "日報テキスト", "個人情報区分": "個人情報"}},
        headers=admin,
    )
    assert created.status_code == 200
    entry_id = created.json()["id"]
    assert created.json()["values"]["名称・種類"] == "日報テキスト"

    removed = client.delete(
        f"/api/v1/ventures/{venture_id}/ledgers/data/entries/{entry_id}", headers=admin
    )
    assert removed.status_code == 200


def test_unknown_ledger_columns_are_rejected() -> None:
    """原本にない列は黙って捨てず拒否する（IT03 数式列への上書き拒否）。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture = create_venture(client, admin)
    venture_id = venture["id"]

    rejected = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/data/entries",
        json={"rowKey": "D-900", "values": {"名称・種類": "OK", "存在しない列": "NG"}},
        headers=admin,
    )
    assert rejected.status_code == 400
    assert "存在しない列" in rejected.json()["detail"]

    created = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/data/entries",
        json={"rowKey": "D-900", "values": {"名称・種類": "OK"}},
        headers=admin,
    )
    assert created.status_code == 200
    assert created.json()["values"] == {"名称・種類": "OK"}

    # 原本が数式で埋める列も入力列ではないので拒否する
    denied = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/incident/entries",
        json={"rowKey": "INC-900", "values": {"検知→復旧h": "3"}},
        headers=admin,
    )
    assert denied.status_code == 400


def test_skill_gap_reflects_applied_tasks_and_assessments() -> None:
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture = create_venture(client, admin)
    venture_id = venture["id"]

    gap = client.get(f"/api/v1/ventures/{venture_id}/skill-gap", headers=admin)
    assert gap.status_code == 200
    body = gap.json()
    assert body["appliedTaskCount"] > 0
    assert body["items"], "適用タスクからスキル需要が算出されること"
    target = body["items"][0]
    assert target["requiredLevel"] >= 1
    assert target["coveredLevel"] == 0
    assert target["gap"] == target["requiredLevel"]

    # 評価できるのは案件の要員だけ
    assert client.post(
        f"/api/v1/ventures/{venture_id}/skill-assessments",
        json={"skillId": target["skillId"], "userId": "demo-user", "assessedLevel": 1},
        headers=admin,
    ).status_code == 400
    client.post(
        f"/api/v1/ventures/{venture_id}/members",
        json={"userId": "demo-user", "roleId": "R02"},
        headers=admin,
    )

    saved = client.post(
        f"/api/v1/ventures/{venture_id}/skill-assessments",
        json={
            "skillId": target["skillId"],
            "userId": "demo-user",
            "assessedLevel": target["requiredLevel"],
            "developmentPlan": "実案件でのOJT",
        },
        headers=admin,
    )
    assert saved.status_code == 200

    after = client.get(f"/api/v1/ventures/{venture_id}/skill-gap", headers=admin).json()
    updated = next(item for item in after["items"] if item["skillId"] == target["skillId"])
    assert updated["coveredLevel"] == target["requiredLevel"]
    assert updated["gap"] == 0
    assert updated["assessments"][0]["userName"]


def test_summary_aggregates_phases_gates_and_ledgers() -> None:
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture = create_venture(client, admin)
    venture_id = venture["id"]

    client.post(
        f"/api/v1/ventures/{venture_id}/members",
        json={"userId": "demo-user", "roleId": "R02", "allocationNote": "0.5FTE"},
        headers=admin,
    )

    summary = client.get(f"/api/v1/ventures/{venture_id}/summary", headers=admin)
    assert summary.status_code == 200
    body = summary.json()
    assert body["venture"]["id"] == venture_id
    assert len(body["phases"]) == 7
    assert sum(phase["total"] for phase in body["phases"]) == 132
    assert len(body["gates"]) == 6
    assert len(body["ledgers"]) == 25
    assert body["members"][0]["roleName"]
    assert body["skillGapCount"] > 0


def test_learner_cannot_create_venture() -> None:
    client = TestClient(app)
    learner = sign_in(client, "learner@example.com", "Learner123!")
    res = client.post("/api/v1/ventures", json={"name": "勝手に作る"}, headers=learner)
    assert res.status_code == 403


def test_invalid_master_reference_is_rejected() -> None:
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")

    bad_tier = client.post(
        "/api/v1/ventures", json={"name": "Tier不正", "riskTier": "T9"}, headers=admin
    )
    assert bad_tier.status_code == 400

    bad_condition = client.post(
        "/api/v1/ventures",
        json={"name": "条件不正", "conditions": {"存在しない条件": "適用"}},
        headers=admin,
    )
    assert bad_condition.status_code == 400


# ── 敵対的レビューで確定した5件の回帰テスト ────────────────


def test_duplicate_ledger_row_key_is_rejected_without_breaking_the_session() -> None:
    """行IDの重複は400で返り、DBセッションを壊さない。

    以前は IntegrityError が素通りし、共有Sessionが壊れて以後の全リクエストが
    500になっていた。
    """
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = create_venture(client, admin)["id"]

    first = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/data/entries",
        json={"rowKey": "D-001", "values": {}},
        headers=admin,
    )
    assert first.status_code == 200

    duplicated = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/data/entries",
        json={"rowKey": "D-001", "values": {}},
        headers=admin,
    )
    assert duplicated.status_code == 400
    assert "D-001" in duplicated.json()["detail"]

    # 失敗の後も他の機能が生きている
    assert client.get("/api/v1/ventures", headers=admin).status_code == 200
    assert client.post(
        "/api/v1/auth/sign-in", json={"email": "admin@example.com", "password": "Admin123!"}
    ).status_code == 200
    entries = client.get(f"/api/v1/ventures/{venture_id}/ledgers/data", headers=admin).json()["items"]
    assert [entry["rowKey"] for entry in entries] == ["D-001"]


def test_master_row_key_cannot_be_reused_by_a_new_row() -> None:
    """点検行と同じIDでの起票も400で弾く。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = create_venture(client, admin)["id"]

    conflict = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/risk/entries",
        json={"rowKey": "RS01", "values": {}},
        headers=admin,
    )
    assert conflict.status_code == 400
    assert client.get(f"/api/v1/ventures/{venture_id}/ledgers/risk", headers=admin).status_code == 200


def test_concurrent_venture_creation_all_succeed() -> None:
    """同時に案件を登録しても全部成功する（Sessionがリクエストごとに分かれている）。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")

    def create(index: int):
        return client.post(
            "/api/v1/ventures",
            json={"name": f"並行案件{index}", "scale": "S", "riskTier": "T1", "conditions": {}},
            headers=admin,
        )

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(create, range(6)))

    assert [res.status_code for res in results] == [200] * 6
    assert len({res.json()["id"] for res in results}) == 6


def test_ledger_key_must_match_the_row_on_write_and_delete() -> None:
    """別台帳のURLで行を書き換えたり消したりできない。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = create_venture(client, admin)["id"]

    created = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/data/entries",
        json={"rowKey": "MY-DATA", "values": {}},
        headers=admin,
    ).json()

    # data の行を risk のURLで更新しようとしても書き込まれない
    mismatched = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/risk/entries",
        json={"id": created["id"], "status": "完了"},
        headers=admin,
    )
    assert mismatched.status_code == 404
    after = client.get(f"/api/v1/ventures/{venture_id}/ledgers/data", headers=admin).json()["items"]
    assert next(item for item in after if item["id"] == created["id"])["status"] == "未着手"

    # data の行を risk のURLでは消せない
    assert (
        client.delete(
            f"/api/v1/ventures/{venture_id}/ledgers/risk/entries/{created['id']}", headers=admin
        ).status_code
        == 404
    )
    assert any(item["id"] == created["id"] for item in
               client.get(f"/api/v1/ventures/{venture_id}/ledgers/data", headers=admin).json()["items"])

    # 自分の台帳からは消せる
    assert (
        client.delete(
            f"/api/v1/ventures/{venture_id}/ledgers/data/entries/{created['id']}", headers=admin
        ).status_code
        == 200
    )


def test_venture_is_hidden_from_users_who_are_not_assigned() -> None:
    """要員に入っていない利用者には案件が見えない。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    learner = sign_in(client, "learner@example.com", "Learner123!")
    venture_id = create_venture(client, admin)["id"]

    listed = [item["id"] for item in client.get("/api/v1/ventures", headers=learner).json()["items"]]
    assert venture_id not in listed
    for path in ("", "/summary", "/tasks", "/gates", "/members", "/skill-gap", "/ledgers/data"):
        assert client.get(f"/api/v1/ventures/{venture_id}{path}", headers=learner).status_code == 404

    client.post(
        f"/api/v1/ventures/{venture_id}/members",
        json={"userId": "demo-user", "roleId": "R02"},
        headers=admin,
    )
    listed = [item["id"] for item in client.get("/api/v1/ventures", headers=learner).json()["items"]]
    assert venture_id in listed
    assert client.get(f"/api/v1/ventures/{venture_id}/tasks", headers=learner).status_code == 200

    # 工程マスタは案件と無関係に誰でも読める
    assert client.get("/api/v1/ventures/master", headers=learner).status_code == 200


def test_other_members_skill_assessments_are_hidden_from_learners() -> None:
    """個人別の到達Lvと育成計画は本人と評価者だけに見せる。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    learner = sign_in(client, "learner@example.com", "Learner123!")
    venture_id = create_venture(client, admin)["id"]
    for user_id in ("demo-user", "mentor-user"):
        client.post(
            f"/api/v1/ventures/{venture_id}/members",
            json={"userId": user_id, "roleId": "R02"},
            headers=admin,
        )

    gap = client.get(f"/api/v1/ventures/{venture_id}/skill-gap", headers=admin).json()
    skill_id = gap["items"][0]["skillId"]
    client.post(
        f"/api/v1/ventures/{venture_id}/skill-assessments",
        json={
            "skillId": skill_id,
            "userId": "mentor-user",
            "assessedLevel": 3,
            "developmentPlan": "本人には未共有の評価",
        },
        headers=admin,
    )

    as_learner = client.get(f"/api/v1/ventures/{venture_id}/skill-gap", headers=learner).json()
    row = next(item for item in as_learner["items"] if item["skillId"] == skill_id)
    assert row["assessments"] == []
    # 集計そのものは見える
    assert row["coveredLevel"] == 3

    as_admin = client.get(f"/api/v1/ventures/{venture_id}/skill-gap", headers=admin).json()
    row = next(item for item in as_admin["items"] if item["skillId"] == skill_id)
    assert [item["userId"] for item in row["assessments"]] == ["mentor-user"]


def test_gate_decision_history_survives_a_revert() -> None:
    """「未審査」に戻しても、誰がいつ承認したかが監査ログに残る。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = create_venture(client, admin)["id"]
    gates = client.get(f"/api/v1/ventures/{venture_id}/gates", headers=admin).json()["items"]
    g3 = next(gate for gate in gates if gate["gateId"] == "G3")

    approved = client.patch(
        f"/api/v1/ventures/{venture_id}/gates/{g3['id']}",
        json={"decision": "承認", "decidedByName": "山田太郎"},
        headers=admin,
    )
    assert approved.status_code == 200
    reverted = client.patch(
        f"/api/v1/ventures/{venture_id}/gates/{g3['id']}", json={"decision": "未審査"}, headers=admin
    )
    assert reverted.status_code == 200
    assert reverted.json()["decidedAt"] is None

    ScopedSession.remove()
    logs = (
        ScopedSession.execute(
            select(AuditLogModel)
            .where(AuditLogModel.resource_id == g3["id"])
            .order_by(AuditLogModel.occurred_at)
        )
        .scalars()
        .all()
    )
    actions = [log.action for log in logs]
    assert "承認" in actions and "未審査" in actions
    approval = next(log for log in logs if log.action == "承認")
    assert approval.actor_user_id == "admin-user"
    assert approval.event_type == "venture.gate.decision"
    revert = next(log for log in logs if log.action == "未審査")
    assert revert.metadata_json["previousDecision"] == "承認"
    assert revert.metadata_json["previousDecidedBy"] == "admin-user"
    ScopedSession.remove()


def test_completion_approval_is_recorded_in_the_audit_log() -> None:
    """完了承認の取り消しも痕跡を残す。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = create_venture(client, admin)["id"]
    task = client.get(f"/api/v1/ventures/{venture_id}/tasks", headers=admin).json()["items"][0]

    approved = client.patch(
        f"/api/v1/ventures/{venture_id}/tasks/{task['id']}",
        json={
            "approveCompletion": True,
            "status": "完了",
            "evidenceUri": "https://example.test/evidence/1",
        },
        headers=admin,
    )
    assert approved.status_code == 200, approved.text
    client.patch(
        f"/api/v1/ventures/{venture_id}/tasks/{task['id']}",
        json={"approveCompletion": False},
        headers=admin,
    )

    ScopedSession.remove()
    logs = (
        ScopedSession.execute(
            select(AuditLogModel).where(AuditLogModel.resource_id == task["id"])
        )
        .scalars()
        .all()
    )
    assert {log.action for log in logs} == {"approve", "revoke"}
    ScopedSession.remove()


def test_values_longer_than_the_column_are_rejected() -> None:
    """列長を超える入力は422で弾く（SQLiteは通すがPostgresでは500になる）。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = create_venture(client, admin)["id"]

    assert (
        client.patch(
            f"/api/v1/ventures/{venture_id}", json={"offeringType": "外" * 100}, headers=admin
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/api/v1/ventures/{venture_id}", json={"industry": "建設" * 200}, headers=admin
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/v1/ventures/{venture_id}/ledgers/data/entries",
            json={"rowKey": "R" * 100, "values": {}},
            headers=admin,
        ).status_code
        == 422
    )

    gates = client.get(f"/api/v1/ventures/{venture_id}/gates", headers=admin).json()["items"]
    assert (
        client.patch(
            f"/api/v1/ventures/{venture_id}/gates/{gates[0]['id']}",
            json={"conditionDue": "2026年10月15日までに解消"},
            headers=admin,
        ).status_code
        == 422
    )
    task = client.get(f"/api/v1/ventures/{venture_id}/tasks", headers=admin).json()["items"][0]
    assert (
        client.patch(
            f"/api/v1/ventures/{venture_id}/tasks/{task['id']}",
            json={"actualHours": 10**30},
            headers=admin,
        ).status_code
        == 422
    )


# ── 統制の穴を塞いだ分の回帰テスト ──────────────────────


def test_self_assessment_is_rejected() -> None:
    """原本28「自己申告だけで配置しない」。評価者と対象者が同一なら弾く。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = create_venture(client, admin)["id"]
    for user_id in ("admin-user", "mentor-user"):
        client.post(
            f"/api/v1/ventures/{venture_id}/members",
            json={"userId": user_id, "roleId": "R02"},
            headers=admin,
        )
    skill_id = client.get(f"/api/v1/ventures/{venture_id}/skill-gap", headers=admin).json()["items"][0][
        "skillId"
    ]

    myself = client.post(
        f"/api/v1/ventures/{venture_id}/skill-assessments",
        json={"skillId": skill_id, "userId": "admin-user", "assessedLevel": 3},
        headers=admin,
    )
    assert myself.status_code == 400
    assert "第三者" in myself.json()["detail"]

    other = client.post(
        f"/api/v1/ventures/{venture_id}/skill-assessments",
        json={"skillId": skill_id, "userId": "mentor-user", "assessedLevel": 3},
        headers=admin,
    )
    assert other.status_code == 200


def test_assessment_target_must_be_a_venture_member() -> None:
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = create_venture(client, admin)["id"]
    skill_id = client.get(f"/api/v1/ventures/{venture_id}/skill-gap", headers=admin).json()["items"][0][
        "skillId"
    ]

    stranger = client.post(
        f"/api/v1/ventures/{venture_id}/skill-assessments",
        json={"skillId": skill_id, "userId": "typo-user", "assessedLevel": 3},
        headers=admin,
    )
    assert stranger.status_code == 400
    assert "要員" in stranger.json()["detail"]
    # 充足には算入されない
    gap = client.get(f"/api/v1/ventures/{venture_id}/skill-gap", headers=admin).json()
    assert next(item for item in gap["items"] if item["skillId"] == skill_id)["coveredLevel"] == 0


def test_completion_approval_requires_evidence_and_completed_status() -> None:
    """画面のボタン制御だけでなく、APIを直接叩いても素通りしない。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = create_venture(client, admin)["id"]
    task = client.get(f"/api/v1/ventures/{venture_id}/tasks", headers=admin).json()["items"][0]
    path = f"/api/v1/ventures/{venture_id}/tasks/{task['id']}"

    no_evidence = client.patch(path, json={"approveCompletion": True}, headers=admin)
    assert no_evidence.status_code == 400
    assert "完了証拠" in no_evidence.json()["detail"]

    not_completed = client.patch(
        path,
        json={"approveCompletion": True, "evidenceUri": "https://example.test/e/1"},
        headers=admin,
    )
    assert not_completed.status_code == 400
    assert "完了" in not_completed.json()["detail"]

    ok = client.patch(
        path,
        json={
            "approveCompletion": True,
            "status": "完了",
            "evidenceUri": "https://example.test/e/1",
        },
        headers=admin,
    )
    assert ok.status_code == 200
    assert ok.json()["completionApprovedAt"] is not None


def test_independent_approval_cannot_be_self_approved() -> None:
    """原本06 R19「実装責任者と分離」。担当者本人は完了承認できない。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = create_venture(client, admin)["id"]
    tasks = client.get(f"/api/v1/ventures/{venture_id}/tasks", headers=admin).json()["items"]
    task = next(item for item in tasks if item["approverRoleId"] == "R19")
    path = f"/api/v1/ventures/{venture_id}/tasks/{task['id']}"

    client.post(
        f"/api/v1/ventures/{venture_id}/members",
        json={"userId": "admin-user", "roleId": "R02"},
        headers=admin,
    )
    client.patch(path, json={"assigneeUserId": "admin-user"}, headers=admin)

    denied = client.patch(
        path,
        json={
            "approveCompletion": True,
            "status": "完了",
            "evidenceUri": "https://example.test/e/2",
        },
        headers=admin,
    )
    assert denied.status_code == 400
    assert "分離" in denied.json()["detail"]

    # 担当を別の人に変えれば承認できる
    client.patch(path, json={"assigneeUserId": "demo-user"}, headers=admin)
    approved = client.patch(
        path,
        json={
            "approveCompletion": True,
            "status": "完了",
            "evidenceUri": "https://example.test/e/2",
        },
        headers=admin,
    )
    assert approved.status_code == 200


def test_exclusion_requires_a_reason() -> None:
    """原本17は対象外に除外理由・代替証拠を要求する。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = create_venture(client, admin)["id"]
    tasks = client.get(
        f"/api/v1/ventures/{venture_id}/tasks", params={"applicability": "未判定"}, headers=admin
    ).json()["items"]
    task = tasks[0]

    bulk = client.post(
        f"/api/v1/ventures/{venture_id}/tasks/applicability",
        json={"taskRowIds": [task["id"]], "applicability": "対象外", "reason": "  "},
        headers=admin,
    )
    assert bulk.status_code == 400
    assert "理由" in bulk.json()["detail"]

    single = client.patch(
        f"/api/v1/ventures/{venture_id}/tasks/{task['id']}",
        json={"applicability": "対象外"},
        headers=admin,
    )
    assert single.status_code == 400

    ok = client.patch(
        f"/api/v1/ventures/{venture_id}/tasks/{task['id']}",
        json={"applicability": "対象外", "applicabilityReason": "外販しないため"},
        headers=admin,
    )
    assert ok.status_code == 200
    assert ok.json()["applicability"] == "対象外"


def test_gate_keeps_the_entered_approver_name() -> None:
    """原本29の「A実名」は入力された承認者。操作者名で上書きしない。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = create_venture(client, admin)["id"]
    gates = client.get(f"/api/v1/ventures/{venture_id}/gates", headers=admin).json()["items"]
    g3 = next(gate for gate in gates if gate["gateId"] == "G3")

    res = client.patch(
        f"/api/v1/ventures/{venture_id}/gates/{g3['id']}",
        json={"decision": "承認", "decidedByName": "山田太郎", "scope": "全社"},
        headers=admin,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["decidedByName"] == "山田太郎"
    assert body["recordedByName"] == "Platform Admin"

    again = client.get(f"/api/v1/ventures/{venture_id}/gates", headers=admin).json()["items"]
    stored = next(gate for gate in again if gate["id"] == g3["id"])
    assert stored["decidedByName"] == "山田太郎"

    # 未審査に戻したら承認者名も残さない（監査ログには残る）
    reverted = client.patch(
        f"/api/v1/ventures/{venture_id}/gates/{g3['id']}", json={"decision": "未審査"}, headers=admin
    )
    assert reverted.json()["decidedByName"] == ""


def test_feature_is_limited_to_enabled_tenants(monkeypatch) -> None:
    """工程マスタは自社の工程定義。有効なテナント以外には出さない。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    assert client.get("/api/v1/ventures", headers=admin).status_code == 200

    monkeypatch.setenv("VENTURE_LEDGER_TENANTS", "other-tenant")
    assert client.get("/api/v1/ventures", headers=admin).status_code == 403
    assert client.get("/api/v1/ventures/master", headers=admin).status_code == 403


# ── 原本から回復した情報の回帰テスト ───────────────────────


def test_ledger_columns_keep_the_source_input_rules() -> None:
    """原本の入力規則（ドロップダウン27件・日付10件・数値2件）を持ち出せていること。"""
    from infrastructure.venture_master import load_master

    master = load_master()
    rules = {
        (ledger["key"], column): rule
        for ledger in master.ledgers
        for column, rule in ledger.get("column_rules", {}).items()
    }
    assert len(rules) >= 40, f"入力規則が少なすぎる: {len(rules)}列"

    # 規則は入力列にだけ付く（定義列や点検列には付けない）
    for ledger in master.ledgers:
        inputs = set(ledger["input_columns"])
        for column in ledger.get("column_rules", {}):
            assert column in inputs, f"{ledger['key']} の {column} は入力列ではない"

    # 原本の代表的な統制語彙が残っていること
    assert rules[("data", "学習利用可否")]["options"] == [
        "未判定",
        "許可",
        "条件付許可",
        "禁止",
        "対象外",
    ]
    assert rules[("risk", "案件での該当")]["options"] == ["未判定", "該当", "対象外"]
    assert rules[("release", "変更区分")]["options"][:3] == ["未判定", "Initial", "Minor"]
    assert rules[("data", "承認日")]["type"] == "date"
    assert rules[("hypothesis", "予算上限（円）")] == {"type": "number", "min": 0.0}
    assert rules[("eval_plan", "状態")]["options"][0] == "未設定"
    # 案件ごとの値を指す名前付き範囲は候補を持たない（参照名だけ残す）
    assert rules[("eval_run", "EvalPlanKey")]["source"] == "EvalPlanKeys"
    assert rules[("eval_run", "EvalPlanKey")]["options"] == []


def test_ledger_rules_are_exposed_to_the_client() -> None:
    """画面が候補・日付・数値を出し分けられるよう、APIが規則を返すこと。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = create_venture(client, admin)["id"]

    ledger = client.get(f"/api/v1/ventures/{venture_id}/ledgers/data", headers=admin).json()["ledger"]
    rules = ledger["columnRules"]
    assert rules["個人情報区分"]["type"] == "select"
    assert "要配慮個人情報" in rules["個人情報区分"]["options"]

    master = client.get("/api/v1/ventures/master", headers=admin).json()
    data_ledger = next(item for item in master["ledgers"] if item["key"] == "data")
    assert data_ledger["columnRules"]["個人情報区分"]["options"]


def test_date_and_number_rules_are_enforced() -> None:
    """日付と数値の規則もサーバで守る。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = create_venture(client, admin)["id"]

    bad_date = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/data/entries",
        json={"rowKey": "D-100", "values": {"承認日": "2026年10月1日"}},
        headers=admin,
    )
    assert bad_date.status_code == 400
    assert "YYYY-MM-DD" in bad_date.json()["detail"]

    hypothesis = client.get(f"/api/v1/ventures/{venture_id}/ledgers/hypothesis", headers=admin).json()
    row = hypothesis["items"][0]
    negative = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/hypothesis/entries",
        json={"id": row["id"], "values": {"予算上限（円）": "-1"}},
        headers=admin,
    )
    assert negative.status_code == 400
    ok = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/hypothesis/entries",
        json={"id": row["id"], "values": {"予算上限（円）": "500000"}},
        headers=admin,
    )
    assert ok.status_code == 200


def test_tasks_keep_their_source_ids_and_reference_urls() -> None:
    """原本の「根拠ID」「確認用URL」が製品内に残り、資料へ解決できること。"""
    from infrastructure.venture_master import load_master

    master = load_master()
    known = set(master.source_by_id)
    assert len(known) == 21

    assert all(task["source_ids"] for task in master.tasks), "根拠IDの無いタスクがある"
    unresolved = {
        source_id
        for task in master.tasks
        for source_id in task["source_ids"]
        if source_id not in known
    }
    assert unresolved == set(), f"資料に解決できない根拠ID: {sorted(unresolved)}"

    with_urls = [task for task in master.tasks if task["reference_urls"]]
    assert len(with_urls) == 52
    b5_20 = master.task_by_id["B5-20"]
    assert b5_20["source_ids"] == ["U01", "W01", "W02", "W03", "W15"]
    assert any("ppc.go.jp" in url for url in b5_20["reference_urls"])
    assert b5_20["legacy_task_ids"] == ["P4-02", "P4-10"]


def test_skills_keep_their_source_ids_and_legacy_ids() -> None:
    """07スキル辞書の落ちていた3列（旧v3 Skill・根拠ID・再編メモ）が戻っていること。"""
    from infrastructure.venture_master import load_master

    master = load_master()
    assert all(skill["source_ids"] for skill in master.skills)
    assert any(skill["legacy_skill_ids"] for skill in master.skills)
    assert any(skill["note"] for skill in master.skills)


def test_standards_endpoint_exposes_the_recovered_reference() -> None:
    """案件を作らずに読める標準（原本03/04/14/24/32）が揃っていること。"""
    client = TestClient(app)
    learner = sign_in(client, "learner@example.com", "Learner123!")

    res = client.get("/api/v1/ventures/master/standards", headers=learner)
    assert res.status_code == 200
    body = res.json()
    assert len(body["tailoring"]) == 3
    assert body["tailoring"][0]["aspect"] == "省略不可の原則"
    assert len(body["effortReference"]) == 8
    assert len(body["devLoop"]) == 8
    assert len(body["runtimeSettings"]) == 8
    assert len(body["harness"]) == 16
    assert len(body["harnessTests"]) == 7
    assert [test["testId"] for test in body["harnessTests"]] == [f"AT0{i}" for i in range(1, 8)]
    assert len(body["evalTypes"]) == 18
    assert len(body["sources"]) == 21
    assert set(body["scales"]) == {"S", "M", "L"}

    w02 = next(source for source in body["sources"] if source["sourceId"] == "W02")
    assert w02["organization"] == "個人情報保護委員会"
    assert w02["url"].startswith("https://www.ppc.go.jp/")


def test_incident_ledger_is_available() -> None:
    """21のインシデント記録ブロックが14番目の台帳として使えること。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = create_venture(client, admin)["id"]

    ledger = client.get(f"/api/v1/ventures/{venture_id}/ledgers/incident", headers=admin)
    assert ledger.status_code == 200
    body = ledger.json()
    assert body["ledger"]["name"] == "インシデント記録"
    assert body["ledger"]["seeded"] is False
    for column in ("検知日時", "受付日時", "復旧日時", "救済/通知/法務", "Postmortem URI"):
        assert column in body["ledger"]["inputColumns"], f"{column} が入力列に無い"

    created = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/incident/entries",
        json={"rowKey": "INC-001", "values": {"概要・利用者影響": "検索結果に他社データが混入"}},
        headers=admin,
    )
    assert created.status_code == 200
    assert created.json()["values"]["概要・利用者影響"] == "検索結果に他社データが混入"
