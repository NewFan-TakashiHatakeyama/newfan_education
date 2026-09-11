from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import HTTPException
from infrastructure.sql_models import ApplicationRecordModel
from sqlalchemy import select

from domain.models import UserContext
from infrastructure.postgres_b2b import PostgresB2BRepository


@dataclass
class B2BService:
    repository: PostgresB2BRepository

    def _assert_roles(self, actor: UserContext, allowed: set[str]) -> None:
        if actor.role not in allowed:
            raise PermissionError("Role is not allowed")

    def get_current_company(self, actor: UserContext, company_id: str) -> dict:
        self._assert_roles(actor, {"admin", "recruiter", "content_editor"})
        return {
            "id": actor.tenant_id,
            "name": "Newfan Demo Company",
            "plan": "team",
            "status": "active",
            "activeLearnerCount": len(self.repository.list_learners(actor.tenant_id)),
        }

    def list_learners(self, actor: UserContext, company_id: str) -> dict:
        self._assert_roles(actor, {"admin", "recruiter", "content_editor"})
        return {"items": self.repository.list_learners(actor.tenant_id)}

    def get_learner_detail(self, actor: UserContext, company_id: str, learner_id: str) -> dict:
        self._assert_roles(actor, {"admin", "recruiter", "content_editor"})
        learners = self.repository.list_learners(actor.tenant_id)
        value = next((item for item in learners if item["id"] == learner_id), None)
        if value is None:
            raise ValueError("Learner not found")
        return value

    def list_role_templates(self, actor: UserContext, company_id: str) -> dict:
        self._assert_roles(actor, {"admin", "recruiter", "content_editor", "learner"})
        return {"items": self.repository.list_role_templates(actor.tenant_id)}

    def assign_roadmap(self, actor: UserContext, company_id: str, learner_id: str, role_template_id: str) -> dict:
        self._assert_roles(actor, {"admin", "recruiter", "content_editor"})
        return self.repository.assign_roadmap(actor.tenant_id, learner_id, role_template_id)

    def list_teams(self, actor: UserContext) -> dict:
        self._assert_roles(actor, {"admin", "recruiter", "content_editor"})
        return {"items": self.repository.list_teams(actor.tenant_id)}

    def create_team(self, actor: UserContext, name: str, description: str | None) -> dict:
        self._assert_roles(actor, {"admin", "recruiter"})
        return self.repository.create_team(actor.tenant_id, name, description)

    def invite_user(self, actor: UserContext, email: str, role: str, team_id: str | None) -> dict:
        self._assert_roles(actor, {"admin"})
        return self.repository.invite_user(
            tenant_id=actor.tenant_id,
            email=email,
            role=role,
            invited_by=actor.user_id,
            team_id=team_id,
        )

    def bulk_invite_from_csv(self, actor: UserContext, csv_content: str, default_role: str) -> dict:
        self._assert_roles(actor, {"admin"})
        created: list[dict] = []
        skipped: list[str] = []
        for raw in csv_content.splitlines():
            email = raw.strip()
            if not email or "@" not in email:
                if email:
                    skipped.append(email)
                continue
            created.append(self.invite_user(actor, email=email, role=default_role, team_id=None))
        return {"created": created, "skipped": skipped}

    def list_exercises(self, actor: UserContext) -> dict:
        self._assert_roles(actor, {"learner", "admin", "content_editor", "mentor", "recruiter"})
        return {"items": self.repository.list_exercises(actor.tenant_id)}

    def get_exercise(self, actor: UserContext, company_id: str, exercise_id: str) -> dict:
        self._assert_roles(actor, {"learner", "admin", "content_editor"})
        value = self.repository.get_exercise(actor.tenant_id, exercise_id)
        if value is None:
            raise ValueError("Exercise not found")
        return value

    def run_exercise(self, actor: UserContext, company_id: str, exercise_id: str, code: str) -> dict:
        self._assert_roles(actor, {"learner", "admin", "content_editor"})
        return self.repository.run_exercise(actor.tenant_id, exercise_id, code)

    def submit_exercise(self, actor: UserContext, company_id: str, exercise_id: str, code: str) -> dict:
        self._assert_roles(actor, {"learner", "admin", "content_editor"})
        submission = self.repository.create_submission(actor.tenant_id, exercise_id, actor.user_id, code)
        self.repository.enqueue_notification_job(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            category="learning",
            title="演習を提出しました",
            body=f"{exercise_id} を提出しました。提出内容を確認できます。AI採点は未提供です。",
            target_url=f"/learner/submissions/{submission['id']}",
            channels=["in_app"],
            is_important=submission.get("executionStatus") != "passed",
        )
        return submission

    def list_submissions(self, actor: UserContext, company_id: str) -> dict:
        self._assert_roles(actor, {"mentor", "admin", "content_editor"})
        return {"items": self.repository.list_submissions(actor.tenant_id)}

    def get_submission(self, actor: UserContext, company_id: str, submission_id: str) -> dict:
        self._assert_roles(actor, {"mentor", "admin", "content_editor", "learner"})
        values = self.repository.list_submissions(actor.tenant_id)
        value = next((item for item in values if item["id"] == submission_id), None)
        if value is None:
            raise ValueError("Submission not found")
        if actor.role == "learner" and value["learnerId"] != actor.user_id:
            raise PermissionError("Only the owner or an authorized reviewer can read a submission")
        return value

    def run_ai_review(self, actor: UserContext, company_id: str, submission_id: str) -> dict:
        self._assert_roles(actor, {"learner", "mentor", "admin", "content_editor"})
        self.get_submission(actor, company_id, submission_id)
        raise HTTPException(status_code=503, detail="検証済みの評価器が未接続のためAI採点は利用できません")

    def submit_mentor_review(self, actor: UserContext, company_id: str, submission_id: str, status: str, comments: str) -> dict:
        self._assert_roles(actor, {"mentor", "admin", "content_editor"})
        self.get_submission(actor, company_id, submission_id)
        return self.repository.create_review(
            tenant_id=actor.tenant_id,
            submission_id=submission_id,
            reviewer_type="mentor",
            status=status,
            score=85 if status == "approved" else 60,
            comments=comments,
        )

    def list_evidence(self, actor: UserContext, company_id: str) -> dict:
        self._assert_roles(actor, {"learner", "admin", "recruiter", "content_editor"})
        items = self.repository.list_evidence(actor.tenant_id)
        if actor.role == "learner":
            items = [item for item in items if item["learnerId"] == actor.user_id]
        return {"items": items}

    def create_requirement(self, actor: UserContext, company_id: str, title: str, description: str, required_skills: list[str]) -> dict:
        self._assert_roles(actor, {"admin", "recruiter"})
        return self.repository.create_requirement(actor.tenant_id, title, description, required_skills)

    def list_requirements(self, actor: UserContext, company_id: str) -> dict:
        self._assert_roles(actor, {"admin", "recruiter", "content_editor"})
        return {"items": self.repository.list_requirements(actor.tenant_id)}

    def assess_requirement(self, actor: UserContext, company_id: str, requirement_id: str) -> dict:
        self._assert_roles(actor, {"admin", "recruiter"})
        requirements = self.repository.list_requirements(actor.tenant_id)
        requirement = next((item for item in requirements if item["id"] == requirement_id), None)
        if requirement is None:
            raise ValueError("Requirement not found")
        learners = self.repository.list_learners(actor.tenant_id)
        if not learners:
            raise ValueError("Learner not found")
        evidence = self.repository.list_evidence(actor.tenant_id)
        required = list(dict.fromkeys(requirement["requiredSkills"]))
        def matches(learner):
            verified = {tag for e in evidence if e["learnerId"] == learner["id"]
                and e["status"] == "passed" and e["reviewType"] == "mentor"
                for tag in e["skillTags"]}
            return [skill for skill in required if skill in verified]
        top_learner = sorted(learners, key=lambda l: (-len(matches(l)), l["id"]))[0]
        matched = matches(top_learner)
        return self.repository.create_fit_assessment(tenant_id=actor.tenant_id, requirement_id=requirement_id,
            recommended_learner_id=top_learner["id"], fit_score=round(100 * len(matched) / len(required)) if required else 0,
            matched_skills=matched, gap_skills=[s for s in required if s not in matched])

    def list_fit_assessments(self, actor: UserContext) -> dict:
        self._assert_roles(actor, {"admin", "recruiter", "content_editor"})
        return {"items": self.repository.list_fit_assessments(actor.tenant_id)}

    def create_sales_summary_report(self, actor: UserContext, company_id: str, requirement_id: str, learner_id: str) -> dict:
        self._assert_roles(actor, {"admin", "recruiter"})
        requirements = self.repository.list_requirements(actor.tenant_id)
        learners = self.repository.list_learners(actor.tenant_id)
        requirement = next((item for item in requirements if item["id"] == requirement_id), None)
        learner = next((item for item in learners if item["id"] == learner_id), None)
        if requirement is None:
            raise ValueError("Requirement not found")
        if learner is None:
            raise ValueError("Learner not found")
        evidence = [e for e in self.repository.list_evidence(actor.tenant_id)
            if e["learnerId"] == learner_id and e["status"] == "passed" and e["reviewType"] == "mentor"]
        tags = {tag for e in evidence for tag in e["skillTags"]}
        matched = [s for s in requirement["requiredSkills"] if s in tags]
        gaps = [s for s in requirement["requiredSkills"] if s not in tags]
        result = {"id": f"report-{uuid4().hex}", "title": "AIプロジェクト提案書",
            "summary": f"業務課題: {requirement['title']}\n候補者: {learner['name']}\n第三者確認済み技能: {', '.join(matched) or 'なし'}\n未確認技能: {', '.join(gaps) or 'なし'}\nこれは技能タグの一致による参考情報です。案件適合性の最終判断は責任者が行ってください。",
            "requirementId": requirement_id, "learnerId": learner_id, "version": 1,
            "createdBy": actor.user_id, "generatedAt": datetime.now(timezone.utc).isoformat(),
            "sourceRequirement": requirement, "sourceEvidence": evidence}
        self.repository._db.add(ApplicationRecordModel(namespace="report:" + actor.tenant_id, id=result["id"], payload=result))
        self.repository._db.commit()
        return result

    def list_reports(self, actor):
        self._assert_roles(actor, {"admin", "recruiter", "content_editor"})
        return {"items": [r.payload for r in self.repository._db.scalars(select(ApplicationRecordModel).where(
            ApplicationRecordModel.namespace == "report:" + actor.tenant_id).order_by(ApplicationRecordModel.created_at.desc())).all()]}

    def get_report(self, actor: UserContext, company_id: str, report_id: str) -> dict:
        self._assert_roles(actor, {"admin", "recruiter", "content_editor"})
        record = self.repository._db.get(ApplicationRecordModel, ("report:" + actor.tenant_id, report_id))
        if record is None:
            raise ValueError("Report not found")
        return record.payload

    def create_report_export_job(self, actor: UserContext, report_id: str, report_format: str) -> dict:
        import base64
        from infrastructure.report_export import render_report
        report = self.get_report(actor, actor.tenant_id, report_id)
        content, media_type = render_report(report, report_format)
        job_id = "export-" + uuid4().hex
        result = {"jobId": job_id, "reportId": report_id, "status": "completed",
            "resultUrl": f"/api/v1/report-exports/{job_id}", "format": report_format,
            "mediaType": media_type, "content": base64.b64encode(content).decode("ascii")}
        self.repository._db.add(ApplicationRecordModel(namespace="export:" + actor.tenant_id, id=job_id, payload=result))
        self.repository._db.commit()
        return result

    def get_report_export(self, actor, job_id):
        self._assert_roles(actor, {"admin", "recruiter", "content_editor"})
        record = self.repository._db.get(ApplicationRecordModel, ("export:" + actor.tenant_id, job_id))
        if not record: raise ValueError("Export not found")
        return record.payload

    def list_curriculum_versions(self, actor: UserContext) -> list[dict]:
        self._assert_roles(actor, {"admin", "content_editor", "recruiter", "learner"})
        return self.repository.list_curriculum_versions(actor.tenant_id)

    def list_notifications(self, actor: UserContext, tab: str = "all", unread_only: bool = False) -> dict:
        self._assert_roles(actor, {"learner", "admin", "content_editor", "mentor", "recruiter"})
        return self.repository.list_notifications(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            tab=tab,
            unread_only=unread_only,
        )

    def mark_notification_read(self, actor: UserContext, notification_id: str) -> dict:
        self._assert_roles(actor, {"learner", "admin", "content_editor", "mentor", "recruiter"})
        updated = self.repository.mark_notification_read(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            notification_id=notification_id,
        )
        if updated is None:
            raise ValueError("Notification not found")
        return updated

    def mark_all_notifications_read(self, actor: UserContext) -> dict:
        self._assert_roles(actor, {"learner", "admin", "content_editor", "mentor", "recruiter"})
        updated = self.repository.mark_all_notifications_read(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
        )
        return {"updatedCount": updated}

    def list_notification_delivery_settings(self, actor: UserContext) -> dict:
        self._assert_roles(actor, {"learner", "admin", "content_editor", "mentor", "recruiter"})
        return self.repository.list_notification_delivery_settings(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
        )

    def update_notification_delivery_setting(
        self,
        actor: UserContext,
        *,
        category: str,
        email_enabled: bool,
        in_app_enabled: bool,
        push_enabled: bool,
    ) -> dict:
        self._assert_roles(actor, {"learner", "admin", "content_editor", "mentor", "recruiter"})
        if email_enabled or push_enabled:
            raise ValueError("メール・push配信は未提供です。アプリ内通知を利用してください")
        if category not in {"learning", "career", "dm", "admin"}:
            raise ValueError("Unsupported notification category")
        return self.repository.upsert_notification_delivery_setting(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            category=category,
            email_enabled=email_enabled,
            in_app_enabled=in_app_enabled,
            push_enabled=push_enabled,
        )

    def list_admin_audit_logs(
        self,
        actor: UserContext,
        *,
        limit: int = 100,
        event_type: str | None = None,
        actor_user_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        occurred_from: str | None = None,
        occurred_to: str | None = None,
    ) -> dict:
        self._assert_roles(actor, {"admin"})
        return {
            "items": self.repository.list_audit_logs(
                tenant_id=actor.tenant_id,
                limit=limit,
                event_type=event_type,
                actor_user_id=actor_user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                occurred_from=occurred_from,
                occurred_to=occurred_to,
            )
        }
