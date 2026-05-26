from __future__ import annotations

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from infrastructure.db import Base


class UserModel(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(32), index=True)
    state: Mapped[str] = mapped_column(String(32), default="active")
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class TeamModel(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TeamMemberModel(Base):
    __tablename__ = "team_members"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True)
    joined_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InviteModel(Base):
    __tablename__ = "invites"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    role: Mapped[str] = mapped_column(String(32))
    team_id: Mapped[str | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="invited")
    invited_by: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RequirementModel(Base):
    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text())
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FitAssessmentModel(Base):
    __tablename__ = "fit_assessments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    requirement_id: Mapped[str] = mapped_column(ForeignKey("requirements.id"), index=True)
    recommended_learner_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    fit_score: Mapped[int] = mapped_column(Integer)
    matched_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    gap_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RoleTemplateModel(Base):
    __tablename__ = "role_templates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    code: Mapped[str] = mapped_column(String(80), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text())
    target_skills: Mapped[list[str]] = mapped_column(JSON, default=list)


class LearnerProfileModel(Base):
    __tablename__ = "learner_profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    team_name: Mapped[str] = mapped_column(String(120))
    target_role: Mapped[str] = mapped_column(String(120))
    roadmap_completion_rate: Mapped[int] = mapped_column(Integer, default=0)
    readiness: Mapped[str] = mapped_column(String(32), default="Not Started")
    pending_submission_count: Mapped[int] = mapped_column(Integer, default=0)
    strong_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    gap_skills: Mapped[list[str]] = mapped_column(JSON, default=list)


class RoadmapAssignmentModel(Base):
    __tablename__ = "roadmap_assignments"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True)
    role_template_id: Mapped[str] = mapped_column(ForeignKey("role_templates.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="assigned")
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExerciseModel(Base):
    __tablename__ = "exercises"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(32), default="notebook")
    title: Mapped[str] = mapped_column(String(255))
    prompt: Mapped[str] = mapped_column(Text())
    starter_code: Mapped[str] = mapped_column(Text())
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class SubmissionModel(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    exercise_id: Mapped[str] = mapped_column(ForeignKey("exercises.id"), index=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="submitted")
    code: Mapped[str] = mapped_column(Text())
    execution_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    execution_stdout: Mapped[str | None] = mapped_column(Text(), nullable=True)
    execution_stderr: Mapped[str | None] = mapped_column(Text(), nullable=True)
    execution_engine: Mapped[str | None] = mapped_column(String(64), nullable=True)
    execution_pipeline: Mapped[str | None] = mapped_column(String(64), nullable=True)
    execution_details_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReviewModel(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), index=True)
    reviewer_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    score: Mapped[int] = mapped_column(Integer)
    comments: Mapped[str] = mapped_column(Text())
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvidenceModel(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text())
    skill_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    strength: Mapped[str | None] = mapped_column(String(32), nullable=True)
    review_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    use_case: Mapped[str | None] = mapped_column(Text(), nullable=True)
    rubric_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    exercise_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    submission_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    submitted_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    related_requirement_ids: Mapped[list[str]] = mapped_column(JSON, default=list)


class ReportJobModel(Base):
    __tablename__ = "report_jobs"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    report_id: Mapped[str] = mapped_column(String(80), index=True)
    report_format: Mapped[str] = mapped_column(String(16), default="csv")
    status: Mapped[str] = mapped_column(String(32), default="queued")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    result_url: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CurriculumVersionModel(Base):
    __tablename__ = "curriculum_versions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    curriculum_slug: Mapped[str] = mapped_column(String(120), index=True)
    version: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    mdx_path: Mapped[str] = mapped_column(String(255))
    skill_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    difficulty: Mapped[int] = mapped_column(Integer)
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    resource_type: Mapped[str] = mapped_column(String(120), index=True)
    resource_id: Mapped[str] = mapped_column(String(120), index=True)
    action: Mapped[str] = mapped_column(String(80))
    actor_user_id: Mapped[str] = mapped_column(String(64), index=True)
    actor_role: Mapped[str] = mapped_column(String(32))
    summary: Mapped[str] = mapped_column(Text())
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_audit_logs_tenant_occurred_at", "tenant_id", "occurred_at"),
        Index("ix_audit_logs_tenant_event_type_occurred_at", "tenant_id", "event_type", "occurred_at"),
        Index("ix_audit_logs_tenant_actor_occurred_at", "tenant_id", "actor_user_id", "occurred_at"),
        Index("ix_audit_logs_tenant_resource_occurred_at", "tenant_id", "resource_type", "resource_id", "occurred_at"),
    )


class NotificationInboxModel(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text())
    target_url: Mapped[str] = mapped_column(String(255))
    is_important: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_notifications_user_read_created", "user_id", "read_at", "created_at"),
        Index("ix_notifications_user_category_created", "user_id", "category", "created_at"),
    )


class NotificationDeliverySettingModel(Base):
    __tablename__ = "notification_delivery_settings"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ux_notification_delivery_user_category", "user_id", "category", unique=True),
    )


class NotificationDeliveryJobModel(Base):
    __tablename__ = "notification_delivery_jobs"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text())
    target_url: Mapped[str] = mapped_column(String(255))
    channels: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_important: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text(), nullable=True)
    available_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_notification_delivery_jobs_status_available", "status", "available_at"),
    )
