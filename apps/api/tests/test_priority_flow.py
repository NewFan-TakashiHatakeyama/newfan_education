from fastapi.testclient import TestClient

from main import app
from presentation.dependencies import CONTAINER


def sign_in(client: TestClient, email: str, password: str) -> dict[str, str]:
    res = client.post("/api/v1/auth/sign-in", json={"email": email, "password": password})
    assert res.status_code == 200
    token = res.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}


def test_jwt_auth_and_me_endpoint() -> None:
    client = TestClient(app)
    headers = sign_in(client, "admin@example.com", "Admin123!")
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["userId"] == "admin-user"
    assert me.json()["tenantId"] == "company-demo"


def test_legacy_domains_are_isolated() -> None:
    client = TestClient(app)
    headers = sign_in(client, "admin@example.com", "Admin123!")
    assert client.get("/api/v1/opportunities", headers=headers).status_code == 410
    assert client.get("/api/v1/messages/threads", headers=headers).status_code == 410
    assert client.get("/api/v1/portfolio/artifacts/me", headers=headers).status_code == 410
    assert client.get("/api/v1/public-profile/settings/me", headers=headers).status_code == 410


def test_b2b_core_flow_with_postgres_repository() -> None:
    client = TestClient(app)
    admin_headers = sign_in(client, "admin@example.com", "Admin123!")
    learner_headers = sign_in(client, "learner@example.com", "Learner123!")
    mentor_headers = sign_in(client, "mentor@example.com", "Mentor123!")

    company = client.get("/api/v1/companies/current", headers=admin_headers)
    assert company.status_code == 200
    assert company.json()["id"] == "company-demo"

    learners = client.get("/api/v1/learners", headers=admin_headers)
    assert learners.status_code == 200
    learner_id = learners.json()["items"][0]["id"]

    role_templates = client.get("/api/v1/role-templates", headers=admin_headers)
    assert role_templates.status_code == 200
    template_id = role_templates.json()["items"][0]["id"]

    assigned = client.post(
        "/api/v1/roadmaps/assign",
        headers=admin_headers,
        json={"learnerId": learner_id, "roleTemplateId": template_id},
    )
    assert assigned.status_code == 200

    exercises = client.get("/api/v1/exercises", headers=learner_headers)
    assert exercises.status_code == 200
    exercise_id = exercises.json()["items"][0]["id"]

    submitted = client.post(
        f"/api/v1/exercises/{exercise_id}/submit",
        headers=learner_headers,
        json={"code": "def solve(items):\n    return items"},
    )
    assert submitted.status_code == 200
    submission_id = submitted.json()["id"]

    ai_review = client.post(f"/api/v1/submissions/{submission_id}/ai-review", headers=learner_headers)
    assert ai_review.status_code == 200
    assert ai_review.json()["reviewerType"] == "ai"

    mentor_review = client.post(
        f"/api/v1/submissions/{submission_id}/mentor-review",
        headers=mentor_headers,
        json={"status": "approved", "comments": "Looks good"},
    )
    assert mentor_review.status_code == 200
    assert mentor_review.json()["reviewerType"] == "mentor"

    evidence = client.get("/api/v1/evidence", headers=admin_headers)
    assert evidence.status_code == 200

    requirement = client.post(
        "/api/v1/requirements",
        headers=admin_headers,
        json={
            "title": "RAG評価支援",
            "description": "顧客RAGの検索精度評価",
            "requiredSkills": ["Python", "RAG", "評価"],
        },
    )
    assert requirement.status_code == 200
    requirement_id = requirement.json()["id"]

    fit = client.post(f"/api/v1/requirements/{requirement_id}/assess", headers=admin_headers, json={})
    assert fit.status_code == 200

    fit_list = client.get("/api/v1/fit-assessments", headers=admin_headers)
    assert fit_list.status_code == 200
    assert fit_list.json()["items"]

    report = client.post(
        "/api/v1/reports/sales-summary",
        headers=admin_headers,
        json={"requirementId": requirement_id, "learnerId": learner_id},
    )
    assert report.status_code == 200
    report_id = report.json()["id"]

    export_job = client.post(
        f"/api/v1/reports/{report_id}/export",
        headers=admin_headers,
        json={"reportFormat": "csv"},
    )
    assert export_job.status_code == 200
    assert export_job.json()["status"] == "completed"


def test_team_management_and_csv_invites() -> None:
    client = TestClient(app)
    admin_headers = sign_in(client, "admin@example.com", "Admin123!")
    learner_headers = sign_in(client, "learner@example.com", "Learner123!")

    create_team = client.post(
        "/api/v1/company/teams",
        headers=admin_headers,
        json={"name": "新規チーム", "description": "検証用"},
    )
    assert create_team.status_code == 200

    invite = client.post(
        "/api/v1/company/invites",
        headers=admin_headers,
        json={"email": "new-member@example.com", "role": "learner"},
    )
    assert invite.status_code == 200
    assert invite.json()["status"] == "invited"

    csv_invite = client.post(
        "/api/v1/company/invites/csv-import",
        headers=admin_headers,
        json={"csvContent": "a@example.com\ninvalid\nb@example.com", "defaultRole": "learner"},
    )
    assert csv_invite.status_code == 200
    assert len(csv_invite.json()["created"]) == 2
    assert "invalid" in csv_invite.json()["skipped"]

    forbidden = client.post(
        "/api/v1/company/teams",
        headers=learner_headers,
        json={"name": "forbidden", "description": None},
    )
    assert forbidden.status_code == 403


def test_rbac_and_tenant_boundaries_negative_paths() -> None:
    client = TestClient(app)
    learner_headers = sign_in(client, "learner@example.com", "Learner123!")
    admin_headers = sign_in(client, "admin@example.com", "Admin123!")

    assert client.get("/api/v1/company/teams", headers=learner_headers).status_code == 403
    assert client.get("/api/v1/admin/task-templates", headers=learner_headers).status_code == 403
    assert client.get("/api/v1/company/settings", headers=admin_headers).status_code == 200


def test_exercise_engines_cover_notebook_sql_rag_ocr() -> None:
    client = TestClient(app)
    learner_headers = sign_in(client, "learner@example.com", "Learner123!")

    notebook_run = client.post(
        "/api/v1/exercises/ex-notebook-001/run",
        headers=learner_headers,
        json={"code": "scores=[0.7,0.8]\nprint('avg_score=0.75')"},
    )
    assert notebook_run.status_code == 200
    assert notebook_run.json()["engine"] == "pyodide"
    assert notebook_run.json()["pipeline"] == "notebook"

    sql_run = client.post(
        "/api/v1/exercises/ex-sql-001/run",
        headers=learner_headers,
        json={"code": "SELECT learner_id, completed_items FROM progress_events"},
    )
    assert sql_run.status_code == 200
    assert sql_run.json()["engine"] == "pyodide"
    assert sql_run.json()["pipeline"] == "sql"

    rag_run = client.post(
        "/api/v1/exercises/ex-rag-001/run",
        headers=learner_headers,
        json={
            "code": (
                "OUTPUT={'queries':["
                "{'relevant':'doc-1','retrieved':['doc-1','doc-2']},"
                "{'relevant':'doc-3','retrieved':['doc-3','doc-4']}"
                "]}"
            )
        },
    )
    assert rag_run.status_code == 200
    assert rag_run.json()["engine"] == "docker_sandbox"
    assert rag_run.json()["pipeline"] == "rag"

    ocr_run = client.post(
        "/api/v1/exercises/ex-ocr-001/run",
        headers=learner_headers,
        json={"code": "OUTPUT={'vendor':'A Corp','amount':1000,'date':'2026-05-01'}"},
    )
    assert ocr_run.status_code == 200
    assert ocr_run.json()["engine"] == "docker_sandbox"
    assert ocr_run.json()["pipeline"] == "ocr"


def test_notification_delivery_job_queue_flow() -> None:
    client = TestClient(app)
    learner_headers = sign_in(client, "learner@example.com", "Learner123!")

    submit = client.post(
        "/api/v1/exercises/ex-notebook-001/submit",
        headers=learner_headers,
        json={"code": "scores=[0.9]\nprint('avg_score=0.90')"},
    )
    assert submit.status_code == 200

    jobs = CONTAINER.b2b_service.repository.reserve_notification_jobs(limit=10)
    assert jobs
    first = jobs[0]
    CONTAINER.b2b_service.repository.create_in_app_notification(
        tenant_id=first["tenantId"],
        user_id=first["userId"],
        category=first["category"],
        title=first["title"],
        body=first["body"],
        target_url=first["targetUrl"],
        is_important=first["isImportant"],
    )
    CONTAINER.b2b_service.repository.mark_notification_job_completed(
        job_id=first["id"],
        result={"deliveredChannels": ["in_app"]},
    )

    notifications = client.get("/api/v1/notifications", headers=learner_headers)
    assert notifications.status_code == 200
    assert notifications.json()["items"]


def test_admin_audit_log_filter_by_resource() -> None:
    client = TestClient(app)
    admin_headers = sign_in(client, "admin@example.com", "Admin123!")
    create_team = client.post(
        "/api/v1/company/teams",
        headers=admin_headers,
        json={"name": "監査テストチーム", "description": "log-check"},
    )
    assert create_team.status_code == 200

    audit_logs = client.get(
        "/api/v1/admin/audit-logs",
        headers=admin_headers,
        params={"resourceType": "team"},
    )
    assert audit_logs.status_code == 200
