from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from infrastructure.auth import hash_password
from infrastructure.exercise_execution import ExerciseExecutionGateway, ExerciseExecutionResult
from infrastructure.settings import load_settings
from infrastructure.sql_models import (
    AuditLogModel,
    CurriculumVersionModel,
    EvidenceModel,
    ExerciseModel,
    FitAssessmentModel,
    InviteModel,
    LearnerProfileModel,
    ReportJobModel,
    RequirementModel,
    ReviewModel,
    RoleTemplateModel,
    RoadmapAssignmentModel,
    NotificationInboxModel,
    NotificationDeliveryJobModel,
    NotificationDeliverySettingModel,
    SubmissionModel,
    TeamMemberModel,
    TeamModel,
    UserModel,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PostgresB2BRepository:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._executor = ExerciseExecutionGateway(load_settings())

    def seed_if_empty(self, tenant_id: str = "company-demo") -> None:
        if self._db.scalar(select(UserModel).limit(1)) is not None:
            return
        users = [
            UserModel(
                user_id="admin-user",
                email="admin@example.com",
                display_name="Platform Admin",
                role="admin",
                state="active",
                tenant_id=tenant_id,
                password_hash=hash_password("Admin123!"),
            ),
            UserModel(
                user_id="recruiter-user",
                email="recruiter@example.com",
                display_name="Recruiter User",
                role="recruiter",
                state="active",
                tenant_id=tenant_id,
                password_hash=hash_password("Recruiter123!"),
            ),
            UserModel(
                user_id="demo-user",
                email="learner@example.com",
                display_name="Demo Learner",
                role="learner",
                state="active",
                tenant_id=tenant_id,
                password_hash=hash_password("Learner123!"),
            ),
            UserModel(
                user_id="mentor-user",
                email="mentor@example.com",
                display_name="Mentor User",
                role="mentor",
                state="active",
                tenant_id=tenant_id,
                password_hash=hash_password("Mentor123!"),
            ),
        ]
        self._db.add_all(users)
        self._db.flush()
        self._db.add_all(
            [
                LearnerProfileModel(
                    user_id="demo-user",
                    tenant_id=tenant_id,
                    team_name="DX推進チーム",
                    target_role="RAG検証補助",
                    roadmap_completion_rate=62,
                    readiness="Almost",
                    pending_submission_count=1,
                    strong_skills=["Python", "RAG評価"],
                    gap_skills=["SQL", "可視化"],
                ),
                LearnerProfileModel(
                    user_id="mentor-user",
                    tenant_id=tenant_id,
                    team_name="業務改善チーム",
                    target_role="データ分析補助",
                    roadmap_completion_rate=38,
                    readiness="Need Training",
                    pending_submission_count=2,
                    strong_skills=["Python基礎"],
                    gap_skills=["pandas", "業務課題分解"],
                ),
            ]
        )
        self._db.add_all(
            [
                TeamModel(
                    id="team-dx",
                    tenant_id=tenant_id,
                    name="DX推進チーム",
                    description="RAG/評価改善を担当",
                ),
                TeamModel(
                    id="team-business",
                    tenant_id=tenant_id,
                    name="業務改善チーム",
                    description="業務分析と自動化を担当",
                ),
            ]
        )
        self._db.flush()
        self._db.add_all(
            [
                TeamMemberModel(id="tm-001", team_id="team-dx", user_id="demo-user"),
                TeamMemberModel(id="tm-002", team_id="team-business", user_id="mentor-user"),
            ]
        )
        self._db.add_all(
            [
                RoleTemplateModel(
                    id="role-rag",
                    tenant_id=tenant_id,
                    code="rag_assistant",
                    name="RAG検証補助",
                    description="検索評価・回答根拠検証を担当",
                    target_skills=["python", "rag", "evaluation"],
                ),
                RoleTemplateModel(
                    id="role-data",
                    tenant_id=tenant_id,
                    code="data_analyst_assistant",
                    name="データ分析補助",
                    description="集計・可視化・示唆抽出を担当",
                    target_skills=["python", "sql", "pandas"],
                ),
            ]
        )
        self._db.add_all(
            [
                ExerciseModel(
                    id="ex-notebook-001",
                    tenant_id=tenant_id,
                    kind="notebook",
                    title="Notebook: RAG評価実験",
                    prompt="評価メトリクスを集計し、改善示唆をまとめる",
                    starter_code=(
                        "scores = [0.72, 0.81, 0.67]\n"
                        "avg = sum(scores) / len(scores)\n"
                        "print(f'avg_score={avg:.2f}')\n"
                    ),
                    metadata_json={"language": "python", "requiredOutputKeyword": "avg_score"},
                ),
                ExerciseModel(
                    id="ex-sql-001",
                    tenant_id=tenant_id,
                    kind="sql",
                    title="SQL: 学習進捗クエリ演習",
                    prompt="受講者ごとの完了率を算出するSQLを作成",
                    starter_code=(
                        "SELECT learner_id,\n"
                        "       completed_items,\n"
                        "       total_items,\n"
                        "       ROUND(100.0 * completed_items / total_items, 1) AS completion_rate\n"
                        "FROM progress_events\n"
                        "ORDER BY completion_rate DESC;"
                    ),
                    metadata_json={"dialect": "postgres"},
                ),
                ExerciseModel(
                    id="ex-rag-001",
                    tenant_id=tenant_id,
                    kind="rag",
                    title="RAG: 検索精度評価",
                    prompt="Hit@K / MRR を算出し評価レポートを作る",
                    starter_code=(
                        "OUTPUT = {\n"
                        "    'queries': [\n"
                        "        {'relevant': 'doc-2', 'retrieved': ['doc-2', 'doc-5', 'doc-1']},\n"
                        "        {'relevant': 'doc-4', 'retrieved': ['doc-7', 'doc-4', 'doc-2']},\n"
                        "    ]\n"
                        "}\n"
                    ),
                    metadata_json={"dataset": "faq_v1", "minHitAtK": 0.5, "minMRR": 0.4},
                ),
                ExerciseModel(
                    id="ex-ocr-001",
                    tenant_id=tenant_id,
                    kind="ocr",
                    title="OCR: 請求書テキスト抽出",
                    prompt="OCR抽出結果から構造化JSONを生成",
                    starter_code=(
                        "OUTPUT = {\n"
                        "    'vendor': 'Newfan Supplies',\n"
                        "    'amount': 128000,\n"
                        "    'date': '2026-05-20'\n"
                        "}\n"
                    ),
                    metadata_json={"format": "invoice"},
                ),
            ]
        )
        self._db.add(
            RequirementModel(
                id="req-demo-001",
                tenant_id=tenant_id,
                title="FAQ RAG検証支援",
                description="受注案件のPoC事前検証",
                required_skills=["Python", "RAG", "評価"],
            )
        )
        self._db.add(
            CurriculumVersionModel(
                id="cv-python-fastapi-1",
                tenant_id=tenant_id,
                curriculum_slug="python-fastapi",
                version="1.0.0",
                title="FastAPI 入門",
                mdx_path="content/curriculum/python-fastapi/intro-v1.mdx",
                skill_tags=["python.api.fastapi"],
                difficulty=2,
                estimated_minutes=35,
                published=True,
            )
        )
        self._db.add_all(
            [
                NotificationDeliverySettingModel(
                    id=f"nds-{uuid4().hex[:8]}",
                    tenant_id=tenant_id,
                    user_id="demo-user",
                    category="learning",
                    email_enabled=False,
                    in_app_enabled=True,
                    push_enabled=True,
                ),
                NotificationDeliverySettingModel(
                    id=f"nds-{uuid4().hex[:8]}",
                    tenant_id=tenant_id,
                    user_id="demo-user",
                    category="career",
                    email_enabled=True,
                    in_app_enabled=True,
                    push_enabled=False,
                ),
            ]
        )
        self._db.commit()

    def get_user_by_user_id(self, user_id: str) -> UserModel | None:
        return self._db.get(UserModel, user_id)

    def get_user_by_email(self, email: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.email == email)
        return self._db.scalar(stmt)

    def create_user(
        self,
        *,
        user_id: str,
        email: str,
        display_name: str,
        role: str,
        tenant_id: str,
        password_hash_value: str,
    ) -> UserModel:
        user = UserModel(
            user_id=user_id,
            email=email,
            display_name=display_name,
            role=role,
            tenant_id=tenant_id,
            state="active",
            password_hash=password_hash_value,
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def list_learners(self, tenant_id: str) -> list[dict]:
        stmt = (
            select(UserModel, LearnerProfileModel)
            .join(LearnerProfileModel, LearnerProfileModel.user_id == UserModel.user_id)
            .where(UserModel.tenant_id == tenant_id)
            .where(UserModel.role == "learner")
        )
        values: list[dict] = []
        for user, profile in self._db.execute(stmt).all():
            values.append(
                {
                    "id": user.user_id,
                    "name": user.display_name,
                    "teamName": profile.team_name,
                    "targetRole": profile.target_role,
                    "roadmapCompletionRate": profile.roadmap_completion_rate,
                    "readiness": profile.readiness,
                    "pendingSubmissionCount": profile.pending_submission_count,
                    "strongSkills": profile.strong_skills,
                    "gapSkills": profile.gap_skills,
                }
            )
        return values

    def list_teams(self, tenant_id: str) -> list[dict]:
        stmt = select(TeamModel).where(TeamModel.tenant_id == tenant_id)
        teams = self._db.scalars(stmt).all()
        return [
            {
                "id": value.id,
                "name": value.name,
                "description": value.description,
            }
            for value in teams
        ]

    def create_team(self, tenant_id: str, name: str, description: str | None) -> dict:
        value = TeamModel(
            id=f"team-{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            name=name,
            description=description,
        )
        self._db.add(value)
        self._db.commit()
        return {"id": value.id, "name": value.name, "description": value.description}

    def invite_user(
        self,
        *,
        tenant_id: str,
        email: str,
        role: str,
        invited_by: str,
        team_id: str | None = None,
    ) -> dict:
        invite = InviteModel(
            id=f"invite-{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            email=email,
            role=role,
            team_id=team_id,
            token=f"invite-token-{uuid4().hex}",
            status="invited",
            invited_by=invited_by,
        )
        self._db.add(invite)
        self._db.commit()
        return {
            "id": invite.id,
            "email": invite.email,
            "role": invite.role,
            "teamId": invite.team_id,
            "status": invite.status,
            "token": invite.token,
        }

    def list_role_templates(self, tenant_id: str) -> list[dict]:
        stmt = select(RoleTemplateModel).where(RoleTemplateModel.tenant_id == tenant_id)
        values = self._db.scalars(stmt).all()
        return [
            {
                "id": value.id,
                "code": value.code,
                "name": value.name,
                "description": value.description,
                "targetSkills": value.target_skills,
            }
            for value in values
        ]

    def assign_roadmap(self, tenant_id: str, learner_id: str, role_template_id: str) -> dict:
        assignment_id = f"roadmap-{learner_id}-{role_template_id}-{uuid4().hex[:6]}"
        value = RoadmapAssignmentModel(
            id=assignment_id,
            tenant_id=tenant_id,
            learner_id=learner_id,
            role_template_id=role_template_id,
            status="assigned",
        )
        self._db.add(value)
        self._db.commit()
        return {"roadmapId": assignment_id, "status": "assigned"}

    def list_exercises(self, tenant_id: str) -> list[dict]:
        stmt = select(ExerciseModel).where(ExerciseModel.tenant_id == tenant_id)
        values = self._db.scalars(stmt).all()
        return [
            {
                "id": value.id,
                "kind": value.kind,
                "title": value.title,
                "prompt": value.prompt,
                "starterCode": value.starter_code,
                "metadata": value.metadata_json,
            }
            for value in values
        ]

    def get_exercise(self, tenant_id: str, exercise_id: str) -> dict | None:
        stmt = select(ExerciseModel).where(
            ExerciseModel.tenant_id == tenant_id,
            ExerciseModel.id == exercise_id,
        )
        value = self._db.scalar(stmt)
        if value is None:
            return None
        return {
            "id": value.id,
            "kind": value.kind,
            "title": value.title,
            "prompt": value.prompt,
            "starterCode": value.starter_code,
            "metadata": value.metadata_json,
        }

    def run_exercise(self, tenant_id: str, exercise_id: str, code: str) -> dict:
        exercise = self.get_exercise(tenant_id=tenant_id, exercise_id=exercise_id)
        if exercise is None:
            raise ValueError("Exercise not found")
        result = self._executor.run(exercise=exercise, code=code)
        return self._execution_result_to_response(result)

    def create_submission(self, tenant_id: str, exercise_id: str, learner_id: str, code: str) -> dict:
        execution = self.run_exercise(tenant_id=tenant_id, exercise_id=exercise_id, code=code)
        submission_id = f"submission-{uuid4().hex[:8]}"
        value = SubmissionModel(
            id=submission_id,
            tenant_id=tenant_id,
            exercise_id=exercise_id,
            learner_id=learner_id,
            status="submitted" if execution["status"] == "passed" else "needs_resubmit",
            code=code,
            execution_status=execution["status"],
            execution_stdout=execution["stdout"],
            execution_stderr=execution["stderr"],
            execution_engine=execution["engine"],
            execution_pipeline=execution["pipeline"],
            execution_details_json=execution["details"],
        )
        self._db.add(value)
        self._db.commit()
        return {
            "id": value.id,
            "exerciseId": value.exercise_id,
            "learnerId": value.learner_id,
            "status": value.status,
            "code": value.code,
            "executionStatus": value.execution_status,
            "executionStdout": value.execution_stdout,
            "executionStderr": value.execution_stderr,
            "executionEngine": value.execution_engine,
            "executionPipeline": value.execution_pipeline,
            "executionDetails": value.execution_details_json,
            "createdAt": _now_iso(),
        }

    def list_submissions(self, tenant_id: str) -> list[dict]:
        stmt = select(SubmissionModel).where(SubmissionModel.tenant_id == tenant_id)
        values = self._db.scalars(stmt).all()
        return [
            {
                "id": value.id,
                "exerciseId": value.exercise_id,
                "learnerId": value.learner_id,
                "status": value.status,
                "code": value.code,
                "executionStatus": value.execution_status,
                "executionStdout": value.execution_stdout,
                "executionStderr": value.execution_stderr,
                "executionEngine": value.execution_engine,
                "executionPipeline": value.execution_pipeline,
                "executionDetails": value.execution_details_json,
                "createdAt": _now_iso(),
            }
            for value in values
        ]

    @staticmethod
    def _execution_result_to_response(result: ExerciseExecutionResult) -> dict:
        return {
            "status": result.status,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "engine": result.engine,
            "pipeline": result.pipeline,
            "details": result.details,
        }

    def create_review(
        self,
        *,
        tenant_id: str,
        submission_id: str,
        reviewer_type: str,
        status: str,
        score: int,
        comments: str,
    ) -> dict:
        review = ReviewModel(
            id=f"review-{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            submission_id=submission_id,
            reviewer_type=reviewer_type,
            status=status,
            score=score,
            comments=comments,
        )
        self._db.add(review)
        self._db.commit()
        return {
            "submissionId": review.submission_id,
            "reviewerType": review.reviewer_type,
            "status": review.status,
            "score": review.score,
            "comments": review.comments,
        }

    def list_evidence(self, tenant_id: str) -> list[dict]:
        stmt = select(EvidenceModel).where(EvidenceModel.tenant_id == tenant_id)
        values = self._db.scalars(stmt).all()
        return [
            {
                "id": value.id,
                "learnerId": value.learner_id,
                "title": value.title,
                "summary": value.summary,
                "skillTags": value.skill_tags,
                "strength": value.strength,
                "reviewType": value.review_type,
                "status": value.status,
                "useCase": value.use_case,
                "rubricSummary": value.rubric_summary,
                "exerciseId": value.exercise_id,
                "submissionId": value.submission_id,
                "score": value.score,
                "submittedAt": _now_iso(),
                "updatedAt": _now_iso(),
                "relatedRequirementIds": value.related_requirement_ids,
            }
            for value in values
        ]

    def append_evidence(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        title: str,
        summary: str,
        skill_tags: list[str],
        strength: str,
        review_type: str | None,
        status: str,
        exercise_id: str | None,
        submission_id: str | None,
        score: int | None,
    ) -> dict:
        value = EvidenceModel(
            id=f"evidence-{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            learner_id=learner_id,
            title=title,
            summary=summary,
            skill_tags=skill_tags,
            strength=strength,
            review_type=review_type,
            status=status,
            use_case="業務適用シーンを含む成果",
            rubric_summary="自動評価",
            exercise_id=exercise_id,
            submission_id=submission_id,
            score=score,
            submitted_at=datetime.now(timezone.utc),
            related_requirement_ids=[],
        )
        self._db.add(value)
        self._db.commit()
        return {"id": value.id}

    def create_requirement(self, tenant_id: str, title: str, description: str, required_skills: list[str]) -> dict:
        value = RequirementModel(
            id=f"req-{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            title=title,
            description=description,
            required_skills=required_skills,
        )
        self._db.add(value)
        self._db.commit()
        return {
            "id": value.id,
            "title": value.title,
            "description": value.description,
            "requiredSkills": value.required_skills,
        }

    def list_requirements(self, tenant_id: str) -> list[dict]:
        stmt = select(RequirementModel).where(RequirementModel.tenant_id == tenant_id)
        values = self._db.scalars(stmt).all()
        return [
            {
                "id": value.id,
                "title": value.title,
                "description": value.description,
                "requiredSkills": value.required_skills,
            }
            for value in values
        ]

    def create_fit_assessment(
        self,
        *,
        tenant_id: str,
        requirement_id: str,
        recommended_learner_id: str,
        fit_score: int,
        matched_skills: list[str],
        gap_skills: list[str],
    ) -> dict:
        value = FitAssessmentModel(
            id=f"fit-{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            requirement_id=requirement_id,
            recommended_learner_id=recommended_learner_id,
            fit_score=fit_score,
            matched_skills=matched_skills,
            gap_skills=gap_skills,
        )
        self._db.add(value)
        self._db.commit()
        return {
            "requirementId": value.requirement_id,
            "fitScore": value.fit_score,
            "matchedSkills": value.matched_skills,
            "gapSkills": value.gap_skills,
            "recommendedLearnerId": value.recommended_learner_id,
        }

    def list_fit_assessments(self, tenant_id: str) -> list[dict]:
        stmt = select(FitAssessmentModel).where(FitAssessmentModel.tenant_id == tenant_id)
        values = self._db.scalars(stmt).all()
        return [
            {
                "id": value.id,
                "requirementId": value.requirement_id,
                "fitScore": value.fit_score,
                "matchedSkills": value.matched_skills,
                "gapSkills": value.gap_skills,
                "recommendedLearnerId": value.recommended_learner_id,
                "createdAt": _now_iso(),
            }
            for value in values
        ]

    def create_report_job(
        self,
        *,
        tenant_id: str,
        report_id: str,
        report_format: str,
        payload: dict,
    ) -> dict:
        job = ReportJobModel(
            id=f"job-{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            report_id=report_id,
            report_format=report_format,
            status="queued",
            payload=payload,
        )
        self._db.add(job)
        self._db.commit()
        return {"jobId": job.id, "status": job.status, "reportId": report_id, "format": report_format}

    def complete_report_job(self, tenant_id: str, job_id: str, result_url: str) -> dict:
        job = self._db.get(ReportJobModel, job_id)
        if job is None or job.tenant_id != tenant_id:
            raise ValueError("Report job not found")
        job.status = "completed"
        job.result_url = result_url
        job.updated_at = datetime.now(timezone.utc)
        self._db.add(job)
        self._db.commit()
        return {
            "jobId": job.id,
            "status": job.status,
            "resultUrl": job.result_url,
            "reportId": job.report_id,
        }

    def list_curriculum_versions(self, tenant_id: str) -> list[dict]:
        stmt = select(CurriculumVersionModel).where(CurriculumVersionModel.tenant_id == tenant_id)
        values = self._db.scalars(stmt).all()
        return [
            {
                "id": value.id,
                "curriculumSlug": value.curriculum_slug,
                "version": value.version,
                "title": value.title,
                "mdxPath": value.mdx_path,
                "published": value.published,
                "skillTags": value.skill_tags,
                "difficulty": value.difficulty,
                "estimatedMinutes": value.estimated_minutes,
            }
            for value in values
        ]

    def publish_curriculum(self, tenant_id: str, payload: dict) -> dict:
        value = CurriculumVersionModel(
            id=f"cv-{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            curriculum_slug=payload["curriculumSlug"],
            version=payload["version"],
            title=payload["title"],
            mdx_path=payload["mdxPath"],
            skill_tags=payload["skillTags"],
            difficulty=payload["difficulty"],
            estimated_minutes=payload["estimatedMinutes"],
            published=True,
        )
        self._db.add(value)
        self._db.commit()
        return {
            "id": value.id,
            "curriculumSlug": value.curriculum_slug,
            "version": value.version,
            "title": value.title,
            "mdxPath": value.mdx_path,
            "published": value.published,
            "skillTags": value.skill_tags,
            "difficulty": value.difficulty,
            "estimatedMinutes": value.estimated_minutes,
        }

    def append_audit_log(
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
        metadata: dict[str, str] | None = None,
    ) -> None:
        value = AuditLogModel(
            id=f"audit-{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            summary=summary,
            metadata_json=metadata or {},
        )
        self._db.add(value)
        self._db.commit()

    def list_audit_logs(
        self,
        *,
        tenant_id: str,
        limit: int = 100,
        event_type: str | None = None,
        actor_user_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        occurred_from: str | None = None,
        occurred_to: str | None = None,
    ) -> list[dict]:
        conditions = [AuditLogModel.tenant_id == tenant_id]
        if event_type:
            conditions.append(AuditLogModel.event_type == event_type)
        if actor_user_id:
            conditions.append(AuditLogModel.actor_user_id == actor_user_id)
        if resource_type:
            conditions.append(AuditLogModel.resource_type == resource_type)
        if resource_id:
            conditions.append(AuditLogModel.resource_id == resource_id)
        if occurred_from:
            conditions.append(AuditLogModel.occurred_at >= occurred_from)
        if occurred_to:
            conditions.append(AuditLogModel.occurred_at <= occurred_to)
        stmt = (
            select(AuditLogModel)
            .where(and_(*conditions))
            .order_by(AuditLogModel.occurred_at.desc())
            .limit(min(max(limit, 1), 500))
        )
        values = self._db.scalars(stmt).all()
        return [
            {
                "id": value.id,
                "eventType": value.event_type,
                "resourceType": value.resource_type,
                "resourceId": value.resource_id,
                "action": value.action,
                "actorUserId": value.actor_user_id,
                "actorRole": value.actor_role,
                "summary": value.summary,
                "metadata": value.metadata_json,
                "occurredAt": value.occurred_at.isoformat() if hasattr(value.occurred_at, "isoformat") else str(value.occurred_at),
            }
            for value in values
        ]

    def create_in_app_notification(
        self,
        *,
        tenant_id: str,
        user_id: str,
        category: str,
        title: str,
        body: str,
        target_url: str,
        is_important: bool = False,
    ) -> dict:
        value = NotificationInboxModel(
            id=f"notif-{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            user_id=user_id,
            category=category,
            title=title,
            body=body,
            target_url=target_url,
            is_important=is_important,
        )
        self._db.add(value)
        self._db.commit()
        return {"id": value.id}

    def enqueue_notification_job(
        self,
        *,
        tenant_id: str,
        user_id: str,
        category: str,
        title: str,
        body: str,
        target_url: str,
        channels: list[str],
        is_important: bool = False,
    ) -> dict:
        value = NotificationDeliveryJobModel(
            id=f"ndj-{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            user_id=user_id,
            category=category,
            title=title,
            body=body,
            target_url=target_url,
            channels=channels,
            is_important=is_important,
            status="queued",
        )
        self._db.add(value)
        self._db.commit()
        return {"id": value.id, "status": value.status}

    def reserve_notification_jobs(self, *, limit: int = 10) -> list[dict]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(NotificationDeliveryJobModel)
            .where(
                and_(
                    NotificationDeliveryJobModel.status.in_(["queued", "retrying"]),
                    NotificationDeliveryJobModel.available_at <= now,
                )
            )
            .order_by(NotificationDeliveryJobModel.available_at.asc())
            .limit(max(1, limit))
            .with_for_update(skip_locked=True)
        )
        values = self._db.scalars(stmt).all()
        jobs: list[dict] = []
        for value in values:
            value.status = "processing"
            value.attempt_count = (value.attempt_count or 0) + 1
            value.updated_at = now
            jobs.append(
                {
                    "id": value.id,
                    "tenantId": value.tenant_id,
                    "userId": value.user_id,
                    "category": value.category,
                    "title": value.title,
                    "body": value.body,
                    "targetUrl": value.target_url,
                    "channels": value.channels,
                    "isImportant": value.is_important,
                    "attemptCount": value.attempt_count,
                }
            )
        self._db.commit()
        return jobs

    def mark_notification_job_completed(self, *, job_id: str, result: dict) -> None:
        value = self._db.get(NotificationDeliveryJobModel, job_id)
        if value is None:
            return
        value.status = "completed"
        value.result_json = result
        value.updated_at = datetime.now(timezone.utc)
        self._db.add(value)
        self._db.commit()

    def mark_notification_job_failed(
        self,
        *,
        job_id: str,
        error_message: str,
        max_retries: int,
        next_retry_at: datetime,
    ) -> None:
        value = self._db.get(NotificationDeliveryJobModel, job_id)
        if value is None:
            return
        if (value.attempt_count or 0) >= max_retries:
            value.status = "failed"
        else:
            value.status = "retrying"
            value.available_at = next_retry_at
        value.last_error = error_message
        value.updated_at = datetime.now(timezone.utc)
        self._db.add(value)
        self._db.commit()

    def list_notifications(self, *, tenant_id: str, user_id: str, tab: str = "all", unread_only: bool = False) -> dict:
        conditions = [NotificationInboxModel.tenant_id == tenant_id, NotificationInboxModel.user_id == user_id]
        if tab != "all":
            conditions.append(NotificationInboxModel.category == tab)
        if unread_only:
            conditions.append(NotificationInboxModel.read_at.is_(None))
        stmt = (
            select(NotificationInboxModel)
            .where(and_(*conditions))
            .order_by(NotificationInboxModel.created_at.desc())
        )
        values = self._db.scalars(stmt).all()
        unread_count = self._db.query(NotificationInboxModel).filter(
            NotificationInboxModel.tenant_id == tenant_id,
            NotificationInboxModel.user_id == user_id,
            NotificationInboxModel.read_at.is_(None),
        ).count()
        return {
            "userId": user_id,
            "unreadCount": unread_count,
            "items": [
                {
                    "id": value.id,
                    "category": value.category,
                    "title": value.title,
                    "body": value.body,
                    "targetUrl": value.target_url,
                    "isImportant": value.is_important,
                    "readAt": value.read_at.isoformat() if value.read_at else None,
                    "createdAt": value.created_at.isoformat() if hasattr(value.created_at, "isoformat") else str(value.created_at),
                }
                for value in values
            ],
        }

    def mark_notification_read(self, *, tenant_id: str, user_id: str, notification_id: str) -> dict | None:
        stmt = select(NotificationInboxModel).where(
            NotificationInboxModel.tenant_id == tenant_id,
            NotificationInboxModel.user_id == user_id,
            NotificationInboxModel.id == notification_id,
        )
        value = self._db.scalar(stmt)
        if value is None:
            return None
        if value.read_at is None:
            value.read_at = datetime.now(timezone.utc)
            self._db.add(value)
            self._db.commit()
        return {"id": value.id, "readAt": value.read_at.isoformat() if value.read_at else None}

    def mark_all_notifications_read(self, *, tenant_id: str, user_id: str) -> int:
        stmt = select(NotificationInboxModel).where(
            NotificationInboxModel.tenant_id == tenant_id,
            NotificationInboxModel.user_id == user_id,
            NotificationInboxModel.read_at.is_(None),
        )
        values = self._db.scalars(stmt).all()
        now = datetime.now(timezone.utc)
        for value in values:
            value.read_at = now
            self._db.add(value)
        self._db.commit()
        return len(values)

    def list_notification_delivery_settings(self, *, tenant_id: str, user_id: str) -> dict:
        categories = ["learning", "career", "dm", "admin"]
        stmt = select(NotificationDeliverySettingModel).where(
            NotificationDeliverySettingModel.tenant_id == tenant_id,
            NotificationDeliverySettingModel.user_id == user_id,
        )
        values = self._db.scalars(stmt).all()
        by_category = {value.category: value for value in values}
        items: list[dict] = []
        for category in categories:
            value = by_category.get(category)
            items.append(
                {
                    "category": category,
                    "emailEnabled": value.email_enabled if value else False,
                    "inAppEnabled": value.in_app_enabled if value else True,
                    "pushEnabled": value.push_enabled if value else False,
                    "updatedAt": (
                        value.updated_at.isoformat()
                        if value and hasattr(value.updated_at, "isoformat")
                        else None
                    ),
                }
            )
        return {"userId": user_id, "items": items}

    def upsert_notification_delivery_setting(
        self,
        *,
        tenant_id: str,
        user_id: str,
        category: str,
        email_enabled: bool,
        in_app_enabled: bool,
        push_enabled: bool,
    ) -> dict:
        stmt = select(NotificationDeliverySettingModel).where(
            NotificationDeliverySettingModel.tenant_id == tenant_id,
            NotificationDeliverySettingModel.user_id == user_id,
            NotificationDeliverySettingModel.category == category,
        )
        value = self._db.scalar(stmt)
        if value is None:
            value = NotificationDeliverySettingModel(
                id=f"nds-{uuid4().hex[:8]}",
                tenant_id=tenant_id,
                user_id=user_id,
                category=category,
            )
        value.email_enabled = email_enabled
        value.in_app_enabled = in_app_enabled
        value.push_enabled = push_enabled
        value.updated_at = datetime.now(timezone.utc)
        self._db.add(value)
        self._db.commit()
        return {
            "category": value.category,
            "emailEnabled": value.email_enabled,
            "inAppEnabled": value.in_app_enabled,
            "pushEnabled": value.push_enabled,
            "updatedAt": value.updated_at.isoformat() if hasattr(value.updated_at, "isoformat") else str(value.updated_at),
        }
