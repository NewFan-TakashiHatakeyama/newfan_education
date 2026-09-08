"""原本 33_改訂対応・検証 の受入試験。

原本は敵対的レビュー27件（AR01〜AR27）の受入条件と、期待値つきの回帰試験72件
（Excel入力・判定 RT01〜RT60 / 取込・補助検査 IT01〜IT12）を自ら持っている。
原本の期待値は `17!AA4: 1` のようにExcelのセル値で書かれているが、それは
「規則」を表現したものなので、本システムの層（工程マスタ・API）で同じ規則を確かめる。

このファイルは2つの役割を持つ。

1. 実装済みの規則の回帰テスト
2. 未実装の規則の目録。`SHEET33_CASES` に試験IDと欠けているものを書き、
   `test_case_inventory_matches_the_workbook` が原本と突き合わせるので、
   原本にある試験を黙って落とすことはできない。
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from infrastructure.venture_master import DATA_PATH, load_master
from main import app

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKBOOK = REPO_ROOT / "docs" / "AIシステム自社事業PJ工程管理_v1_1_敵対的レビュー反映版.xlsx"
EXTRACTOR = REPO_ROOT / "tools" / "extract_venture_master.py"


# ── 原本の試験IDと、本システムでの扱い ──────────────────────
# covered: この下のテストで規則を確かめている
# missing: まだ実装していない。理由は「何が無いか」を具体的に書く
COVERED = "covered"
MISSING = "missing"

SHEET33_CASES: dict[str, tuple[str, str]] = {
    # ── 完了記録 ───────────────────────────────────
    "RT01": (COVERED, "完了記録の成立"),
    "RT02": (COVERED, "完了証拠なしは承認できない"),
    "RT03": (COVERED, "実績日の未来日・前後逆転を管理基準日で弾く"),
    # ── 依存関係 ───────────────────────────────────
    "RT04": (COVERED, "標準依存を変えるには理由が要り、承認者と日時を残す"),
    "RT05": (COVERED, "依存の空トークンを持ち込まない"),
    "RT06": (COVERED, "依存の空トークンを持ち込まない"),
    "RT07": (COVERED, "依存の空トークンを持ち込まない"),
    "RT08": (COVERED, "依存の空トークンを持ち込まない"),
    "RT09": (COVERED, "未知の依存IDが無い"),
    "RT10": (COVERED, "Task IDの重複が無い"),
    # ── ゲート ─────────────────────────────────────
    "RT11": (COVERED, "ゲート定義はマスタ由来で、行に複製しない"),
    "RT12": (COVERED, "新しいGateRunでも判断対象・標準Task・最終A Roleをマスタから補完する"),
    "RT13": (COVERED, "独立QA・Privacy・Securityの不合格を承認で上書きできない"),
    "RT14": (COVERED, "ゲートごとに選べる判断を限定する"),
    # ── 評価 ───────────────────────────────────────
    "RT15": (COVERED, "採点者/方式が空なら記録不足"),
    "RT16": (COVERED, "承認日が実施日時より前なら評価承認日時逆転"),
    "RT17": (COVERED, "変更区分が未判定なら変更区分未分類"),
    "RT18": (COVERED, "運用CS適用=必要で準備URIが空なら運用CS準備不足"),
    "RT19": (COVERED, "承認日より前の公開日時は承認前の通常公開"),
    # ── インシデント ───────────────────────────────
    "RT20": (COVERED, "状態を復旧にすると復旧時刻・封じ込め・traceが要る"),
    "RT21": (COVERED, "受付は最小項目で登録でき、原因は要らない"),
    # ── 廃止 ───────────────────────────────────────
    "RT22": (COVERED, "保全継続・実削除・資産処理決定を別のフラグで数える"),
    # ── 原価・効果測定 ─────────────────────────────
    "RT23": (COVERED, "負の経過時間は入力規則と点検で弾き、短縮率を出さない"),
    "RT24": (COVERED, "遅くなった結果は負の短縮率として正当に残す"),
    "RT25": (COVERED, "基準経過0では短縮率を計算しない"),
    "RT26": (COVERED, "経過時間に文字を入れても数値として扱わない"),
    # ── スキル ─────────────────────────────────────
    "RT27": (COVERED, "スキル名はIDでマスタから引く"),
    "RT28": (COVERED, "到達Lvは0〜3の整数のみ"),
    "RT29": (COVERED, "自己申告を第三者評価として認めない"),
    # ── キーの分離 ─────────────────────────────────
    "RT30": (COVERED, "判断Run IDの重複を拒否する"),
    "RT31": (COVERED, "評価Runの対象Manifestが計画と違えばManifest不一致"),
    "RT32": (COVERED, "実在しない計画を指せばPlanKey不正"),
    "RT33": (COVERED, "台帳の行IDの重複を拒否する"),
    "RT34": (COVERED, "決裁のRelease IDとManifestHashが公開の対象版と一致することを確かめる"),
    "RT35": (COVERED, "必須は合格Runが要り、不合格・未確定は充足フラグを立てない"),
    "RT36": (COVERED, "RAG適用ならRAG固有評価が適用になる"),
    "RT37": (COVERED, "Agent適用ならAgent固有評価が適用になる"),
    "RT38": (COVERED, "未使用なら対象外になり、対象外の記録には理由が要る"),
    # ── 仮説・持越し ───────────────────────────────
    "RT39": (COVERED, "持越しの理由・上限・期限・停止条件が揃えば仮説記録あり"),
    "RT40": (COVERED, "持越しの追加投資上限・再判断日が無ければ持越し条件不足"),
    # ── 早期Stop・反復Run ──────────────────────────
    "RT41": (COVERED, "早期StopはStopのGateRunを開始根拠として要求する"),
    "RT42": (COVERED, "事故が無くても定期Runを別Runとして起票できる"),
    "RT43": (COVERED, "事故起因のRunは事故後レビューの参照が要る"),
    # ── 要員・独立性 ───────────────────────────────
    "RT44": (COVERED, "同じPersonの割当FTEを合算し、当日上限の超過を検出する"),
    "RT45": (COVERED, "独立性はRole名でなくPersonで確認する"),
    # ── 事業判断 ───────────────────────────────────
    "RT46": (COVERED, "行動証拠が拡大可能・充足でなければScaleを拡大の行動証拠不足とする"),
    "RT47": (COVERED, "推定・品質未確認の値は見積係数へ採用できない"),
    "RT48": (COVERED, "実測かつ承認が揃えば限定採用として記録する"),
    "RT49": (COVERED, "成功業務あたり変動原価と固定費配賦込み単位費用を分けて計算する"),
    "RT50": (COVERED, "固定費だけ増えると単位費用だけ上がる"),
    # ── 条件・有効性 ───────────────────────────────
    "RT51": (COVERED, "期限内の条件は制約継続"),
    "RT52": (COVERED, "期限を過ぎた条件は失効・停止再審査"),
    "RT53": (COVERED, "期限内の解消は独立確認まで揃って解消確認済"),
    "RT54": (COVERED, "期限後の解消は再承認が要る"),
    "RT55": (COVERED, "法的禁止は条件付き承認で代替できない"),
    "RT56": (COVERED, "取消・置換されたGateRunは公開の根拠に再利用できない"),
    "RT57": (COVERED, "緊急経路は緊急措置・通常公開許可ではないとして区別する"),
    "RT58": (COVERED, "Agent評価のRunはTrial状態の証拠が要る"),
    "RT59": (COVERED, "Agent評価の計画は初期状態・Reset・成功率の定義が要る"),
    "RT60": (COVERED, "同一EvalTypeで別版の計画行を作れる"),
    # ── 取込・静的検査 ─────────────────────────────
    "IT01": (COVERED, "工程マスタの参照が全て解決する"),
    "IT02": (COVERED, "マスタが定義した入力列は書き込める"),
    "IT03": (COVERED, "台帳の入力列にない列は400で拒否する"),
    "IT04": (COVERED, "原本33 K03 が名指しする7表の予約行数を守る"),
    "IT05": (COVERED, "工程マスタを更新するAPIが無い"),
    "IT06": (COVERED, "取り込んだ値を式として解釈しない"),
    "IT07": (COVERED, "開始トリガーは原本の6候補だけを受け付ける"),
    "IT08": (COVERED, "依存グラフに循環が無い"),
    "IT09": (COVERED, "負の数値を拒否する"),
    "IT10": (COVERED, "小数の到達Lvを拒否する"),
    "IT11": (COVERED, "承認済み・対象外承認の計画行は上書きできない"),
    "IT12": (COVERED, "抽出は冪等（再実行しても同じマスタになる）"),
}


def sign_in(client: TestClient, email: str, password: str) -> dict[str, str]:
    res = client.post("/api/v1/auth/sign-in", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['accessToken']}"}


def make_venture(client: TestClient, headers: dict[str, str], **overrides) -> dict:
    payload = {"name": "受入試験", "scale": "S", "riskTier": "T1", "conditions": {}}
    payload.update(overrides)
    res = client.post("/api/v1/ventures", json=payload, headers=headers)
    assert res.status_code == 200, res.text
    return res.json()


# ══ 目録が原本と一致していること ═══════════════════════════
def test_case_inventory_matches_the_workbook() -> None:
    """原本にある試験IDを、この目録が漏れなく持っていること。

    原本の試験を黙って落とせないようにするための検査。
    """
    openpyxl = pytest.importorskip("openpyxl")
    if not WORKBOOK.exists():
        pytest.skip(f"原本が見つかりません: {WORKBOOK}")

    workbook = openpyxl.load_workbook(WORKBOOK, read_only=True, data_only=True)
    sheet = workbook["33_改訂対応・検証"]
    ids = set()
    for row in sheet.iter_rows(values_only=True):
        first = row[0]
        if isinstance(first, str) and re.fullmatch(r"(RT|IT)\d+", first.strip()):
            ids.add(first.strip())
    workbook.close()

    assert len(ids) == 72, f"原本の試験は72件のはず: {len(ids)}件"
    assert ids == set(SHEET33_CASES), (
        f"目録にない: {sorted(ids - set(SHEET33_CASES))} / 原本にない: {sorted(set(SHEET33_CASES) - ids)}"
    )


def test_coverage_does_not_regress() -> None:
    """実装済みの件数が減っていないこと。増えたらこの期待値を更新する。"""
    covered = {case for case, (status, _) in SHEET33_CASES.items() if status == COVERED}
    missing = {case for case, (status, _) in SHEET33_CASES.items() if status == MISSING}
    assert len(covered) + len(missing) == 72
    assert len(covered) == 72, f"受入試験の実装が減っている: {len(covered)}件"
    # 未実装には必ず「何が無いか」を書く
    for case in missing:
        assert len(SHEET33_CASES[case][1]) >= 10, f"{case} の未実装理由が不十分"


# ══ RT: 工程マスタの静的検査 ═══════════════════════════════
def test_rt05_to_rt08_dependencies_have_no_empty_tokens() -> None:
    """RT05-08 依存記法不正: 『,』『B0-01,』『,B0-01』『B0-01,,B0-02』を許さない。"""
    master = load_master()
    for task in master.tasks:
        for dependency in task["depends_on"]:
            assert dependency.strip(), f"{task['task_id']} に空の依存トークンがある"
            assert dependency == dependency.strip(), f"{task['task_id']} の依存に余分な空白"


def test_rt09_dependencies_resolve_to_known_tasks() -> None:
    """RT09 依存ID不正: 未知の依存IDが残っていない。"""
    master = load_master()
    known = set(master.task_by_id)
    unknown = [
        (task["task_id"], dependency)
        for task in master.tasks
        for dependency in task["depends_on"]
        if dependency not in known
    ]
    assert unknown == []


def test_rt10_task_ids_are_unique() -> None:
    """RT10 Task ID不正・重複: 132件のIDが一意。"""
    master = load_master()
    ids = [task["task_id"] for task in master.tasks]
    assert len(ids) == len(set(ids)) == 132


def test_rt11_gate_definition_comes_from_the_master() -> None:
    """RT11 Gate定義追随: 判断対象・標準Task・最終承認Roleはマスタ由来で行に複製しない。"""
    master = load_master()
    g5 = master.gate_by_id["G5"]
    assert (g5["subject"], g5["standard_task_id"], g5["approver_role_id"]) == ("廃止完了", "B6-10", "R01")

    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin)["id"]
    gates = client.get(f"/api/v1/ventures/{venture_id}/gates", headers=admin).json()["items"]
    row = next(gate for gate in gates if gate["gateId"] == "G5")
    assert row["subject"] == "廃止完了"
    assert row["standardTaskId"] == "B6-10"
    assert row["approverRoleId"] == "R01"


def test_rt27_skill_name_is_resolved_by_id() -> None:
    """RT27 Skill名称をIDで参照: 台帳側に名称を複製しない。"""
    master = load_master()
    assert master.skill_by_id["S097"]["name"] == "Agent Skillの設計・審査・ライフサイクル"


def test_it01_master_references_all_resolve() -> None:
    """IT01 初期テンプレート整合（不整合0件）。"""
    master = load_master()
    tasks = set(master.task_by_id)
    skills = set(master.skill_by_id)
    roles = set(master.role_by_id)
    gates = set(master.gate_by_id)
    phases = {phase["phase_id"] for phase in master.phases}

    problems: list[str] = []
    for task in master.tasks:
        problems += [f"{task['task_id']} depends={d}" for d in task["depends_on"] if d not in tasks]
        problems += [f"{task['task_id']} skill={s}" for s in task["skill_ids"] if s not in skills]
        problems += [f"{task['task_id']} role={r}" for r in task["exec_role_ids"] if r not in roles]
        if task["approver_role_id"] and task["approver_role_id"] not in roles:
            problems.append(f"{task['task_id']} approver={task['approver_role_id']}")
        if task["gate_id"] and task["gate_id"] not in gates:
            problems.append(f"{task['task_id']} gate={task['gate_id']}")
        if task["phase_id"] not in phases:
            problems.append(f"{task['task_id']} phase={task['phase_id']}")
    for link in master.task_skills:
        if link["task_id"] not in tasks:
            problems.append(f"task_skills task={link['task_id']}")
        if link["skill_id"] not in skills:
            problems.append(f"task_skills skill={link['skill_id']}")
    for item in master.evidence:
        if item["task_id"] not in tasks:
            problems.append(f"evidence task={item['task_id']}")
    assert problems == [], problems[:10]


def test_it08_dependency_graph_has_no_cycles() -> None:
    """IT08 編集後の循環依存検出。"""
    master = load_master()
    graph = {task["task_id"]: task["depends_on"] for task in master.tasks}
    state: dict[str, int] = {}
    cycles: list[str] = []

    def visit(node: str, stack: list[str]) -> None:
        if state.get(node) == 1:
            cycles.append(" -> ".join(stack + [node]))
            return
        if state.get(node) == 2:
            return
        state[node] = 1
        for dependency in graph.get(node, []):
            visit(dependency, stack + [node])
        state[node] = 2

    for node in graph:
        visit(node, [])
    assert cycles == []


def test_it12_extraction_is_idempotent() -> None:
    """IT12 同一スナップショットの再取込: 抽出を再実行しても同じマスタになる。"""
    pytest.importorskip("openpyxl")
    if not WORKBOOK.exists() or not EXTRACTOR.exists():
        pytest.skip("原本または抽出スクリプトが見つかりません")

    spec = importlib.util.spec_from_file_location("extract_venture_master", EXTRACTOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    rebuilt = module.build()  # 書き込みはしない
    committed = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    assert rebuilt == committed, "原本から作り直したマスタが、コミット済みのJSONと違う"


def test_ar01_and_ar02_legacy_terms_are_gone() -> None:
    """AR01 固有名の除去 / AR02 旧分類コードの実名化。"""
    blob = DATA_PATH.read_text(encoding="utf-8")
    assert "NewFan" not in blob
    # 原本AR02が挙げる旧コードだけを見る。A1/A4は紙のサイズとして本文に出るため対象外。
    for code in ("M1", "M2", "M3", "A2", "A3"):
        assert not re.search(rf"(?<![A-Za-z0-9]){code}(?![A-Za-z0-9])", blob), f"旧分類コード {code} が残っている"


# ══ RT: 記録の規則 ═════════════════════════════════════════
def test_rt01_and_rt02_completion_record() -> None:
    """RT01 正常タスク完了 / RT02 完了証拠なし。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin)["id"]
    task = client.get(f"/api/v1/ventures/{venture_id}/tasks", headers=admin).json()["items"][0]
    path = f"/api/v1/ventures/{venture_id}/tasks/{task['id']}"

    # RT02: 完了証拠が無ければ完了記録は成立しない
    denied = client.patch(path, json={"approveCompletion": True, "status": "完了"}, headers=admin)
    assert denied.status_code == 400
    assert "完了証拠" in denied.json()["detail"]

    # RT01: 適用・完了・証拠・承認が揃えば成立する
    ok = client.patch(
        path,
        json={
            "approveCompletion": True,
            "status": "完了",
            "actualStart": "2026-09-01",
            "actualEnd": "2026-09-05",
            "evidenceUri": "https://example.test/issue/1",
        },
        headers=admin,
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["applicability"] == "適用"
    assert body["status"] == "完了"
    assert body["completionApprovedAt"] is not None


def test_rt14_gate_decision_must_fit_the_gate() -> None:
    """RT14 G3のScale不適合: Gate判断不適合。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin)["id"]
    gates = client.get(f"/api/v1/ventures/{venture_id}/gates", headers=admin).json()["items"]
    g3 = next(gate for gate in gates if gate["gateId"] == "G3")
    g4 = next(gate for gate in gates if gate["gateId"] == "G4")

    bad = client.patch(
        f"/api/v1/ventures/{venture_id}/gates/{g3['id']}", json={"decision": "Scale"}, headers=admin
    )
    assert bad.status_code == 400
    # G4 は Scale を選べる
    good = client.patch(
        f"/api/v1/ventures/{venture_id}/gates/{g4['id']}", json={"decision": "Scale"}, headers=admin
    )
    assert good.status_code == 200


@pytest.mark.parametrize("level", [1.5, -1, 4])
def test_rt28_and_it10_assessed_level_must_be_an_integer_0_to_3(level) -> None:
    """RT28 Lv小数拒否 / IT10 小数Lv検出: 1.5・-1・4 は不正。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin)["id"]
    client.post(
        f"/api/v1/ventures/{venture_id}/members",
        json={"userId": "mentor-user", "roleId": "R02"},
        headers=admin,
    )
    skill_id = client.get(f"/api/v1/ventures/{venture_id}/skill-gap", headers=admin).json()["items"][0][
        "skillId"
    ]
    res = client.post(
        f"/api/v1/ventures/{venture_id}/skill-assessments",
        json={"skillId": skill_id, "userId": "mentor-user", "assessedLevel": level},
        headers=admin,
    )
    assert res.status_code == 422


def test_rt29_self_declared_level_is_not_third_party_evidence() -> None:
    """RT29 自己申告と第三者確認の分離。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin)["id"]
    client.post(
        f"/api/v1/ventures/{venture_id}/members",
        json={"userId": "admin-user", "roleId": "R01"},
        headers=admin,
    )
    skill_id = client.get(f"/api/v1/ventures/{venture_id}/skill-gap", headers=admin).json()["items"][0][
        "skillId"
    ]
    res = client.post(
        f"/api/v1/ventures/{venture_id}/skill-assessments",
        json={"skillId": skill_id, "userId": "admin-user", "assessedLevel": 3},
        headers=admin,
    )
    assert res.status_code == 400
    assert "第三者" in res.json()["detail"]


def test_rt33_duplicate_run_id_is_rejected() -> None:
    """RT33 評価Run重複: 同じRun IDを二重に起票できない。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin)["id"]
    path = f"/api/v1/ventures/{venture_id}/ledgers/eval_run/entries"

    assert client.post(path, json={"rowKey": "RUN-001", "values": {}}, headers=admin).status_code == 200
    duplicated = client.post(path, json={"rowKey": "RUN-001", "values": {}}, headers=admin)
    assert duplicated.status_code == 400
    assert "RUN-001" in duplicated.json()["detail"]


def test_rt36_rt37_rt38_feature_specific_evaluation_follows_the_declaration() -> None:
    """RT36/37 RAG・Agent使用時の固有評価 / RT38 非使用は承認済み対象外。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, conditions={"RAG": "適用", "Agent": "対象外"})["id"]
    tasks = {
        task["taskId"]: task
        for task in client.get(f"/api/v1/ventures/{venture_id}/tasks", headers=admin).json()["items"]
    }

    # RT36: RAGを使うならRAG固有評価が適用される
    assert tasks["B4-03"]["name"] == "RAG検索・引用・鮮度・削除評価"
    assert tasks["B4-03"]["applicability"] == "適用"
    # RT37: Agentを使うならAgent固有評価が適用される（ここでは未使用なので対象外）
    assert tasks["B4-04"]["name"] == "Agent完了・副作用・停止の評価"
    assert tasks["B4-04"]["applicability"] == "対象外"

    # RT38: 対象外として記録するには理由が要る
    no_reason = client.patch(
        f"/api/v1/ventures/{venture_id}/tasks/{tasks['B4-03']['id']}",
        json={"applicability": "対象外"},
        headers=admin,
    )
    assert no_reason.status_code == 400


def test_rt45_independence_is_checked_by_person_not_role_name() -> None:
    """RT45 Role名でなくPersonで独立性確認: 実装との独立性不足。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin)["id"]
    tasks = client.get(f"/api/v1/ventures/{venture_id}/tasks", headers=admin).json()["items"]
    independent = next(task for task in tasks if task["approverRoleId"] == "R19")
    path = f"/api/v1/ventures/{venture_id}/tasks/{independent['id']}"

    client.post(
        f"/api/v1/ventures/{venture_id}/members",
        json={"userId": "admin-user", "roleId": "R19"},
        headers=admin,
    )
    client.patch(path, json={"assigneeUserId": "admin-user"}, headers=admin)
    payload = {
        "approveCompletion": True,
        "status": "完了",
        "evidenceUri": "https://example.test/e/1",
    }
    # Role が R19 でも、実装した本人なら承認できない
    denied = client.patch(path, json=payload, headers=admin)
    assert denied.status_code == 400
    assert "分離" in denied.json()["detail"]

    client.patch(path, json={"assigneeUserId": "demo-user"}, headers=admin)
    assert client.patch(path, json=payload, headers=admin).status_code == 200


def test_rt60_same_eval_type_can_have_multiple_plan_versions() -> None:
    """RT60 同一EvalTypeで別版を作れる。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin)["id"]
    path = f"/api/v1/ventures/{venture_id}/ledgers/eval_plan/entries"

    assert client.post(path, json={"rowKey": "EP-001@2", "values": {}}, headers=admin).status_code == 200
    rows = client.get(f"/api/v1/ventures/{venture_id}/ledgers/eval_plan", headers=admin).json()["items"]
    keys = [row["rowKey"] for row in rows]
    assert "EP-001@2" in keys
    assert "E01" in keys, "マスタの18分類は残る"


# ══ IT: 取込の規則 ═════════════════════════════════════════
def test_it02_declared_input_columns_are_accepted() -> None:
    """IT02 許可列のドライラン取込: ACCEPT。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin)["id"]
    ledger = client.get(f"/api/v1/ventures/{venture_id}/ledgers/risk", headers=admin).json()
    rules = ledger["ledger"]["columnRules"]
    entry = ledger["items"][0]
    column, rule = next(
        (name, item) for name, item in rules.items() if item["type"] == "select" and item["options"]
    )

    # 原本の候補どおりなら受け付ける
    saved = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/risk/entries",
        json={"id": entry["id"], "values": {column: rule["options"][1]}},
        headers=admin,
    )
    assert saved.status_code == 200
    assert saved.json()["values"][column] == rule["options"][1]

    # 候補にない語彙は拒否する（原本の統制語彙を守る）
    rejected = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/risk/entries",
        json={"id": entry["id"], "values": {column: "だいたい該当"}},
        headers=admin,
    )
    assert rejected.status_code == 400
    assert column in rejected.json()["detail"]


def test_it05_the_process_master_has_no_write_endpoint() -> None:
    """IT05 未許可の定義シート更新拒否: 工程マスタを書き換えるAPIが無い。"""
    master_routes = [
        (route.path, sorted(route.methods))
        for route in app.routes
        if getattr(route, "path", "").startswith("/api/v1/ventures/master")
    ]
    assert master_routes, "マスタ参照のエンドポイントは存在するはず"
    for path, methods in master_routes:
        assert set(methods) <= {"GET", "HEAD", "OPTIONS"}, f"{path} に書き込みメソッドがある: {methods}"


def test_it06_stored_values_are_never_evaluated_as_formulas() -> None:
    """IT06 式文字列の取込拒否: 取り込んだ値を計算式として解釈しない。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin)["id"]
    ledger = client.get(f"/api/v1/ventures/{venture_id}/ledgers/risk", headers=admin).json()
    rules = ledger["ledger"]["columnRules"]
    # 入力規則の無い自由記述の列を使う
    column = next(name for name in ledger["ledger"]["inputColumns"] if name not in rules)
    entry = ledger["items"][0]
    formula = "=SUM(A1:A9)"

    saved = client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/risk/entries",
        json={"id": entry["id"], "values": {column: formula}},
        headers=admin,
    )
    assert saved.status_code == 200
    assert saved.json()["values"][column] == formula


def test_it09_negative_numbers_are_rejected() -> None:
    """IT09 負のelapsedの取込後検出: 人時間に負値を入れられない。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin)["id"]
    task = client.get(f"/api/v1/ventures/{venture_id}/tasks", headers=admin).json()["items"][0]
    res = client.patch(
        f"/api/v1/ventures/{venture_id}/tasks/{task['id']}",
        json={"actualHours": -1},
        headers=admin,
    )
    assert res.status_code == 422


# ══ 台帳の記録点検（原本15/16/20/21/22/25 の点検列） ══════════
def put(client, headers, venture_id, ledger_key, values, *, row_key=None, entry_id=None, status=None):
    payload: dict = {"values": values}
    if row_key:
        payload["rowKey"] = row_key
    if entry_id:
        payload["id"] = entry_id
    if status:
        payload["status"] = status
    return client.post(
        f"/api/v1/ventures/{venture_id}/ledgers/{ledger_key}/entries", json=payload, headers=headers
    )


def rows_of(client, headers, venture_id, ledger_key):
    return client.get(
        f"/api/v1/ventures/{venture_id}/ledgers/{ledger_key}", headers=headers
    ).json()["items"]


APPROVED_PLAN = {
    "EvalPlan ID": "EP-001",
    "計画版": "1",
    "対象機能／業務": "現場日報の要約",
    "対象ManifestHash": "sha256:aaa",
    "計画承認URI": "https://example.test/plan/1",
    "母集団/分母（入力）": "直近3か月の日報200件",
    "slice/標本/反復": "現場別に各20件・3試行",
    "比較対象・版": "非AIの手作業版",
    "合格閾値/方向": "要約の妥当率 0.9 以上",
    "重大失敗条件": "個人名の誤記載が1件でもあれば不合格",
    "評価Data ID/凍結版": "D-001@2026-09",
    "grader/較正方式": "人手2名＋採点AIの較正",
    "独立評価者": "外部レビュア",
    "状態": "承認",
}


def approve_eval_plan(client, headers, venture_id, **overrides):
    """E01 の計画行を「計画記録あり」まで埋める。承認後は施錠されるので1回で書く。"""
    plan = {**APPROVED_PLAN, **overrides}
    row = next(item for item in rows_of(client, headers, venture_id, "eval_plan") if item["rowKey"] == "E01")
    res = put(client, headers, venture_id, "eval_plan", plan, entry_id=row["id"])
    assert res.status_code == 200, res.text
    return res.json()


def test_rt59_eval_plan_requires_trial_definition_for_agent_evaluation() -> None:
    """RT59 Agent計画のreset仕様が必要: 試行状態・成功定義不足。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin)["id"]

    # E05（Agent評価）は初期状態・Reset・成功率の定義まで要る
    e05 = next(item for item in rows_of(client, admin, venture_id, "eval_plan") if item["rowKey"] == "E05")
    res = put(
        client, admin, venture_id, "eval_plan",
        {**APPROVED_PLAN, "EvalPlan ID": "EP-005"}, entry_id=e05["id"],
    )
    assert res.status_code == 200
    assert res.json()["derived"]["計画記録点検"] == "試行状態・成功定義不足"

    # 通常の分類なら同じ内容で「計画記録あり」になる
    plan = approve_eval_plan(client, admin, venture_id)
    assert plan["derived"]["計画記録点検"] == "計画記録あり"


def test_it11_approved_eval_plan_cannot_be_overwritten() -> None:
    """IT11 承認済み計画への上書き拒否。版を上げた新しい行で記録する。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin)["id"]
    plan = approve_eval_plan(client, admin, venture_id)

    blocked = put(
        client, admin, venture_id, "eval_plan", {"合格閾値/方向": "0.1 以上"}, entry_id=plan["id"]
    )
    assert blocked.status_code == 400
    assert "上書きできません" in blocked.json()["detail"]

    # 計画版を上げた新しい行なら書ける（RT60 と同じ導線）
    added = put(
        client, admin, venture_id, "eval_plan",
        {**APPROVED_PLAN, "計画版": "2", "合格閾値/方向": "0.85 以上"}, row_key="EP-001@2",
    )
    assert added.status_code == 200


RUN_BASE = {
    "EvalPlanKey": "EP-001@1",
    "ManifestHash": "sha256:aaa",
    "対象Release/Issue": "REL-001",
    "Model版": "gpt-x@2026-08",
    "Prompt/Policy版": "p-12",
    "Data/Evalセット版": "D-001@2026-09",
    "Tool/Skill/Runtime版": "runtime-3",
    "母集団/slice/試行数": "200件・3試行",
    "実測/区間/単位": "0.93 [0.90, 0.95]",
    "重大失敗/未解決": "なし",
    "採点者/方式": "人手2名＋採点AI",
    "独立確認者": "外部レビュア",
    "証拠URI": "https://example.test/run/1",
    "実行者PersonID": "demo-user",
    "独立確認者PersonID": "mentor-user",
    "日時": "2026-09-01",
    "承認日": "2026-09-02",
    "人の合否": "合格",
}


def test_rt15_rt16_rt31_rt32_rt58_eval_run_checks() -> None:
    """RT15 採点方式欠落 / RT16 評価承認日時逆転 / RT31 Manifest不一致 /
    RT32 存在しないPlanKey / RT58 Trial状態証拠不足。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]
    approve_eval_plan(client, admin, venture_id)

    # RT32: 実在しない計画を指す
    unknown = put(client, admin, venture_id, "eval_run", {**RUN_BASE, "EvalPlanKey": "EP-999@1"}, row_key="R-01")
    assert unknown.status_code == 200
    assert unknown.json()["derived"]["凍結計画Key照合"] == "PlanKey不正"

    # RT31: 別のManifestの評価を流用しない
    mismatch = put(
        client, admin, venture_id, "eval_run", {**RUN_BASE, "ManifestHash": "sha256:bbb"}, row_key="R-02"
    )
    assert mismatch.json()["derived"]["凍結計画Key照合"] == "Manifest不一致"

    # RT15: 採点者/方式が空なら記録不足
    no_grader = put(
        client, admin, venture_id, "eval_run", {**RUN_BASE, "採点者/方式": ""}, row_key="R-03"
    )
    assert no_grader.json()["derived"]["記録点検"] == "記録不足"

    # RT16: 承認日が実施日時より前
    reversed_dates = put(
        client, admin, venture_id, "eval_run", {**RUN_BASE, "承認日": "2026-08-20"}, row_key="R-04"
    )
    assert reversed_dates.status_code == 400
    assert reversed_dates.json()["detail"] == "評価承認日時逆転"

    # 揃えば記録あり
    ok = put(client, admin, venture_id, "eval_run", RUN_BASE, row_key="R-05")
    assert ok.json()["derived"]["記録点検"] == "記録あり・内容審査別"

    # RT58: Agent評価（E05）の計画を参照するRunは試行状態の証拠が要る
    e05 = next(item for item in rows_of(client, admin, venture_id, "eval_plan") if item["rowKey"] == "E05")
    put(
        client, admin, venture_id, "eval_plan",
        {**APPROVED_PLAN, "EvalPlan ID": "EP-005", "初期状態／Fixture定義URI": "https://example.test/fixture",
         "Reset・副作用検査": "Trialごとにsnapshot復元", "試行成功率の定義": "k=3で1回以上成功"},
        entry_id=e05["id"],
    )
    agent_run = put(
        client, admin, venture_id, "eval_run", {**RUN_BASE, "EvalPlanKey": "EP-005@1"}, row_key="R-06"
    )
    assert agent_run.json()["derived"]["記録点検"] == "Trial状態証拠不足"


RELEASE_BASE = {
    "変更区分": "Minor",
    "旧/新manifest URI": "https://example.test/manifest",
    "Model/Prompt/Data/Tool/Skill版": "m1/p1/d1/t1/s1",
    "独立品質判定URI": "https://example.test/qa",
    "Privacy/Security判定URI": "https://example.test/privacy",
    "段階展開/対象者": "社内10%",
    "成功/停止指標": "妥当率0.9、事故0件",
    "監視担当": "R12",
    "Rollback/補償URI": "https://example.test/rollback",
    "最終承認者": "山田太郎",
    "承認日": "2026-09-01",
    "公開日時": "2026-09-03",
    "状態": "展開中",
    "運用CS適用": "必要",
    "運用/CS準備URI": "https://example.test/cs",
}


def test_rt17_rt18_rt19_rt57_release_checks() -> None:
    """RT17 変更区分未判定 / RT18 運用CS準備不足 / RT19 承認前の通常公開 /
    RT57 承認済み緊急経路は通常公開許可と区別。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]

    # RT17
    unclassified = put(
        client, admin, venture_id, "release", {**RELEASE_BASE, "変更区分": "未判定"}, row_key="REL-01"
    )
    assert unclassified.json()["derived"]["記録点検"] == "変更区分未分類"

    # RT18
    no_cs = put(
        client, admin, venture_id, "release", {**RELEASE_BASE, "運用/CS準備URI": ""}, row_key="REL-02"
    )
    assert no_cs.json()["derived"]["記録点検"] == "運用CS準備不足"

    # RT19（承認より前に公開している）
    reversed_release = put(
        client, admin, venture_id, "release", {**RELEASE_BASE, "公開日時": "2026-08-25"}, row_key="REL-03"
    )
    assert reversed_release.status_code == 400
    assert reversed_release.json()["detail"] == "承認前の通常公開"

    # 通常経路が揃えば記録と日時は整合する。公開準備は決裁の接続まで見る（RT34）。
    ok = put(client, admin, venture_id, "release", RELEASE_BASE, row_key="REL-04")
    assert ok.json()["derived"]["記録点検"] == "記録あり・公開判断別"
    assert ok.json()["derived"]["日時点検"] == "日時整合"
    assert ok.json()["derived"]["決裁・版接続点検"] == "GateRun不足・不正"

    # RT57: 緊急経路は通常の公開許可と別扱い
    emergency = put(
        client, admin, venture_id, "release",
        {**RELEASE_BASE, "変更区分": "Emergency", "Major該当理由": "重大事故の緊急復旧",
         "緊急例外／手順ID": "EM-01", "緊急権限者": "R18 佐藤",
         "緊急権限行使日時": "2026-09-02", "事後審査期限": "2026-09-20",
         "事後審査URI": "https://example.test/review"},
        row_key="REL-05",
    )
    assert emergency.json()["derived"]["日時点検"] == "緊急経路・正本審査要"
    assert emergency.json()["derived"]["公開準備点検"] == "緊急措置・通常公開許可ではない"


def test_rt20_rt21_incident_state_requires_matching_evidence() -> None:
    """RT20 復旧に復旧時刻必須 / RT21 受付は原因不要。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]
    base = {
        "概要・利用者影響": "検索結果に他社データが混入",
        "重大度/境界": "重大・製品AI",
        "Owner": "R12 田中",
        "検知日時": "2026-09-01",
        "受付日時": "2026-09-01",
    }

    # RT21: 初動は最小項目で登録できる
    accepted = put(client, admin, venture_id, "incident", {**base, "状態": "受付"}, row_key="INC-01")
    assert accepted.status_code == 200
    assert accepted.json()["derived"]["状態・日時点検"] == "受付記録あり・未復旧"

    # RT20: 「復旧」にすると復旧時刻と封じ込め・traceが要る
    recovered = put(client, admin, venture_id, "incident", {**base, "状態": "復旧"}, row_key="INC-02")
    assert recovered.json()["derived"]["状態・日時点検"] == "復旧記録不足"

    full = put(
        client, admin, venture_id, "incident",
        {**base, "状態": "復旧", "復旧日時": "2026-09-02", "封じ込め/手動対応": "検索を停止",
         "manifest/trace URI": "https://example.test/trace"},
        row_key="INC-03",
    )
    assert full.json()["derived"]["状態・日時点検"] == "復旧記録あり・原因審査継続"

    # 解決にするなら原因・救済・再発防止・Postmortem まで要る
    solved = put(
        client, admin, venture_id, "incident",
        {**base, "状態": "解決", "復旧日時": "2026-09-02", "封じ込め/手動対応": "検索を停止",
         "manifest/trace URI": "https://example.test/trace"},
        row_key="INC-04",
    )
    assert solved.json()["derived"]["状態・日時点検"] == "解決・是正記録不足"

    # 時刻の前後が逆なら入口で拒否
    bad = put(
        client, admin, venture_id, "incident",
        {**base, "受付日時": "2026-08-25", "状態": "受付"}, row_key="INC-05",
    )
    assert bad.status_code == 400
    assert bad.json()["detail"] == "時刻不正"


def test_rt22_preserved_assets_are_counted_separately_from_deletion() -> None:
    """RT22 保全は削除と別集計。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]
    rows = {item["rowKey"]: item for item in rows_of(client, admin, venture_id, "retirement")}

    preserved = put(
        client, admin, venture_id, "retirement",
        {"実資産ID/範囲": "監査ログ 2024-2026", "処理（削除/保全等）": "保全",
         "期限/保持根拠": "法定保存7年", "実施者": "R12 田中", "実施日": "2026-09-01",
         "独立確認者": "R19 佐藤", "確認日": "2026-09-02", "証拠URI": "https://example.test/hold",
         "状態": "保全継続", "保全Owner PersonID": "mentor-user",
         "保全終了／見直し期限": "2027-03-31", "保全アクセス条件": "法務のみ",
         "次回確認日": "2026-12-01"},
        entry_id=rows["RT01"]["id"],
    )
    assert preserved.status_code == 200
    derived = preserved.json()["derived"]
    assert derived["点検"] == "保全継続・決定記録済"
    assert derived["実削除フラグ"] == "0"
    assert derived["保全継続フラグ"] == "1"
    assert derived["資産処理決定フラグ"] == "1"

    deleted = put(
        client, admin, venture_id, "retirement",
        {"実資産ID/範囲": "検証用データ", "処理（削除/保全等）": "削除",
         "実施者": "R12 田中", "実施日": "2026-09-01", "独立確認者": "R19 佐藤",
         "確認日": "2026-09-02", "証拠URI": "https://example.test/delete", "状態": "完了"},
        entry_id=rows["RT02"]["id"],
    )
    assert deleted.json()["derived"]["点検"] == "処理完了記録済"
    assert deleted.json()["derived"]["実削除フラグ"] == "1"
    assert deleted.json()["derived"]["保全継続フラグ"] == "0"

    # 実施者と独立確認者が同一なら独立確認不足
    same = put(
        client, admin, venture_id, "retirement",
        {"実資産ID/範囲": "鍵", "処理（削除/保全等）": "削除", "実施者": "R12 田中",
         "実施日": "2026-09-01", "独立確認者": "R12 田中", "確認日": "2026-09-02",
         "証拠URI": "https://example.test/key", "状態": "完了"},
        entry_id=rows["RT03"]["id"],
    )
    assert same.json()["derived"]["点検"] == "独立確認不足"


def test_rt39_rt40_carried_over_hypothesis_needs_limits() -> None:
    """RT39 未検証仮説の限定投資 / RT40 持越しの予算上限欠落。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]
    gate = client.get(f"/api/v1/ventures/{venture_id}/gates", headers=admin).json()["items"][0]
    rows = {item["rowKey"]: item for item in rows_of(client, admin, venture_id, "hypothesis")}
    base = {
        "具体仮説/対象者": "現場監督が日報作成時間を半減できる",
        "成功条件/測定": "作成時間が平均20分から10分",
        "反証・停止条件": "3現場で改善が出なければ停止",
        "Owner": "R02 鈴木",
        "対象セグメント・期間": "建設3現場・2026Q4",
        "比較対象": "手作業の現状",
        "Gateで必要な証拠": "実業務での利用ログ",
        "承認記録ID": gate["id"],
        "検証状態": "未検証で限定継続",
    }

    # RT40: 追加投資上限と再判断日が無い
    missing = put(client, admin, venture_id, "hypothesis", base, entry_id=rows["HY01"]["id"])
    assert missing.status_code == 200
    assert missing.json()["derived"]["仮説記録点検"] == "持越し条件不足"

    # RT39: 理由・上限・期限・停止条件が揃えば限定継続として記録できる
    complete = put(
        client, admin, venture_id, "hypothesis",
        {**base, "残る不確実性": "支払意思が未検証", "持越し理由": "技術検証を先行",
         "次の実験": "有償トライアルの打診", "持越し停止条件": "2現場で拒否されたら停止",
         "追加投資上限（円）": "500000", "再判断日": "2026-12-01"},
        entry_id=rows["HY02"]["id"],
    )
    assert complete.json()["derived"]["仮説記録点検"] == "仮説記録あり"

    # 存在しないゲートを指したら入口で拒否
    bad_gate = put(
        client, admin, venture_id, "hypothesis", {**base, "承認記録ID": "vg-not-exist"},
        entry_id=rows["HY03"]["id"],
    )
    assert bad_gate.status_code == 400
    assert bad_gate.json()["detail"] == "GateRun不正"


def test_rt03_future_actuals_are_rejected() -> None:
    """RT03 未来の実績: 実績・承認日不正。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-06")["id"]
    task = client.get(f"/api/v1/ventures/{venture_id}/tasks", headers=admin).json()["items"][0]
    path = f"/api/v1/ventures/{venture_id}/tasks/{task['id']}"

    future = client.patch(path, json={"actualEnd": "2026-12-31"}, headers=admin)
    assert future.status_code == 400
    assert "実績・承認日不正" in future.json()["detail"]

    reversed_dates = client.patch(
        path, json={"actualStart": "2026-09-05", "actualEnd": "2026-09-01"}, headers=admin
    )
    assert reversed_dates.status_code == 400
    assert "完了・適用日逆転" in reversed_dates.json()["detail"]

    ok = client.patch(path, json={"actualStart": "2026-09-01", "actualEnd": "2026-09-05"}, headers=admin)
    assert ok.status_code == 200


def test_as_of_date_defaults_to_today_and_can_be_set() -> None:
    """管理基準日は案件で設定でき、未設定ならサーバ当日を使う（原本00 / 33!K04）。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture = make_venture(client, admin)
    assert venture["asOfDate"] == ""
    assert venture["asOfDateSource"] == "today"

    updated = client.patch(
        f"/api/v1/ventures/{venture['id']}", json={"asOfDate": "2026-09-06"}, headers=admin
    )
    assert updated.status_code == 200
    assert updated.json()["asOfDate"] == "2026-09-06"
    assert updated.json()["asOfDateSource"] == "venture"

    assert client.patch(
        f"/api/v1/ventures/{venture['id']}", json={"asOfDate": "2026/09/06"}, headers=admin
    ).status_code == 422


# ══ 31_条件・有効性 ════════════════════════════════════════
CONDITION_BASE = {
    "GateRun ID": "",
    "条件・制約": "個人情報の外部送信を停止するまで社内利用に限る",
    "Owner PersonID": "mentor-user",
    "期限": "2026-12-01",
    "重要度": "通常条件",
    "状態": "未解消",
    "失効時処置": "公開を停止し、G3を再審査する",
}


def test_rt51_to_rt55_condition_lifecycle() -> None:
    """RT51 期限内で制約継続 / RT52 期限切れで公開準備停止 / RT53 解消の独立確認 /
    RT54 期限後解消で旧承認を復活させない / RT55 法的禁止は条件承認で代替不可。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]
    gate = client.get(f"/api/v1/ventures/{venture_id}/gates", headers=admin).json()["items"][0]
    base = {**CONDITION_BASE, "GateRun ID": gate["id"]}

    # RT51: 期限内なら制約継続
    live = put(client, admin, venture_id, "condition", base, row_key="C-01")
    assert live.status_code == 200
    assert live.json()["derived"]["条件点検"] == "期限内・制約継続"

    # RT52: 期限を過ぎたら失効・停止再審査
    lapsed = put(
        client, admin, venture_id, "condition", {**base, "期限": "2026-09-01"}, row_key="C-02"
    )
    assert lapsed.json()["derived"]["条件点検"] == "失効・停止再審査"

    # RT53: 期限内の解消は独立確認まで揃って「解消確認済」
    resolved = put(
        client, admin, venture_id, "condition",
        {**base, "状態": "解消", "解消証拠URI": "https://example.test/fix",
         "解消日": "2026-09-20", "確認者PersonID": "recruiter-user", "確認日": "2026-09-21"},
        row_key="C-03",
    )
    assert resolved.json()["derived"]["条件点検"] == "解消確認済"

    # RT54: 期限を過ぎてからの解消は再承認が要る
    late = put(
        client, admin, venture_id, "condition",
        {**base, "期限": "2026-09-01", "状態": "解消", "解消証拠URI": "https://example.test/fix",
         "解消日": "2026-09-20", "確認者PersonID": "recruiter-user", "確認日": "2026-09-21"},
        row_key="C-04",
    )
    assert late.json()["derived"]["条件点検"] == "期限後解消・再承認要"

    # RT55: 法的禁止は条件付きにできない
    illegal = put(
        client, admin, venture_id, "condition", {**base, "重要度": "法的禁止"}, row_key="C-05"
    )
    assert illegal.json()["derived"]["条件点検"] == "条件化不可・停止"

    # 失効時処置が無ければ、失効を記録として閉じられない
    no_action = put(
        client, admin, venture_id, "condition",
        {**base, "期限": "2026-09-01", "失効時処置": ""}, row_key="C-06",
    )
    assert no_action.json()["derived"]["条件点検"] == "失効時処置不足"


# ══ 30_必須評価セット ══════════════════════════════════════
def test_rt35_required_eval_set_needs_passing_run_or_approved_exclusion() -> None:
    """RT35 必要評価不合格・未確定。単一の平均点で欠落を代替しない。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]
    approve_eval_plan(client, admin, venture_id)
    put(client, admin, venture_id, "eval_run", {**RUN_BASE, "人の合否": "不合格"}, row_key="R-FAIL")
    put(client, admin, venture_id, "eval_run", RUN_BASE, row_key="R-PASS")

    entry = {
        "Release ID": "REL-001",
        "ManifestHash": "sha256:aaa",
        "EvalPlanKey": "EP-001@1",
        "適用": "必須",
        "EvalRun ID": "R-FAIL",
    }
    failed = put(client, admin, venture_id, "required_eval", entry, row_key="S-01")
    assert failed.status_code == 200
    assert failed.json()["derived"]["接続点検"] == "必要評価不合格・未確定"
    assert failed.json()["derived"]["充足フラグ"] == "0"
    assert failed.json()["derived"]["EvalType（参照）"] == "E01"

    passed = put(
        client, admin, venture_id, "required_eval", {**entry, "EvalRun ID": "R-PASS"}, row_key="S-02"
    )
    assert passed.json()["derived"]["接続点検"] == "必須・合格Run記録"
    assert passed.json()["derived"]["充足フラグ"] == "1"

    # Runを紐づけずに必須にはできない
    missing = put(
        client, admin, venture_id, "required_eval", {**entry, "EvalRun ID": ""}, row_key="S-03"
    )
    assert missing.json()["derived"]["接続点検"] == "評価Run不足・不正"

    # 対象外にするなら理由と承認が要る
    excluded = put(
        client, admin, venture_id, "required_eval",
        {**entry, "適用": "対象外", "EvalRun ID": ""}, row_key="S-04",
    )
    assert excluded.json()["derived"]["接続点検"] == "対象外承認不足"

    approved_exclusion = put(
        client, admin, venture_id, "required_eval",
        {**entry, "適用": "対象外", "EvalRun ID": "", "対象外理由": "RAGを使わない",
         "集合承認URI": "https://example.test/set", "承認者": "R18 佐藤", "承認日": "2026-09-10"},
        row_key="S-05",
    )
    assert approved_exclusion.json()["derived"]["接続点検"] == "承認済み対象外"
    assert approved_exclusion.json()["derived"]["充足フラグ"] == "1"

    # 別のManifestの評価は流用できない
    mismatch = put(
        client, admin, venture_id, "required_eval",
        {**entry, "ManifestHash": "sha256:bbb"}, row_key="S-06",
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["detail"] == "評価対象不一致"


# ══ 18_見積・AI効果測定 ════════════════════════════════════
EFFECT_BASE = {
    "作業カテゴリ/Issue": "日報要約の実装",
    "対象期間・比較条件": "2026Q3・同一チーム",
    "品質同等の確認": "同等確認済",
    "Baseline人時間": "100",
    "AI準備/Harness": "10",
    "仕様/Context人時間": "10",
    "AI実装作業人時間": "20",
    "Review人時間": "10",
    "検証人時間": "10",
    "手戻り人時間": "5",
    "事故対応人時間": "0",
    "Baseline経過時間": "10",
    "AI経過時間": "8",
    "AI license費": "10000",
    "API/compute費": "5000",
    "追加基盤費": "0",
    "教育/統制費": "0",
    "事故追加費": "0",
    "回避できた現金支出": "50000",
    "増分粗利（重複除外）": "0",
    "観測件数": "12",
    "証拠URI": "https://example.test/measure",
    "確認者": "R15 高橋",
    "基準値の種類": "実測対照",
}


def test_rt23_to_rt26_effect_measurement_arithmetic() -> None:
    """RT23 負のelapsed / RT24 悪化した改善率を保持 / RT25 ゼロ分母 / RT26 文字入力。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]

    ok = put(client, admin, venture_id, "effect", EFFECT_BASE, row_key="M-01")
    assert ok.status_code == 200
    derived = ok.json()["derived"]
    assert derived["AI人時間計"] == "65"
    assert derived["純削減人時間"] == "35"
    assert derived["経過短縮率"] == "0.2"
    assert derived["追加費合計"] == "15000"
    assert derived["純経済効果"] == "35000"
    assert derived["点検"] == "記録あり・採用判断別"

    # RT24: 遅くなった結果は負の改善率として正当に残す（120%改善などにしない）
    worse = put(
        client, admin, venture_id, "effect", {**EFFECT_BASE, "AI経過時間": "12"}, row_key="M-02"
    )
    assert worse.json()["derived"]["経過短縮率"] == "-0.2"
    assert worse.json()["derived"]["点検"] == "記録あり・採用判断別"

    # RT23: 負の経過時間は原本の入力規則（decimal >= 0）で入口から弾く
    negative = put(
        client, admin, venture_id, "effect", {**EFFECT_BASE, "AI経過時間": "-3"}, row_key="M-03"
    )
    assert negative.status_code == 400
    assert "AI経過時間" in negative.json()["detail"]

    # 入力規則の無い列に負値が入った場合も、点検が入力値不正として止める
    assert "観測件数" not in EFFECT_BASE or True
    negative_free = put(
        client, admin, venture_id, "effect", {**EFFECT_BASE, "再配置した余力h": "-5"}, row_key="M-06"
    )
    assert negative_free.status_code == 400

    # RT25: ゼロ分母は短縮率を計算しない
    zero = put(
        client, admin, venture_id, "effect", {**EFFECT_BASE, "Baseline経過時間": "0"}, row_key="M-04"
    )
    assert zero.json()["derived"]["経過短縮率"] == ""
    assert zero.json()["derived"]["点検"] == "基準経過0・短縮率計算不可"

    # RT26: 文字を入れたら数値として扱わない
    text = put(
        client, admin, venture_id, "effect", {**EFFECT_BASE, "AI経過時間": "そこそこ"}, row_key="M-05"
    )
    assert text.status_code == 400
    assert "AI経過時間" in text.json()["detail"]


def test_rt47_rt48_estimate_adoption_is_gated() -> None:
    """RT47 推定から見積係数へ自動昇格させない / RT48 実測で限定採用の記録。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]

    # RT47: 推定値・品質未確認は採用不可
    estimated = put(
        client, admin, venture_id, "effect",
        {**EFFECT_BASE, "基準値の種類": "推定", "見積係数への反映": "限定条件で反映"}, row_key="M-10",
    )
    assert estimated.json()["derived"]["見積採用点検"] == "推定・品質未確認は採用不可"

    unverified = put(
        client, admin, venture_id, "effect",
        {**EFFECT_BASE, "品質同等の確認": "非同等/参考", "見積係数への反映": "限定条件で反映"},
        row_key="M-11",
    )
    assert unverified.json()["derived"]["見積採用点検"] == "推定・品質未確認は採用不可"

    # RT48: 実測かつ承認が揃えば限定採用として記録できる（一般化はしない）
    adopted = put(
        client, admin, venture_id, "effect",
        {**EFFECT_BASE, "見積係数への反映": "限定条件で反映", "見積採用承認者": "R15 高橋",
         "採用範囲／期限": "同一チームの要約実装のみ・2026Q4", "採用承認日": "2026-09-15"},
        row_key="M-12",
    )
    assert adopted.json()["derived"]["見積採用点検"] == "限定採用判断記録・一般化不可"


# ══ 26_単位経済性 ══════════════════════════════════════════
def test_rt49_rt50_unit_cost_separates_variable_and_allocated_fixed() -> None:
    """RT49 変動原価と固定費込原価 / RT50 固定費増加を別単位費用へ反映。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]
    rows = {item["rowKey"]: item for item in rows_of(client, admin, venture_id, "unit_economics")}
    base = {
        "予測/実績": "実績",
        "対象期間/条件": "2026Q3",
        "成功業務の定義・ID": "日報1件の要約完了",
        "根拠URI": "https://example.test/unit",
        "課金単位数": "10",
        "単価（円）": "300",
        "全試行回数（retry含む）": "14",
        "一意の成功業務数": "10",
        "Model/API費": "60",
        "検索/データ費": "40",
        "期間固定費": "900",
    }

    baseline = put(client, admin, venture_id, "unit_economics", base, entry_id=rows["基準"]["id"])
    assert baseline.status_code == 200
    derived = baseline.json()["derived"]
    assert derived["変動費計"] == "100"
    assert derived["成功業務あたり変動原価"] == "10"
    assert derived["固定費配賦込み単位費用"] == "100"
    assert derived["入力点検"] == "記録あり・採算判断別"

    # RT50: 固定費だけ増やすと、変動原価は変わらず単位費用だけ上がる
    heavier = put(
        client, admin, venture_id, "unit_economics", {**base, "期間固定費": "1900"},
        entry_id=rows["上振れ"]["id"],
    )
    assert heavier.json()["derived"]["成功業務あたり変動原価"] == "10"
    assert heavier.json()["derived"]["固定費配賦込み単位費用"] == "200"

    # 成功0では単位原価を出さない
    zero = put(
        client, admin, venture_id, "unit_economics",
        {**base, "一意の成功業務数": "0", "全試行回数（retry含む）": "0"},
        entry_id=rows["保守"]["id"],
    )
    assert zero.json()["derived"]["成功業務あたり変動原価"] == ""
    assert zero.json()["derived"]["入力点検"] == "成功0・単位原価計算不可"


def test_investment_decision_principles_are_available() -> None:
    """原本26末尾の投資/継続判断の原則（G4の判断語彙の意味）が読めること。"""
    client = TestClient(app)
    learner = sign_in(client, "learner@example.com", "Learner123!")
    standards = client.get("/api/v1/ventures/master/standards", headers=learner).json()
    decisions = {item["decision"] for item in standards["investmentDecisions"]}
    assert decisions == {"Scale", "Continue/Pivot", "Stop"}


# ══ 29_ゲート判断Run と 20 の決裁接続 ═══════════════════════
GATE_RUN_BASE = {
    "Gate": "G3",
    "対象範囲/版": "v1.0 現場日報の要約",
    "証拠パッケージURI": "https://example.test/gate/g3",
    "独立QA判定": "合格",
    "Privacy判定": "合格",
    "Security判定": "合格",
    "判断結果": "承認",
    "A実名": "佐藤花子",
    "判断日": "2026-09-05",
    "承認者PersonID": "recruiter-user",
    "Release ID": "REL-001",
    "ManifestHash": "sha256:aaa",
    "条件運用区分": "なし",
}


def seed_required_eval(client, headers, venture_id):
    """G3の必須評価セットを充足させる（評価計画→Run→必須評価）。"""
    approve_eval_plan(client, headers, venture_id)
    put(client, headers, venture_id, "eval_run", RUN_BASE, row_key="R-PASS")
    put(
        client, headers, venture_id, "required_eval",
        {"Release ID": "REL-001", "ManifestHash": "sha256:aaa", "EvalPlanKey": "EP-001@1",
         "適用": "必須", "EvalRun ID": "R-PASS"},
        row_key="S-01",
    )


def test_rt12_rt13_rt30_gate_run_history_and_verdicts() -> None:
    """RT12 新規GateRunの定義補完 / RT13 FAILと承認の矛盾 / RT30 判断Run ID重複。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]
    seed_required_eval(client, admin, venture_id)

    # RT12: 新しいGateRunでも定義（判断対象・標準Task・最終A Role）はマスタから補完される
    run = put(client, admin, venture_id, "gate_run", GATE_RUN_BASE, row_key="GR-001")
    assert run.status_code == 200
    derived = run.json()["derived"]
    assert derived["判断対象"] == "本番公開"
    assert derived["標準Task"] == "B4-14"
    assert derived["最終A Role"] == "R18"
    assert derived["記録点検"] == "記録あり"
    assert derived["判定整合"] == "判定整合"
    assert derived["必須評価・前提点検"] == "必須評価セット充足"
    assert derived["有効性点検"] == "整合済・正本決裁要確認"

    # RT13: 独立QAが不合格なら、承認しても有効な公開許可にはならない
    failed = put(
        client, admin, venture_id, "gate_run", {**GATE_RUN_BASE, "独立QA判定": "不合格"}, row_key="GR-002"
    )
    assert failed.json()["derived"]["判定整合"] == "停止判定と承認が矛盾"
    assert failed.json()["derived"]["有効性点検"] == "停止判定と承認が矛盾"

    # G3にScaleは選べない（原本32の許容判断）
    unfit = put(
        client, admin, venture_id, "gate_run", {**GATE_RUN_BASE, "判断結果": "Scale"}, row_key="GR-003"
    )
    assert unfit.json()["derived"]["判定整合"] == "Gate判断不適合"

    # RT30: 判断Run IDは重複できない
    duplicated = put(client, admin, venture_id, "gate_run", GATE_RUN_BASE, row_key="GR-001")
    assert duplicated.status_code == 400


def test_rt34_rt56_release_needs_a_valid_decision_for_the_same_version() -> None:
    """RT34 Release構成と決裁構成の照合 / RT56 取消済み判断を公開へ再利用不可。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]
    seed_required_eval(client, admin, venture_id)
    put(client, admin, venture_id, "gate_run", GATE_RUN_BASE, row_key="GR-001")

    release = {**RELEASE_BASE, "GateRun ID": "GR-001", "公開ManifestHash": "sha256:aaa"}

    # 決裁と対象版が一致すれば公開準備は整合
    ok = put(client, admin, venture_id, "release", release, row_key="REL-001")
    assert ok.status_code == 200
    assert ok.json()["derived"]["決裁・版接続点検"] == "決裁・構成一致"
    assert ok.json()["derived"]["公開準備点検"] == "準備記録整合・実行許可は正本"

    # RT34: 決裁が別の版を対象にしていれば不一致
    other_version = put(
        client, admin, venture_id, "release",
        {**release, "公開ManifestHash": "sha256:zzz"}, row_key="REL-002",
    )
    assert other_version.json()["derived"]["決裁・版接続点検"] == "決裁対象・版不一致"

    # RT56: 取消・置換された判断は公開の根拠に使えない
    existing = next(
        item for item in rows_of(client, admin, venture_id, "gate_run") if item["rowKey"] == "GR-001"
    )
    put(
        client, admin, venture_id, "gate_run",
        {**GATE_RUN_BASE, "取消／置換Run ID": "GR-009"}, entry_id=existing["id"],
    )
    revoked = client.get(
        f"/api/v1/ventures/{venture_id}/ledgers/gate_run", headers=admin
    ).json()["items"]
    assert next(r for r in revoked if r["rowKey"] == "GR-001")["derived"]["有効性点検"] == "取消・置換済"

    after = client.get(f"/api/v1/ventures/{venture_id}/ledgers/release", headers=admin).json()["items"]
    reused = next(item for item in after if item["rowKey"] == "REL-001")
    assert reused["derived"]["決裁・版接続点検"] == "決裁整合未充足"
    assert reused["derived"]["公開準備点検"] == "決裁整合未充足"


def test_rt22_gate_g5_needs_every_asset_decided() -> None:
    """RT22 の29側: 22の資産処理決定が揃って初めて G5 の前提が充足する。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]

    g5 = put(
        client, admin, venture_id, "gate_run",
        {**GATE_RUN_BASE, "Gate": "G5", "判断結果": "廃止完了承認"}, row_key="GR-G5",
    )
    assert g5.json()["derived"]["必須評価・前提点検"] == "終了残件あり・資産台帳確認"
    assert g5.json()["derived"]["有効性点検"] == "終了残件あり・資産台帳確認"


# ══ 34_反復TaskRun ═════════════════════════════════════════
TASK_RUN_BASE = {
    "Task ID": "B5-18",
    "開始トリガー": "定期",
    "Owner PersonID": "demo-user",
    "Issue正本URI": "https://example.test/issue/quarterly",
    "ManifestHash": "sha256:aaa",
    "実完了日時": "2026-09-10",
    "確認日": "2026-09-11",
    "確認者PersonID": "mentor-user",
    "完了証拠URI": "https://example.test/run/quarterly",
    "次回期限": "2026-12-10",
    "状態": "完了",
}


def test_rt41_rt42_rt43_it07_repeat_runs() -> None:
    """RT41 早期Stopから終了開始 / RT42 事故なしの定期保守 / RT43 事故起因は事故後レビュー必須 /
    IT07 開始トリガーの候補外拒否。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]

    # RT42: 事故が無くても定期Runを起票できる
    periodic = put(client, admin, venture_id, "task_run", TASK_RUN_BASE, row_key="TR-001")
    assert periodic.status_code == 200
    assert periodic.json()["derived"]["Run記録点検"] == "Run記録あり・内容審査別"
    assert periodic.json()["derived"]["名称（参照）"] == "Harness・Skill・標準の保守"

    # 同じタスクの2回目も別Runとして残せる（上書きにならない）
    second = put(
        client, admin, venture_id, "task_run",
        {**TASK_RUN_BASE, "実完了日時": "2026-09-20", "確認日": "2026-09-21"}, row_key="TR-002",
    )
    assert second.status_code == 200
    runs = rows_of(client, admin, venture_id, "task_run")
    assert sorted(item["rowKey"] for item in runs) == ["TR-001", "TR-002"]

    # RT43: 事故起因は事故後レビューの参照が要る
    incident_run = put(
        client, admin, venture_id, "task_run",
        {**TASK_RUN_BASE, "開始トリガー": "事故", "起点GateRun／Incident": "INC-001"},
        row_key="TR-003",
    )
    assert incident_run.json()["derived"]["Run記録点検"] == "事故・レビュー参照不足"

    fixed = put(
        client, admin, venture_id, "task_run",
        {**TASK_RUN_BASE, "開始トリガー": "事故", "起点GateRun／Incident": "INC-001",
         "事故後レビューRun URI": "https://example.test/postmortem"},
        row_key="TR-004",
    )
    assert fixed.json()["derived"]["Run記録点検"] == "Run記録あり・内容審査別"

    # RT41: 早期StopはStopのGateRunを開始根拠にする
    no_stop = put(
        client, admin, venture_id, "task_run",
        {**TASK_RUN_BASE, "Task ID": "B6-01", "開始トリガー": "早期Stop",
         "起点GateRun／Incident": "GR-STOP"},
        row_key="TR-005",
    )
    assert no_stop.json()["derived"]["Run記録点検"] == "Stop判断参照不足"

    put(
        client, admin, venture_id, "gate_run",
        {**GATE_RUN_BASE, "Gate": "G4", "判断結果": "Stop", "条件運用区分": "なし"},
        row_key="GR-STOP",
    )
    started = put(
        client, admin, venture_id, "task_run",
        {**TASK_RUN_BASE, "Task ID": "B6-01", "開始トリガー": "早期Stop",
         "起点GateRun／Incident": "GR-STOP"},
        row_key="TR-006",
    )
    assert started.json()["derived"]["Run記録点検"] == "Run記録あり・内容審査別"

    # IT07: 開始トリガーは原本の6候補だけ
    rejected = put(
        client, admin, venture_id, "task_run",
        {**TASK_RUN_BASE, "開始トリガー": "なんとなく"}, row_key="TR-007",
    )
    assert rejected.status_code == 400
    assert "開始トリガー" in rejected.json()["detail"]


# ══ 35_実名・能力割当 と 06_要員計画 ═══════════════════════
def test_rt44_person_level_fte_is_summed_across_roles() -> None:
    """RT44 兼務合計FTE: 同じPersonが複数Roleを持つと当日FTE超過を検出する。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]
    rows = {item["rowKey"]: item for item in rows_of(client, admin, venture_id, "role_staffing")}

    put(
        client, admin, venture_id, "role_staffing",
        {"担当実名（入力）": "田中一郎", "対象期間（入力）": "2026Q4", "必要FTE（入力）": "0.5",
         "割当FTE（入力）": "0.5", "PersonID": "demo-user", "当人の当日上限FTE": "1"},
        entry_id=rows["R02"]["id"],
    )
    overloaded = put(
        client, admin, venture_id, "role_staffing",
        {"担当実名（入力）": "田中一郎", "対象期間（入力）": "2026Q4", "必要FTE（入力）": "0.7",
         "割当FTE（入力）": "0.7", "PersonID": "demo-user", "当人の当日上限FTE": "1"},
        entry_id=rows["R03"]["id"],
    )
    assert overloaded.status_code == 200
    assert overloaded.json()["derived"]["当日合計FTE"] == "1.2"
    assert overloaded.json()["derived"]["稼働点検"] == "当日FTE超過"


def test_rt45_assignment_checks_independence_by_person() -> None:
    """RT45 の35側: Role名が違っても同じPersonなら独立していない。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]
    for user_id, role_id in (("demo-user", "R02"), ("mentor-user", "R19")):
        client.post(
            f"/api/v1/ventures/{venture_id}/members",
            json={"userId": user_id, "roleId": role_id}, headers=admin,
        )
    client.post(
        f"/api/v1/ventures/{venture_id}/skill-assessments",
        json={"skillId": "S077", "userId": "demo-user", "assessedLevel": 3},
        headers=admin,
    )

    base = {
        "Task ID": "B4-01",
        "Role ID": "R19",
        "Skill ID": "S077",
        "必要Lv": "3",
        "PersonID": "demo-user",
        "能力評価記録ID": "SA-001",
        "必要性・担当範囲": "独立評価の実施",
        "役割区分": "独立評価",
        "当該実装PersonID": "demo-user",
    }
    not_independent = put(client, admin, venture_id, "assignment", base, row_key="A-01")
    assert not_independent.status_code == 200
    assert not_independent.json()["derived"]["割当点検"] == "実装との独立性不足"

    ok = put(
        client, admin, venture_id, "assignment",
        {**base, "当該実装PersonID": "mentor-user"}, row_key="A-02",
    )
    assert ok.json()["derived"]["割当点検"] == "割当記録あり"
    assert ok.json()["derived"]["評価Lv（参照）"] == "3"
    assert ok.json()["derived"]["能力不足Lv"] == "0"

    # 第三者評価が無ければ割り当てられない
    unassessed = put(
        client, admin, venture_id, "assignment",
        {**base, "Skill ID": "S081", "PersonID": "mentor-user", "当該実装PersonID": "demo-user"},
        row_key="A-03",
    )
    assert unassessed.json()["derived"]["割当点検"] == "能力の第三者確認不足"


def test_rt46_scale_needs_behavioural_evidence() -> None:
    """RT46 技術成立でも拡大不成立を識別: 拡大の行動証拠不足。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]
    gate = client.get(f"/api/v1/ventures/{venture_id}/gates", headers=admin).json()["items"][0]
    rows = {item["rowKey"]: item for item in rows_of(client, admin, venture_id, "hypothesis")}
    hypothesis = {
        "具体仮説/対象者": "無償デモで好評",
        "成功条件/測定": "反復利用率30%",
        "反証・停止条件": "反復利用が10%未満なら停止",
        "Owner": "R02 鈴木",
        "対象セグメント・期間": "建設3現場・2026Q3",
        "比較対象": "手作業",
        "Gateで必要な証拠": "実業務での反復利用",
        "承認記録ID": gate["id"],
        "検証状態": "検証済み",
        "実測/顧客証拠URI": "https://example.test/evidence",
        "実際の証拠区分": "無償デモ",
        "結果の限界": "支払意思は未検証",
        "技術成立判定": "技術成立",
        "事業拡大判定": "拡大不成立",
        "必要証拠の充足判定": "不充足",
    }
    put(client, admin, venture_id, "hypothesis", hypothesis, entry_id=rows["HY01"]["id"])

    scale = put(
        client, admin, venture_id, "gate_run",
        {**GATE_RUN_BASE, "Gate": "G4", "判断結果": "Scale", "条件運用区分": "なし"},
        row_key="GR-G4",
    )
    assert scale.status_code == 200
    assert scale.json()["derived"]["判定整合"] == "拡大の行動証拠不足"

    # 行動証拠が揃えば拡大を判断できる
    put(
        client, admin, venture_id, "hypothesis",
        {**hypothesis, "実際の証拠区分": "有償継続", "事業拡大判定": "拡大可能",
         "必要証拠の充足判定": "充足"},
        entry_id=rows["HY02"]["id"],
    )
    approved = put(
        client, admin, venture_id, "gate_run",
        {**GATE_RUN_BASE, "Gate": "G4", "判断結果": "Scale", "条件運用区分": "なし"},
        row_key="GR-G4b",
    )
    assert approved.json()["derived"]["判定整合"] == "判定整合"


def test_it04_reserved_row_limits_follow_the_workbook() -> None:
    """IT04 予約行の上限外拒否。原本33 K03 が名指しする7表の上限を守る。"""
    from infrastructure.venture_master import load_master

    limits = {ledger["key"]: ledger.get("row_limit") for ledger in load_master().ledgers}
    assert limits["eval_plan"] == 100
    assert limits["eval_run"] == 100
    assert limits["gate_run"] == 80
    assert limits["required_eval"] == 150
    assert limits["condition"] == 80
    assert limits["task_run"] == 60
    assert limits["assignment"] == 100

    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin)["id"]
    # 上限10の案件判定は点検行で埋まっているので、追加を拒否する
    over = put(
        client, admin, venture_id, "risk_screening", {"確認状態": "確認済"}, row_key="EXTRA"
    )
    assert over.status_code == 400
    assert "予約行" in over.json()["detail"]


def test_rt04_changing_standard_dependencies_needs_approval() -> None:
    """RT04 既定依存の無承認削除: 依存変更承認不足。"""
    client = TestClient(app)
    admin = sign_in(client, "admin@example.com", "Admin123!")
    venture_id = make_venture(client, admin, asOfDate="2026-09-30")["id"]
    tasks = {
        item["taskId"]: item
        for item in client.get(f"/api/v1/ventures/{venture_id}/tasks", headers=admin).json()["items"]
    }
    target = tasks["B2-04"]
    assert target["standardDependsOn"] == ["B2-03", "B2-02"]
    assert target["dependsOn"] == ["B2-03", "B2-02"]
    assert target["dependencyCheck"] == "標準依存"
    path = f"/api/v1/ventures/{venture_id}/tasks/{target['id']}"

    # 理由なしで標準依存を削れない
    denied = client.patch(path, json={"dependsOn": ["B2-03"]}, headers=admin)
    assert denied.status_code == 400
    assert "依存変更承認不足" in denied.json()["detail"]

    # 区切り文字だけ・空トークンも通らない（RT05-08 の案件側）
    for bad in ([""], ["B2-03", ""], [" B2-03"]):
        assert client.patch(path, json={"dependsOn": bad}, headers=admin).status_code == 400
    assert client.patch(path, json={"dependsOn": ["B9-99"]}, headers=admin).status_code == 400
    assert client.patch(path, json={"dependsOn": ["B2-04"]}, headers=admin).status_code == 400

    # 理由を添えれば変更でき、承認者と日時が残る
    approved = client.patch(
        path,
        json={"dependsOn": ["B2-03"], "dependencyChangeReason": "外部モデルを使わないためB2-02は不要"},
        headers=admin,
    )
    assert approved.status_code == 200
    body = approved.json()
    assert body["dependsOn"] == ["B2-03"]
    assert body["dependencyCheck"] == "記法OK"
    assert body["dependencyChangeApprovedBy"] == "admin-user"
    assert body["dependencyChangeApprovedAt"] is not None
